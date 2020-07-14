from azure.cosmos import exceptions, CosmosClient, PartitionKey
import json
try:
    from secrets import Secrets
except:
    print('Secrets module could not be imported')
import datetime


url = Secrets.cosmos_url
key = Secrets.cosmos_key
# phone_num = Secrets.phone_num
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

# print(query_items(email))


def read_items():
    print('\n1.3 - Reading all items in a container\n')

    item_list = list(container.read_all_items(max_item_count=8000))
    print('Found {0} items'.format(item_list.__len__()))

    for doc in item_list:
        # print('Item Id: {0}'.format(doc.get('id')))
        print(doc)

# print(read_items())

def create_items(container, phone_num, first_name, last_name, email, remind_dates):
    print('Creating Items....')

    new_reminder = {
        'id': '1',
        'phone_num' : phone_num,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'remind_dates': remind_dates
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


# create_items(container, 'phone', 'first_name', 'last_name', 'test@test.com', ['2020-01-01', '2020-01-02'])


