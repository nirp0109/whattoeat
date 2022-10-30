import base64
import argparse
import requests
import json
import re
import csv
import pandas as pd
import copy as clone
import send_mail
import string
from dotenv import dotenv_values
from itertools import combinations
import mysql.connector
import os
import sys

auth = ()

PRODUCT_ID_INDEX = 'GTIN'
COMPANY_ID_INDEX = 'GLN'
PRODUCT_NAME_INDEX = 'Sub_Brand_Name'
EXCEPTION_INDEX = 'exception'

NO_MILK = 5523
NO_GLUTEN = 5538
WITHOUT_GLUTEN = 5502
VEGAN_FRIENDLY = 5573
VEGAN = 5521

# Product_Shelf_Life - product life span
# Product_Status - product status (status in hebrew as json)


def find_key(somejson, key):
    """
    find key in json and return array of values. use when the value of a key is simple string or number
    :param somejson: string json
    :param key: string  key to find
    :return: list of values founded
    """
    pattern_str = "(?<=\"{}\":\").+?(?=\")".format(key)
    compile_pattern = re.compile(pattern_str)
    data= compile_pattern.findall(somejson)
    return data


def find_array(somejson, key):
    """
    find key in json and return value. use when the value of a key  is array of strings or numbers
    :param somejson: string json
    :param key: string key to find
    :return: list of values founded (json array)
    """
    pattern_str = "(?<=\"{}\":\[).+?(?=\])".format(key)
    compile_pattern = re.compile(pattern_str)
    data= compile_pattern.findall(somejson)
    return data[0]


def pretty_json(txt):
    """
    pretty print json
    :param txt:
    :return:
    """
    parsed = json.loads(txt)
    print(json.dumps(parsed, indent=4, sort_keys=True))


def test_api(name):
    paramters = {"field":"Rabbinate", "hq":"1"}
    # get all products modification in last 120 days
    url = 'https://fe.gs1-hq.mk101.signature-it.com/external/app_query/select_query.json'
    body = {"query": "modification_timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY)","get_chunks":{ "start": 0, "rows": 600 }}
    # body = {"query": "modification_timestamp > DATE_SUB(NOW(), INTERVAL 360 DAY)"}
    res = requests.request(method="post", url=url, auth=auth, json=body)
    print(res.status_code)
    print(res.headers)
    print(res.text)
    arr = find_key(res.text, 'product_code')
    print(len(arr))
    print('-----------------------------------------')

    # 7290002700005 עלית/שטראוס get manufactor product
    # body = {"query": "GLN = '7290002700005'","get_chunks": { "start": 0, "rows": 50 }}
    # אוסם
    body = {"query": "GLN = '7290009800005'", "get_chunks": {"start": 0, "rows": 50}}
    res = requests.request(method="post", url=url, auth=auth, json=body)
    print(res.status_code)
    print(res.text)
    products = find_key(res.text, 'product_code')
    print('=========================================================')

    # get specfic  products
    # חויף שיבולת שועל עם בוטנים
    # body = {"query": "GTIN = '7290115675603'","get_chunks": { "start": 0, "rows": 50 }}
    body = {"query": "GTIN = '7290115675603'", "get_chunks": {"start": 0, "rows": 600}}
    res = requests.request(method="post", url=url, auth=auth, json=body)
    print(res.status_code)
    pretty_json(res.text)
    products = find_key(res.text, 'product_code')

    # get product details
    print('-----------------------------------------')

    url = "https://fe.gs1-retailer.mk101.signature-it.com/external/product/{}.json?hq=1".format(products[0])
    print(url)
    res = requests.request(method="get", url=url, auth=auth)
    print(res.status_code)
    print(res.text)

    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    # all fields
    # url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=All&hq=1'
    # may contain allergen
    # url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=Allergen_Type_Code_and_Containment_May_Contain&hq=1'
    # contain allergen
    url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=Allergen_Type_Code_and_Containment&hq=1'

    # url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=Ingredient_Sequence_and_Name&hq=1'
    res = requests.request(method="get", url=url, auth=auth)
    print(res.text)

    # download first product from array of product a zip of his media files
    print('-----------------------------------------')
    url="https://fe.gs1-retailer.mk101.signature-it.com//external/product/{}/files?media=all&hq=1".format(products[0])
    print(url)
    res = requests.request(method="get", url=url, auth=auth)
    if res.status_code == 200:
        with open('media.zip','wb') as fd:
            fd.write(base64.decodebytes(res.text.encode('utf-8')))


