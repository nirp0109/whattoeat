import openfoodfacts

def main():
    data = openfoodfacts.facets.get_allergens()
    for item in data:
        if 'en:' in item['id']:
            print(item)


if __name__ == '__main__':
    main()
