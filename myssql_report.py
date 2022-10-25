import mysql.connector
from mysql.connector import errorcode
import csv
import datetime
import os
import sys
import re
import json

from dotenv import dotenv_values

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


def create_csv_report():
    """
    Create a CSV report from the MySQL database
    the PRODUCTS table contain the following fields: product_code, gln, gtin, product_info
    all fields are strings the product_info is json string that contains the following fields:GPC_Category_Code,Trade_Item_Description
    the CSV will contain GTIN,GPC_Category_Code,Trade_Item_Description
    """

    # reading .env
    (user, password, user_d, pass_d, hostname, database) = dotenv_values('.env').values()

    # connecting to the database
    try:
        cnx = mysql.connector.connect(user=user_d, password=pass_d, host=hostname, database=database)

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        sys.exit(1)

    # creating a cursor
    cursor = cnx.cursor()

    # creating a query fetching the json data from PRODUCTS table
    query = ("SELECT * FROM PRODUCTS")

    # executing the query
    cursor.execute(query)

    # fetching the data: GTIN,GPC_Category_Code,Trade_Item_Description the later two from json product_info
    data = cursor.fetchall()

       # creating a csv file
    with open('report.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['GTIN', 'GPC_Category_Code', 'Trade_Item_Description'])
        for row in data:
            json_data = json.loads(row[3])

            writer.writerow([row[2], find_key(json_data,'GPC_Category_Code')[0], find_key(json_data, 'Trade_Item_Description')[0]])


def create_GLN_table():
    """
    create GLN table at mysql with name GLN from GLN.csv
    """
    # reading .env
    (user, password, user_d, pass_d, hostname, database) = dotenv_values('.env').values()

    # connecting to the database
    try:
        cnx = mysql.connector.connect(user=user_d, password=pass_d, host=hostname, database=database)

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        sys.exit(1)

    # creating a cursor
    cursor = cnx.cursor()

    # creating a query fetching the json data from PRODUCTS table
    query = ("CREATE TABLE GLN (GLN VARCHAR(13), NAME VARCHAR(255), PRIMARY KEY (GLN))")

    # executing the query
    cursor.execute(query)
    cnx.commit()

    # creating a csv file
    with open('GLN.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for row in reader:
            query = ("INSERT INTO GLN (GLN, NAME) VALUES (%s, %s)")
            data = (row[0], row[1])
            cursor.execute(query, data)
            cnx.commit()


def create_category_table():
    """
    create category table at mysql with name CATEGORY from Products_categories.csv
    On the csv each category is on a new line appear at the first column on the second column there are list GPC category codes remove the '"' char and trim spaces
    """
    # reading .env
    (user, password, user_d, pass_d, hostname, database) = dotenv_values('.env').values()

    # connecting to the database
    try:
        cnx = mysql.connector.connect(user=user_d, password=pass_d, host=hostname, database=database)

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        sys.exit(1)

    # creating a cursor
    cursor = cnx.cursor()

    # creating a table if not exist
    query = ("CREATE TABLE IF NOT EXISTS CATEGORY (CATEGORY VARCHAR(255), GPC_CATEGORY_CODE VARCHAR(255), PRIMARY KEY (CATEGORY))")

    # executing the query
    cursor.execute(query)
    cnx.commit()

    # creating a csv file
    with open('Products_categories.csv', 'r', encoding='utf-8') as file:
        file.lines = file.readlines()
        for line in file.lines:
            # split the line by comman that is not surrounded by double quotes
            columns = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)
            category = columns[0].replace('"', '').strip()
            gpc_category_code = columns[1].replace('"', '').strip()+columns[2].replace('"', '').strip()

            query = ("INSERT INTO CATEGORY (CATEGORY, GPC_CATEGORY_CODE) VALUES (%s, %s)")
            data = (category, gpc_category_code)
            cursor.execute(query, data)
            cnx.commit()

def map_category_to_gpc_category():
       """
       load table CATEGORY read id column and list seperated by comma from GPC_CATEGORY_CODE
       and insert them in table GPC_CATEGORY_CODE to field CATEGORY and GPC_CODE
       """
       # reading .env
       (user, password, user_d, pass_d, hostname, database) = dotenv_values('.env').values()

        # connecting to the database
       try:
           cnx = mysql.connector.connect(user=user_d, password=pass_d, host=hostname, database=database)

       except mysql.connector.Error as err:
           if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
               print("Something is wrong with your user name or password")
           elif err.errno == errorcode.ER_BAD_DB_ERROR:
               print("Database does not exist")
           else:
               print(err)
           sys.exit(1)

        # creating a cursor
       cursor = cnx.cursor()

        # creating a table if not exist
       query = ("CREATE TABLE IF NOT EXISTS GPC_CATEGORY_CODE (CATEGORY VARCHAR(255), GPC_CODE VARCHAR(255))")

        # executing the query
       cursor.execute(query)
       cnx.commit()

        #read each row from CATEGORY table and insert them in GPC_CATEGORY_CODE
       query = ("SELECT id, GPC_CATEGORY_CODE FROM CATEGORY")
       cursor.execute(query)
       data = cursor.fetchall()
       for row in data:
           category = row[0]
           gpc_category_code = re.findall(r'\d+', row[1])
           for gpc in gpc_category_code:
               query = ("INSERT INTO GPC_CATEGORY_CODE (CATEGORY, GPC_CODE) VALUES (%s, %s)")
               data = (category, gpc.strip())
               cursor.execute(query, data)
               cnx.commit()


def add_columns_to_products_table():
    """
    read json from table PRODUCTS at column product_info
    extract from it the following GS1 fields: Short_Description, BrandName, Sub_Brand_Name, Ingredient_Sequence_and_Name, Allergen_Type_Code_and_Containment, Allergen_Type_Code_and_Containment_May_Contain
    and add them in them same order to the table PRODUCTS as Short_Description, Brand_Name, Sub_Brand_Name, Ingredients, Allergens_Contain, Allergens_May_Contain
    """
    # reading .env
    (user, password, user_d, pass_d, hostname, database) = dotenv_values('.env').values()

    # connecting to the database
    try:
        cnx = mysql.connector.connect(user=user_d, password=pass_d, host=hostname, database=database)

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        sys.exit(1)

    # creating a cursor
    cursor = cnx.cursor()

    # read each row from PRODUCTS table and extract the GS1 fields
    query = ("SELECT id, product_info FROM PRODUCTS")
    cursor.execute(query)
    data = cursor.fetchall()
    for row in data:
        product_id = row[0]
        json_data = json.loads(row[1])
        short_description, brand_name, sub_brand_name, ingredients, allergens_contain, allergens_may_contain = '', '', '', '', '', ''
        # fields = ['Short_Description', 'BrandName' ,'Sub_Brand_Name', 'Ingredient_Sequence_and_Name']

        field_values = []
        # for field in fields:
        #     try:
        #         val = find_key(json_data, field)
        #         if type(val) == list:
        #             if len(val) == 0:
        #                 field_values.append('')
        #             else:
        #                 field_values.append(val[0])
        #         else:
        #             field_values.append(val)
        #     except:
        #         val = find_array(json_data, field)[0]
        #         if type(val) == list:
        #             if len(val) == 0:
        #                 field_values.append('')
        #             else:
        #                 field_values.append(val[0])
        #         else:
        #             field_values.append(val)
        #
        #
        # pattern_str = "(?<=\"{}\":\[).+?(?=\])".format('Allergen_Type_Code_and_Containment')
        # compile_pattern = re.compile(pattern_str)
        # allergen_contain = compile_pattern.findall(json_data)
        # pattern_str = "(?<=\"{}\":\[).+?(?=\])".format('Allergen_Type_Code_and_Containment_May_Contain')
        # compile_pattern = re.compile(pattern_str)
        # allergen_may_contain = compile_pattern.findall(json_data)
        #
        # try:
        #     allergen_contain_set = set(map(lambda item: json.loads(item)['value'], allergen_contain))
        # except:
        #     allergen_contain_set = set(
        #         map(lambda item: json.loads(item)['value'], re.findall(r"\{.*?\}", allergen_contain[0])))
        # try:
        #     allergen_may_contain_set = set(map(lambda item: json.loads(item)['value'], allergen_may_contain))
        # except:
        #     allergen_may_contain_set = set(
        #         map(lambda item: json.loads(item)['value'], re.findall(r"\{.*?\}", allergen_may_contain[0])))
        #
        # # get allergen contain and may contain from product info(labels)
        # pretty_alleregen_contain = list(allergen_contain_set)
        # pretty_alleregen_contain = sorted(pretty_alleregen_contain)
        # field_values.append(','.join(pretty_alleregen_contain))
        # pretty_alleregen_may_contain = list(allergen_may_contain_set)
        # pretty_alleregen_may_contain = sorted(pretty_alleregen_may_contain)
        # field_values.append(','.join(pretty_alleregen_may_contain))

        # insert the GS1 fields in the same order to the table PRODUCTS
        val = find_array(json_data, 'Product_Status')
        if val and len(val) > 0:
            json_value = json.loads(val)
            field_values.append(json_value['code'])
            status_int = int(json_value['code'])
            # active is 1 if status is 6303
            if status_int == 6303:
                field_values.append(1)
            else:
                field_values.append(0)
        else:
            field_values.append(0)
            field_values.append(0)


        # query = ("UPDATE PRODUCTS SET Short_Description=%s, Brand_Name=%s, Sub_Brand_Name=%s, Ingredients=%s, Allergens_Contain=%s, Allergens_May_Contain=%s WHERE id=%s")
        query = ("UPDATE PRODUCTS SET Product_Status=%s, Active=%s WHERE id=%s")
        cursor.execute(query, field_values)
        cnx.commit()



if __name__ == '__main__':
    # create_csv_report()
    # create_GLN_table()
    # create_category_table()
    # map_category_to_gpc_category()
    add_columns_to_products_table()


