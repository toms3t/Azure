import datetime
import logging
import os
import json
import gspread
import azure.functions as func
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from azure.cosmos import exceptions, CosmosClient, PartitionKey
from oauth2client.service_account import ServiceAccountCredentials
try:
    from ..secrets import Secrets
except:
    print('Secrets module could not be imported')


cosmos_url = Secrets.cosmos_url
cosmos_key = Secrets.cosmos_key
sendgrid_key = Secrets.sendgrid_key
client = CosmosClient(cosmos_url, cosmos_key)
query_email = Secrets.query_email
test_from_email = Secrets.test_from_email
test_to_email = Secrets.test_to_email
GSHEET_CREDS = Secrets.gsheet_creds
GSHEET_NAME = Secrets.gsheet_name
HOLIDAYS = ["Valentine's Day", "Professional Assistant's Day", "Mother's Day", 'Thanksgiving', 'Christmas']

database_name = "Contacts"
container_name = "Contacts"

database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

def gsheet_export(GSHEET_CREDS, GSHEET_NAME):
    customers = []
    scope = [
        'https://spreadsheets.google.com/feeds', 
        'https://www.googleapis.com/auth/drive'
        ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GSHEET_CREDS, scope)
    client = gspread.authorize(credentials)
    gsheet = client.open(GSHEET_NAME).sheet1
    gsheet_data = gsheet.get_all_values()
    for row in gsheet_data[1:]:
        dates = row[1].split(',')
        dates = [date.strip() for date in dates]
        other_event = ''
        if dates[-1] not in HOLIDAYS:
            other_event = dates[-1]

        customer_reminder_holidays = []
        other_event_plus_date = {}
        if other_event:
            other_event_plus_date[other_event] = row[2]
            customer_reminder_holidays = dates[:-1]
        else:
            customer_reminder_holidays = dates

        first_name, email = row[5], row[3]

        customer_json = {
            'id': '1',
            'first_name': first_name, 
            'email': email, 
            'holidays': customer_reminder_holidays, 
            'special_date': other_event_plus_date
            }
        customers.append(customer_json)

    return(customers)

def cosmos_import(customers):
    print('Importing customers to CosmosDB....')
    for customer_json in customers:
        print(customer_json)
        try:
            container.create_item(body=customer_json)
            print('Customer added successfully')
        except Exception as e:
            s = str(e)
            if "id already exists in the system":
                print('The customer already exists in the database')
            else:
                print(s)

def find_customers_to_remind():
    pass

def cosmos_query_items(email_address):
    for item in container.query_items(
        query="SELECT * FROM Contacts p WHERE p.email = '{}'".format(query_email),
        enable_cross_partition_query=True,
    ):
        return(json.dumps(item, indent=True))


def send_mail(to_address, from_address, body):
    message = Mail(
        from_email='{}'.format(from_address),
        to_emails='{}'.format(to_address),
        subject='Testing!',
        html_content='{}'.format(body))
    try:
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    customer_list = gsheet_export(GSHEET_CREDS, GSHEET_NAME)
    cosmos_import(customer_list)
    cosmos_json = cosmos_query_items(query_email)
    # send_mail(test_to_email, test_from_email, cosmos_json)
    

    
