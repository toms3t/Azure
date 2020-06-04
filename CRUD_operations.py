from azure.cosmos import exceptions, CosmosClient, PartitionKey
import json

# import os

url = ""
key = ""
client = CosmosClient(url, key)

database_name = "Contacts"
container_name = "contacts"

database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

for item in container.query_items(
    query='SELECT * FROM contacts p WHERE p.id = ""',
    enable_cross_partition_query=True,
):
    print(json.dumps(item, indent=True))
