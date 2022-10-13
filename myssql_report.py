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


if __name__ == '__main__':
    # create_csv_report()
    # create_GLN_table()
    create_category_table()
