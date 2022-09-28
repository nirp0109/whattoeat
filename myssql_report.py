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

            writer.writerow([row[2], row[3]['GPC_Category_Code'], row[3]['Trade_Item_Description']])




if __name__ == '__main__':
    create_csv_report()