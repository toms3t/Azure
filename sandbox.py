from azure.cosmos import exceptions, CosmosClient, PartitionKey
import json
try:
    from secrets import Secrets
except:
    print('Secrets module could not be imported')
import datetime
import re


url = Secrets.cosmos_url
key = Secrets.cosmos_key
client = CosmosClient(url, key)

database_name = "Contacts"
container_name = "Contacts"

database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

def read_items(id, partition_key):
    response = container.read_item(item='1', partition_key=email)
    return response

# print(read_items('1', phone_num))

def query_items(email):
    for item in container.query_items(
        query="SELECT * FROM Contacts p WHERE p.email = '{}'".format(email),
        enable_cross_partition_query=True,
    ):
        return(json.dumps(item, indent=True))

# print(query_items('test@test.com'))


def read_items():
    print('\n1.3 - Reading all items in a container\n')

    item_list = list(container.read_all_items(max_item_count=8000))
    print('Found {0} items'.format(item_list.__len__()))
    customers_to_remind = {}
    pattern = re.compile('(\d+)\/(\d+)\/(\d+)')
    for doc in item_list:
        # print(doc)
        try:
            special_date_dict = doc['special_date']
            special_date_to_name = doc['special_date_to_name']
        except KeyError:
            continue
        if special_date_dict:
            print(doc['special_date'])
            for k,v in special_date_dict.items():
                special_date = v
                special_month, special_day, special_year = int(re.search(pattern, special_date).group(1)), int(re.search(pattern, special_date).group(2)), int(re.search(pattern, special_date).group(3))
                special_date_obj = datetime.date(year=special_year, month=special_month, day=special_day)
                today = datetime.date.today()
                date_diff = str(special_date_obj - today)
                print(date_diff)
                date_diff = int(re.search('(.*) day', date_diff).group(1))
                if date_diff <= 6 and date_diff > 0:
                    customers_to_remind[doc['email']] = special_date_dict, special_date_to_name

    print(customers_to_remind)

print(read_items())






