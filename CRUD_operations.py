from azure.cosmos import exceptions, CosmosClient, PartitionKey
import json
try:
    from secrets import Secrets
except:
    print('Secrets module could not be imported')
import datetime


url = Secrets.cosmos_url
key = Secrets.cosmos_key
phone_num = Secrets.phone_num
client = CosmosClient(url, key)

database_name = "Contacts"
container_name = "contacts"

database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

def read_items(id, partition_key):
    response = container.read_item(item='1', partition_key=phone_num)
    return response

# print(read_items('1', phone_num))

def query_items():
    for item in container.query_items(
        query="SELECT * FROM contacts p WHERE p.phone_num = '{}'".format(phone_num),
        enable_cross_partition_query=True,
    ):
        return(json.dumps(item, indent=True))

# print(query_items())


def read_items():
    print('\n1.3 - Reading all items in a container\n')

    item_list = list(container.read_all_items(max_item_count=10))
    print('Found {0} items'.format(item_list.__len__()))

    for doc in item_list:
        # print('Item Id: {0}'.format(doc.get('id')))
        print(doc)

# print(read_items())

def create_items(container, phone_num, name, remind_date):
    print('Creating Items....')

    new_reminder = {
        'id': '1',
        'phone_num' : phone_num,
        'name': name,
        'remind_date': remind_date
        }
    try:
        container.create_item(body=new_reminder)
        print('Item added successfully')
    except Exception as e:
        s = str(e)
        if "id already exists in the system":
            print('The phone number already exists in the database')
        else:
            print(s)


# create_items(container, '4444443844', 'Sue', '2020-01-01')