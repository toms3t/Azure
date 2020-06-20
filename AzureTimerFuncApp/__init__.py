import datetime
import logging
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
try:
    from ..secrets import Secrets
except:
    print('Secrets module could not be imported')
import azure.functions as func

from azure.cosmos import exceptions, CosmosClient, PartitionKey
import json

cosmos_url = Secrets.cosmos_url
cosmos_key = Secrets.cosmos_key
sendgrid_key = Secrets.sendgrid_key
client = CosmosClient(cosmos_url, cosmos_key)
query_email = Secrets.query_email
test_from_email = Secrets.test_from_email
test_to_email = Secrets.test_to_email

database_name = "Contacts"
container_name = "Contacts"

database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    def cosmos_query_items(email_address):
        for item in container.query_items(
            query="SELECT * FROM Contacts p WHERE p.email_address = '{}'".format(query_email),
            enable_cross_partition_query=True,
        ):
            return(json.dumps(item, indent=True))

    cosmos_json = cosmos_query_items(query_email)

    def send_mail(to_address, from_address, body):
        message = Mail(
            from_email='{}'.format(from_address),
            to_emails='{}'.format(to_address),
            subject='Sending with Twilio SendGrid is Fun!!',
            html_content='{}'.format(body))
        try:
            sg = SendGridAPIClient(sendgrid_key)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)

    send_mail(test_to_email, test_from_email, cosmos_json)

    