def download_media_product(product_code:str, id:str="all"):
    """
    use GS1 api to download media files of a product. save as zip file or media file with prefix of product code
    :param product_code: string product code
    :param id: string media id or "all" for all media files
    """
    url="https://fe.gs1-retailer.mk101.signature-it.com//external/product/{}/files?media={}&hq=1".format(product_code, id)
    print(url)
    res = requests.request(method="get", url=url, auth=auth)
    if res.status_code == 200:
        json_data = json.loads(res.text)
        print(json_data.keys())
        data = json_data['file']
        format_type = json_data['format']
        with open('{}.{}'.format('{}_{}'.format(product_code, id), format_type),'wb') as fd:
            fd.write(base64.decodebytes(data.encode('ascii')))



def create_allergen_csv():
    """
    Create allergen list from api using data from field. also store in cvs as output.cvs
    :return: allergen list<str>
    """
    allergen_list = []
    # add may contain
    url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=Allergen_Type_Code_and_Containment_May_Contain&hq=1'
    res = requests.request(method="get", url=url, auth=auth)
    items = find_array(res.text, 'select_options')
    items = re.findall("\"name\":\"(.*?)\"", items)
    for item in items:
        allergen_list.append(item)
    # add contain
    url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=Allergen_Type_Code_and_Containment&hq=1'
    res = requests.request(method="get", url=url, auth=auth)
    items = find_array(res.text, 'select_options')
    items = re.findall("\"name\":\"(.*?)\"", items)
    for item in items:
        allergen_list.append(item)

    my_set = set(allergen_list)
    allergen_list = list(my_set)
    allergen_list = sorted(allergen_list, reverse=True)
    print(len(allergen_list))

    with open('output.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['allergen'])
        w.writeheader()
        my_repo_request = []
        for row in allergen_list:  # skip header row
            my_repo_request.append({'allergen':row})
        w.writerows(my_repo_request)
    return  allergen_list


def load_allergens_from_cvs():
    """
    load allergens from CVSs Elad created and return different data structures
    :return: allegens as list of Strings and allergen dict
    """
    table = pd.read_csv('allergens.csv')
    allergens = []
    allergens_dict = {}
    allergens_family_dict = {}
    allergen_group = {}
    # iterate over all rows of table
    for row in table.iterrows():
        vec = row[1]
        alleregen_dict = vec.to_dict()
        # first column is allergen the other in the rows it is in the same family
        key = alleregen_dict['allergen']
        # prepare to get the rest of the row without the first one as list
        del alleregen_dict['allergen']
        values = list(alleregen_dict.values())
        values = list(filter(lambda x:not "nan".__eq__(x), map(lambda x: str(x), values)))
        # put allergen main as key and the other in the row as list
        allergens_dict[key] = list(values)
        for item in allergens_dict[key]:
            allergen_group[item] = key
        # get all cells of table (without header)
        for elem in vec: # vec[1:]
            if type(elem)==str:
                allergens.append(elem.strip())

    table = pd.read_csv('GlutenNuts.csv')
    for row in table.iterrows():
        vec = row[1]
        data = vec.to_list()
        result_list =list(filter(lambda x:not "nan".__eq__(x), map(lambda x: str(x), data[1:])))
        allergens_family_dict[data[0]] = result_list
        for item in result_list:
            allergen_group[item] = item
            allergens.append(item)

    table = pd.read_csv('Alias.csv')
    alias = {}
    # iterate over all rows of table
    # for each row create mapping in alias dict that every element in the row is the key and the value is the first element in the row.
    for row in table.iterrows():
        vec = row[1]
        data = vec.to_list()
        # get list elements of data without NaN or empty strings
        result_list =list(filter(lambda x:not "nan".__eq__(x), map(lambda x: str(x), data[1:])))
        [alias.update({x:data[0]}) for x in result_list]
        [allergens.append(x) for x in result_list]

    allergens = sorted(set(allergens), reverse=True)
    return allergens, allergens_dict, allergens_family_dict, allergen_group, alias


def transfrom_allergen_set_to_alis_set(allergens_set:set, alias:dict):
    """
    transform allergen set to alias set
    :param allergens_set: set of allergen
    :param alias: dict of alias
    :return: set of alias
    """
    result = set()
    for item in allergens_set:
        if item in alias:
            result.add(alias[item])
        else:
            result.add(item)
    return result


def get_product_info(product_code:str):
    """
    Use the API to get product info using product_code
    :param product_code: str
    :return: str JSON of product details (with no media)
    """
    url = "https://fe.gs1-retailer.mk101.signature-it.com/external/product/{}.json?hq=1".format(product_code)
    print(url)
    res = requests.request(method="get", url=url, auth=auth)
    if res.status_code == 200:
        return res.text
    else:
        print(res.status_code, res.text)
        if res.text and '[' in res.text and ']' in res.text:
        # print the hebrew of res.text
            print(res.text[1:-1].encode('utf-8').decode('unicode_escape'))


def get_product_ingrident(product_details:str):
    """
    Get product ingedients as list of str from product details (from API)
    :param product_details: str JSon result from API
    :return: list<str> list of ingredints
    """
    ingrdients = find_key(product_details, 'Ingredient_Sequence_and_Name')
    # split by comma that is no inside parenthesis
    ingrdients_list = re.split(',(?=(?:[^"]*"[^"]*")*[^"]*$)', ingrdients[0])
    print(ingrdients_list)
    for item in ingrdients_list:
        print(item)
    return  ingrdients_list

def get_normalize_allergens_dict(file_name:str):
    """
    get normalize allergen dict from csv file.
    Each line in the csv file is a list of the same allergen.
    :param file_name:
    :return: dict<str, str> allergen dict where all alleregens from the same line are mapped to the first allergen in the line
    """
    #read csv file
    with open(file_name, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
#     for each row,except the first one in data make a dict with key a value from all columns to first column value
    allergens_dict = {}
    count = 0
    for row in data:
        count += 1
        if count == 1:
            continue
        for item in row[1:]:
            allergens_dict[item] = row[0]
    return allergens_dict


def extract_allergens_from_ingredients(ingredients:list, allergens:list):
    """
    Extract allergens from ingredients
    :param ingredients: list of string of ingredients. Got using api
    :param allergens: list of string of allergens
    :return: set of string of allergens found in ingredients
    """
    allergen_in_ingredients = []
    allerenes_set = set(allergens)
    for ingredient in ingredients:
        #get tokens of only hebrew chars squences hopefully of word(more than one word more than one sequence)
        ingredient_tokens = re.findall(r'[\u0590-\u05fe]+', ingredient)
        #remove all empty tokens created by no hebrew chars like digits, parentsis, dot and more
        ingredient_tokens = list(filter(None, ingredient_tokens))
        #create set with one elments or more of one word
        ingredient_tokens_set = set(ingredient_tokens)
        #get tokens of two words and clean empty tokens and make set
        two_word_phases = list(map(lambda x: x[0] + ' ' + x[1], combinations(ingredient_tokens, 2)))
        # ingredient_tokens_pharse = re.findall('|'.join(two_word_phases), ingredient)
        ingrident_tokens_pharse_set = set(list(filter(None, two_word_phases)))
        #intersect words found with allergens set to find allergens in ingredient
        intersect = ingredient_tokens_set.intersection(allerenes_set)
        intersect2 = ingrident_tokens_pharse_set.intersection(allerenes_set)
        # add all allergens found in list
        if intersect:
            for i in intersect:
                allergen_in_ingredients.append(i)
        if intersect2:
            for i in intersect2:
                allergen_in_ingredients.append(i)
    allergen_in_ingredients_set = set(allergen_in_ingredients)
    return  allergen_in_ingredients_set


def product_test(product_code:str):
    """
    create serval tests on specfic product
    :param product_code: str the product_code
    :return: list of json - each line a different exception
    """
    record = {}
    results = []
    exception = None
    # load product info
    product_info = get_product_info(product_code)
    if not product_info:
        print("failed to get product info for {}".format(product_code))
        return

    report_fields = [COMPANY_ID_INDEX, 'Manufacturer_Name',PRODUCT_ID_INDEX, 'BrandName', PRODUCT_NAME_INDEX, 'Trade_Item_Description', 'Short_Description',
                      'Ingredient_Sequence_and_Name', 'Product_Categories_Classification']
    for key in report_fields:
        try:
            val = find_key(product_info, key)
            if type(val) == list:
                if len(val) == 0:
                    record[key] = ""
                else:
                    record[key] = val[0]
            else:
                record[key] = val
        except:
            val = find_array(product_info, key)[0]
            if type(val) == list:
                if len(val) == 0:
                    record[key] = ""
                else:
                    record[key] = val[0]
            else:
                record[key] = val

    print(product_info)
    data = get_product_ingrident(product_info)
    # load allergens from csv
    allergens, allergens_dict, allergens_family_dict, allergens_group, alias = load_allergens_from_cvs()
    # find allergen in ingredients in united name using alias
    allergen_in_ingredients_set = transfrom_allergen_set_to_alis_set(extract_allergens_from_ingredients(data, allergens), alias)
    # remove גלוטן from allergens_in_ingredients
    allergen_in_ingredients_set.discard('גלוטן')
    print(">>>>", allergen_in_ingredients_set)
    # get alleregen contain and may contain from product info(labels)
    pattern_str = "(?<=\"{}\":\[).+?(?=\])".format('Allergen_Type_Code_and_Containment')
    compile_pattern = re.compile(pattern_str)
    allergen_contain= compile_pattern.findall(product_info)
    pattern_str = "(?<=\"{}\":\[).+?(?=\])".format('Allergen_Type_Code_and_Containment_May_Contain')
    compile_pattern = re.compile(pattern_str)
    allergen_may_contain= compile_pattern.findall(product_info)
    print(allergen_contain)
    try:
        allergen_contain_set = set(map(lambda item : json.loads(item)['value'], allergen_contain))
    except:
        allergen_contain_set = set(map(lambda item : json.loads(item)['value'], re.findall(r"\{.*?\}",allergen_contain[0])))
    try:
        allergen_may_contain_set = set(map(lambda item :  json.loads(item)['value'], allergen_may_contain))
    except:
        allergen_may_contain_set = set(
            map(lambda item: json.loads(item)['value'], re.findall(r"\{.*?\}", allergen_may_contain[0])))

    # get allergen contain and may contain from product info(labels)
    pretty_alleregen_contain = list(allergen_contain_set)
    pretty_alleregen_contain = sorted(pretty_alleregen_contain)
    record["Allergens_Contain"] = ','.join(pretty_alleregen_contain)
    pretty_alleregen_may_contain = list(allergen_may_contain_set)
    pretty_alleregen_may_contain = sorted(pretty_alleregen_may_contain)
    record["Allergens_May_Contain"] = ','.join(pretty_alleregen_may_contain)
    record["Diet_Information"] = find_array(product_info, "Diet_Information")
    print("allergen_contain label: ", allergen_contain_set)
    print("allergen_may_contain_set label: ", allergen_may_contain_set)
    # transform allergen contain and may contain to allergen set that are name unifrom using alias
    allergen_contain_set = transfrom_allergen_set_to_alis_set(allergen_contain_set, alias)
    allergen_may_contain_set = transfrom_allergen_set_to_alis_set(allergen_may_contain_set, alias)

    # have allergens that are not allergen label
    if len(allergen_in_ingredients_set - allergen_contain_set) > 0:
        missing_contains_allergens = allergen_in_ingredients_set - allergen_contain_set
        missing_contains_allergens_set = set([allergens_group[item] if item in allergens_group else item for item in missing_contains_allergens ])
        delta = missing_contains_allergens_set - allergen_contain_set
        if delta:
            delta_list = sorted(list(delta))
            print("in allergens there is missing:",delta_list)
            exception = "in allergens there is missing:" + ','.join(delta_list)
            record[EXCEPTION_INDEX] = exception
            results.append(record)
            record = clone.deepcopy(record)


    # have allergens that are not in ingredients
    if len(allergen_contain_set) > 0 and len(allergen_in_ingredients_set) == 0:
        pass

    # missing allergen label
    if len(allergen_in_ingredients_set) > 0 and len(allergen_contain_set) == 0:
        pass
    # get product diet labels like No_GLUTEN, NO_MILK and etc
    diet_information_list =re.findall(r"\{.*?\}",find_array(product_info, 'Diet_Information'))
    print("diet_information_list>>>",diet_information_list)
    diet_information_codes =  list(map(lambda item : int_code_value_from_json(item), diet_information_list))

    #test there is no contradiction between allergens and ingredients and the diet information labels
    # test that if have no milk label than there is not milk and his components in ingrideints and allergens
    if NO_MILK in diet_information_codes:
        milk_allergens_list = allergens_dict['חלב']
        milk_found_ingredients = extract_allergens_from_ingredients(data, milk_allergens_list)
        milk_found_allergens_contain = extract_allergens_from_ingredients(list(allergen_contain_set), milk_allergens_list)
        milk_found_allergens_may_contain = extract_allergens_from_ingredients(list(allergen_may_contain_set), milk_allergens_list)
        if len(milk_found_ingredients) > 0 or len(milk_found_allergens_contain) > 0 or len(milk_found_allergens_may_contain) > 0:
            print("milk is found either in ingridents or allergens labels")
            exception = "milk is found either in ingridents or allergens labels"
            record[EXCEPTION_INDEX] = exception
            results.append(record)
            record = clone.deepcopy(record)

    if NO_GLUTEN in diet_information_codes or WITHOUT_GLUTEN in diet_information_codes:
        gluten_allergens_list = allergens_dict['גלוטן']
        gluten_found_ingredients = extract_allergens_from_ingredients(data, gluten_allergens_list)
        gluten_found_allergens_contain = extract_allergens_from_ingredients(list(allergen_contain_set), gluten_allergens_list)
        gluten_found_allergens_may_contain = extract_allergens_from_ingredients(list(allergen_may_contain_set), gluten_allergens_list)
        if len(gluten_found_ingredients) > 0 or len(gluten_found_allergens_contain) > 0 or len(gluten_found_allergens_may_contain) > 0:
            print("gluten is found either in ingridents or allergens labels")
            exception = "gluten is found either in ingridents or allergens labels"
            record[EXCEPTION_INDEX] = exception
            results.append(record)
            record = clone.deepcopy(record)

    if VEGAN_FRIENDLY in diet_information_codes or VEGAN in diet_information_codes:
        vegan_list = ['חלב', 'גבינה', 'בשר', 'עוף', 'דבש', 'יוגורט', 'ביצה', 'ביצים', 'בקר']
        vegan_list.extend(allergens_dict['דגים'])
        none_vegan_found_ingredients = extract_allergens_from_ingredients(data, vegan_list)
        if len(none_vegan_found_ingredients) > 0:
            print('contain none vegan products:', none_vegan_found_ingredients)
            exception = 'contain none vegan products:' + ','.join(none_vegan_found_ingredients)
            record[EXCEPTION_INDEX] = exception
            results.append(record)
            record = clone.deepcopy(record)

    en_heb_dict = {'אגוזים':'nuts', 'גלוטן':'gluten'}

    # test that there is details of allergens in allergens labels
    for key in allergens_family_dict.keys():
        if key in allergen_contain_set or key in allergen_may_contain_set:
            exception = 'there is not details of {} contain'.format(en_heb_dict[key])
            print(exception)
            record[EXCEPTION_INDEX] = exception
            results.append(record)
            record = clone.deepcopy(record)


    return results


def int_code_value_from_json(item):
    try:
        return int(json.loads(item)['code'])
    except:
        return -1


def find_product_code_by_gtin(gtin:str):
    """
    find product code by gtin using the GS1 api.
    :param gtin:
    :return:
    """
    url = 'https://fe.gs1-hq.mk101.signature-it.com/external/app_query/select_query.json'
    body = {"query": "GTIN = '{}'".format(gtin), "get_chunks": {"start": 0, "rows": 5}}
    res = requests.request(method="post", url=url, auth=auth, json=body)
    print(res.status_code, res.text)
    product = find_key(res.text, 'product_code')
    return  product


def get_company_products(gln:str):
    """
    get products codes of a company or manufactur using the GS1 api.
    :param gln: str gln of a company or manufactur
    :return: list<str>  product codes list
    """
    products = []
    # get all products modification in last 120 days
    url = 'https://fe.gs1-hq.mk101.signature-it.com/external/app_query/select_query.json'
    body = {"query": "GLN = '{}'".format(gln), "get_chunks": {"start": 0, "rows": 600}}
    res = requests.request(method="post", url=url, auth=auth, json=body)
    print(res.status_code)
    products_temp = find_key(res.text, 'product_code')
    products.extend(products_temp)
    print(len(products))
    while len(products_temp) == 600:
        body = {"query": "GLN = '{}'".format(gln), "get_chunks": {"start": len(products), "rows": 600}}
        res = requests.request(method="post", url=url, auth=auth, json=body)
        products_temp = find_key(res.text, 'product_code')
        if len(products_temp) > 0:
            products.extend(products_temp)
            print(len(products))
    return products


def read_csv(file_name):
    """
    read csv file and return a list of lists
    :param file_name: str name of the file
    :return: list of lists
    """
    with open(file_name, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        data = list(reader)
    return data

def test_and_add_exception_to_report(product_code:str, writer:csv.DictWriter):
    results = product_test(product_code)
    if len(results) > 0:
        writer.writerows(results)

    return product_code
def create_report(gln:str = '7290009800005', name=None):
    """
    create a report of all products of a company or manufactur
    :param gln: str the company or manufactur gln
    :return: None
    """
    field_names = [COMPANY_ID_INDEX, 'Manufacturer_Name',PRODUCT_ID_INDEX, PRODUCT_NAME_INDEX, "Allergens_Contain", "Allergens_May_Contain", 'Ingredient_Sequence_and_Name', 'Diet_Information', 'BrandName', 'Trade_Item_Description', 'Short_Description', EXCEPTION_INDEX, 'Product_Categories_Classification']
    if name is None:
        report_file_name = 'report_{}.csv'.format(gln)
    else:
        report_file_name = format_filename('report_{}.csv'.format(name))
    with open(report_file_name,'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        product_codes = get_company_products(gln)
        # map(lambda x: test_and_add_exception_to_report(x, writer), product_codes)
        for product_code in product_codes:
            results = product_test(product_code)
            if results and len(results) > 0:
                writer.writerows(results)

def get_updated_products():
    """
    get a list of products udpated for the last day from now using GS1 API
    :return: list<str> products codes
    """
    url = 'https://fe.gs1-hq.mk101.signature-it.com/external/app_query/select_query.json'
    body = {"query": "modification_timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY)","get_chunks":{ "start": 0, "rows": 600 }}
    res = requests.request(method="post", url=url, auth=auth, json=body)
    print(res.text)
    print(res.status_code)
    products_temp = find_key(res.text, 'product_code')
    products = []
    products.extend(products_temp)
    print(len(products))
    while len(products_temp) == 600:
        body = {"query": "modification_timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY)",
                "get_chunks": {"start": len(products), "rows": 600}}
        res = requests.request(method="post", url=url, auth=auth, json=body)
        products_temp = find_key(res.text, 'product_code')
        if len(products_temp) > 0:
            products.extend(products_temp)
            print(len(products))
    return products


def get_companies():
    """
    get all companies from GLN.csv file by collecting from the second row to the end
    :return: list<list> companies list each element is GLN and his name
    """
    companies = []
    with open('GLN.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        data = list(reader)
        for row in data[1:]:
            companies.append([row[0], row[1]])
    return companies


def format_filename(filename):
    """
    remove invalid chars from filename
    :param filename:
    :return: filename without invalid chars
    """
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename


def inquire_GS1_fields():
    # all fields
    url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=All&hq=1'
    # may contain allergen
    # url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=Allergen_Type_Code_and_Containment_May_Contain&hq=1'
    # contain allergen
    # url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=Allergen_Type_Code_and_Containment&hq=1'

    # url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=Ingredient_Sequence_and_Name&hq=1'

    url = 'https://fe.gs1-retailer.mk101.signature-it.com/external/product/fieldInfo.json?field=Brand_Name&hq=1'
    res = requests.request(method="get", url=url, auth=auth)
    print(res.text.encode('utf8'))
    pretty_json(res.text)


def store_product_info(product_info, gln, db_user, db_password, db_name, db_host):
    """
    create table of products info if table is not exist and store the product info in it
    :param product_info: product info as json
    :param gln: str the company gln
    :param db_user: str the db user
    :param db_password: str the db password
    :param db_name: str the db name
    :param db_host: str the db host
    :return: None
    """
    mydb = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )

    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE  IF NOT EXISTS PRODUCTS(id int NOT NULL AUTO_INCREMENT, product_code VARCHAR(255), gln VARCHAR(255), gtin VARCHAR(255), product_info MEDIUMTEXT, Short_Description varchar(255), Brand_Name varchar(255), Sub_Brand_Name varchar(255), Ingredients varchar(255), Allergens_Contain varchar(255), Allergens_May_Contain varchar(255), Active tinyint(1),Product_Status int(4), PRIMARY KEY (id))")
    sql = "INSERT INTO PRODUCTS (product_code, gln, gtin, product_info, Short_Description, Brand_Name, Sub_Brand_Name, Ingredients, Allergens_Contain, Allergens_May_Contain, Product_Status, Active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    fields = ['Short_Description', 'BrandName', 'Sub_Brand_Name', 'Ingredients']
    field_values = []
    for field in fields:
        try:
            val = find_key(product_info, field)
            if type(val) == list:
                if len(val) == 0:
                    field_values.append('')
                else:
                    field_values.append(val[0])
            else:
                field_values.append(val)
        except:
            val = find_array(product_info, field)[0]
            if type(val) == list:
                if len(val) == 0:
                    field_values.append('')
                else:
                    field_values.append(val[0])
            else:
                field_values.append(val)

    pattern_str = "(?<=\"{}\":\[).+?(?=\])".format('Allergen_Type_Code_and_Containment')
    compile_pattern = re.compile(pattern_str)
    allergen_contain = compile_pattern.findall(product_info)
    pattern_str = "(?<=\"{}\":\[).+?(?=\])".format('Allergen_Type_Code_and_Containment_May_Contain')
    compile_pattern = re.compile(pattern_str)
    allergen_may_contain = compile_pattern.findall(product_info)

    try:
        allergen_contain_set = set(map(lambda item: json.loads(item)['value'], allergen_contain))
    except:
        allergen_contain_set = set(
            map(lambda item: json.loads(item)['value'], re.findall(r"\{.*?\}", allergen_contain[0])))
    try:
        allergen_may_contain_set = set(map(lambda item: json.loads(item)['value'], allergen_may_contain))
    except:
        allergen_may_contain_set = set(
            map(lambda item: json.loads(item)['value'], re.findall(r"\{.*?\}", allergen_may_contain[0])))

    # get allergen contain and may contain from product info(labels)
    pretty_alleregen_contain = list(allergen_contain_set)
    pretty_alleregen_contain = sorted(pretty_alleregen_contain)
    field_values.append(','.join(pretty_alleregen_contain))
    pretty_alleregen_may_contain = list(allergen_may_contain_set)
    pretty_alleregen_may_contain = sorted(pretty_alleregen_may_contain)
    field_values.append(','.join(pretty_alleregen_may_contain))
    status = find_array(product_info, 'Product_Status')
    try:
        status_json = json.loads(status)
        status_int = int(status_json['code'])
    except:
        status_int = 0
    field_values.append(status_int)
    # active is 1 if status is 6303
    if status_int == 6303:
        field_values.append(1)
    else:
        field_values.append(0)

    product_code = find_key(product_info, 'product_code')[0]
    gtin = find_key(product_info, PRODUCT_ID_INDEX)[0]
    val = (product_code, gln, gtin, json.dumps(product_info), *field_values)
    mycursor.execute(sql, val)
    mydb.commit()
    print(mycursor.rowcount, "record inserted.")

    #insert diet information into PRODUCT_DIETS table where product_id is the id of the product in PRODUCTS table and diet_id is array is extract from product_info Diet_Information array
    product_id = mycursor.lastrowid
    diet_information_list =re.findall(r"\{.*?\}",find_array(product_info, 'Diet_Information'))
    print("diet_information_list>>>",diet_information_list)
    diet_information_codes =  list(map(lambda item : int_code_value_from_json(item), diet_information_list))
    sql = "INSERT INTO PRODUCT_DIETS (product_id, diet_id) VALUES (%s, %s)"
    # if diet_information_codes is not empty insert diet information into PRODUCT_DIETS table
    if len(diet_information_codes) > 0:
        for diet_id in diet_information_codes:
            val = (product_id, diet_id)
            mycursor.execute(sql, val)
            mydb.commit()
            print(mycursor.rowcount, "record inserted.")



def get_products_exist_in_db(gln, db_user, db_password, db_name, db_host):
    """
    get a list of products that exist in the db for the given gln
    :param gln: str the company gln
    :param db_user: str the db user
    :param db_password: str the db password
    :param db_name: str the db name
    :param db_host: str the db host
    :return: list<str> products codes
    """
    mydb = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )

    mycursor = mydb.cursor()
    mycursor.execute("SELECT product_code FROM PRODUCTS WHERE gln = '{}'".format(gln))
    myresult = mycursor.fetchall()
    products = []
    for x in myresult:
        products.append(x[0])
    return products


if __name__ == '__main__':
    """
    main entry point
    can execute the script with a product code or a company gln
    for example:
    1. create a report of all products of a company or manufactur using the GS1 api, execute the script with the gln of the company or manufactur like this:
    python3 main.py -c 7290009800005
    2. create a test for a product using the GS1 api, execute the script with the product code like this:
    python3 main.py -p    7290112341723
    python3 main.py -p    7290018724699 
    3. get the updated products list of companies or manufacturs using the GS1 api for the last day. execute the script like this:
    python3 main.py -u  
    4. create report for the updated products list of companies or manufacturs using the GS1 api for the last day. execute the script like this:
    python3 main.py -s
    5.upload all companies products to the database
    python3 main.py -d
    """
    (user, password, user_d, pass_d, hostname, database) = dotenv_values('.env').values()
    auth = (user, password)
    my_parser = argparse.ArgumentParser(description="for test a given product(-p) or a company(-c) or get updated products list(-u) or create report foe updated products list(-s)")
    my_group = my_parser.add_mutually_exclusive_group(required=True)

    my_group.add_argument('-p', action='store', help='test a given product given')
    my_group.add_argument('-c', action='store', help="test all product of given company")
    my_group.add_argument('-u', action='store_true', help="get updated products list")
    my_group.add_argument('-s', action='store_true', help="create report for the updated products list")
    my_group.add_argument('-a', action='store_true', help="create reports for all companies")
    my_group.add_argument('-d', action='store_true', help="upload all companies products to database")

    args = my_parser.parse_args()
    actions = vars(args)

    if 'p' in actions and actions['p']:
        product_code = find_product_code_by_gtin(actions['p'])
        print(product_code)
        res = product_test(product_code[0])
        print(res)
        download_media_product(product_code[0])

    if 'c' in actions and actions['c']:
        create_report(actions['c'])

    if 'u' in actions and actions['u']:
        # get updated products list
        products = get_updated_products()
        for product in products:
            # get product info
            product_info = get_product_info(product)
            # if product exist get it data
            if product_info:
                # get it main media
                medias = find_array(product_info, 'media_assets')
                if medias:
                    # create array from the json string of the media that come without the square brackets
                    arr = json.loads('['+medias+']')
                    # iterate over the array and get all medias
                    for media in arr:
                        download_media_product(product, media['id'])




    if 's' in actions and actions['s']:
        products = get_updated_products()
        field_names = [COMPANY_ID_INDEX,'Manufacturer_Name', PRODUCT_ID_INDEX, PRODUCT_NAME_INDEX, "Allergens_Contain", "Allergens_May_Contain", 'Ingredient_Sequence_and_Name', 'Diet_Information', 'BrandName', 'Trade_Item_Description', 'Short_Description', EXCEPTION_INDEX, 'Product_Categories_Classification']
        with open('updated_products_report.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()
            for product_code in products:
                results = product_test(product_code)
                if results and len(results) > 0:
                    writer.writerows(results)
        send_mail.send_email_using_smtp(recipients=['nirp0109@gmail.com', 'horelad@gmail.com'], subject='updated products report', message_text='updated products report attached', attachment_filename='updated_products_report.csv')
        for product in products:
            # get product info
            product_info = get_product_info(product)
            if product_info:
                # store product info with gln in myssql database
                gln = find_key(product_info, COMPANY_ID_INDEX)[0]
                store_product_info(product_info, gln, user_d, pass_d, database, hostname)
                # create images folder if not exist two folder above the script
                # store product images in the images folder
                if not os.path.exists('../../allergyfood.my-new-vision.com/images'):
                    os.makedirs('../../allergyfood.my-new-vision.com/images')
                # get current foldr path
                current_path = os.path.dirname(os.path.abspath(__file__))
                # get it main media
                os.chdir('../../allergyfood.my-new-vision.com/images')
                medias = find_array(product_info, 'media_assets')
                if medias:
                    try:
                        # create array from the json string of the media that come without the square brackets
                        arr = json.loads('['+medias+']')
                        # iterate over the array and get all medias
                        for media in arr:
                            download_media_product(product, media['id'])
                    except Exception as e:
                        print(e)
                os.chdir(current_path)

    if 'a' in actions and actions['a']:
        companies = get_companies()
        for company in companies:
            gln, name = company
            create_report(gln, name)

    if 'd' in actions and actions['d']:
        # get all companies
        companies = get_companies()
        # iterate over the companies
        for company in companies:
            # get the company gln and get all products of the company
            gln, name = company
            products = get_company_products(gln)
            if not products:
                # write to log file
                with open('no_products_company.log', 'a') as f:
                    f.write(gln +'\n')
            # find the products that not exist in the database
            # get the products that not exist in the database
            products_exist_in_db = get_products_exist_in_db(gln, user_d, pass_d, database, hostname)
            products_not_exist = list(set(products) - set(products_exist_in_db))
            for product in products_not_exist:
                # get product info
                product_info = get_product_info(product)
                if product_info:
                    # store product info with gln in myssql database
                    store_product_info(product_info, gln, user_d, pass_d, database, hostname)
                    # create images folder if not exist two folder above the script
                    # store product images in the images folder
                    if not os.path.exists('../../allergyfood.my-new-vision.com/images'):
                        os.makedirs('../../allergyfood.my-new-vision.com/images')
                    # get current foldr path
                    current_path = os.path.dirname(os.path.abspath(__file__))
                    # get it main media
                    os.chdir('../../allergyfood.my-new-vision.com/images')
                    medias = find_array(product_info, 'media_assets')
                    if medias:
                        try:
                            # create array from the json string of the media that come without the square brackets
                            arr = json.loads('['+medias+']')
                            # iterate over the array and get all medias
                            for media in arr:
                                download_media_product(product, media['id'])
                        except:
                            print('error in media, medias: ' + medias)
                    os.chdir(current_path)

                else:
                    # write to log file the product that not found
                    with open('not_found_products.log', 'a') as f:
                        f.write(product + '\n')




    inquire_GS1_fields()