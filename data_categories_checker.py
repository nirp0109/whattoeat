import  pandas  as  pd

def main():
    """
    load report.csv file and load the Categories.csv file
    intersect records from both files and print the result
    do the intersection by compare the id column of Catrgories.csv with the GPC_Category_Code column of report.csv

    :return:
    """

    # load the report.csv file
    report = pd.read_csv('report.csv')

    # load the Categories.csv file
    categories = pd.read_csv('Categories.csv')

    # intersect records from both files and print the result
    # do the intersection by compare the id column of Catrgories.csv with the GPC_Category_Code column of report.csv
    food =  report.merge(categories, left_on='GPC_Category_Code', right_on='id', how='inner')

    # print the result
    print(food.columns)


    # remove from food the columns that are not needed, the colums that are not needed are: id, GPC_Category_Code, GPC_Category_Name
    food = food.drop(columns=['id', 'name', 'name_hebrew', 'level', 'isleaf'])

    print(report.shape)
    print(food.shape)

    # find the difference between the report.csv and the food dataframe
    diff = report.merge(food, how='outer', indicator=True).loc[lambda x : x['_merge']=='left_only']
    diff.drop(columns=['_merge'], inplace=True)

    print(diff.shape)

    # save the diff dataframe to a csv file
    diff.to_csv('diff.csv', index=False)
    food.to_csv('food.csv', index=False)




    print(report.columns)


if __name__ == "__main__":
    main()
