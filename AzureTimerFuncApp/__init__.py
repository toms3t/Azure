import datetime
import json
import logging
import subprocess

import azure.functions as func
import gspread
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from oauth2client.service_account import ServiceAccountCredentials
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, template_id

try:
    from ..secrets import Secrets
except:
    print('Secrets module could not be imported')


COSMOS_URL = Secrets.cosmos_url
COSMOS_KEY = Secrets.cosmos_key
SENDGRID_KEY = Secrets.sendgrid_key
CLIENT = CosmosClient(COSMOS_URL, COSMOS_KEY)
QUERY_EMAIL = Secrets.query_email
TEST_FROM_EMAIL = Secrets.test_from_email
TEST_TO_EMAIL = Secrets.test_to_email
GSHEET_CREDS = Secrets.gsheet_creds
GSHEET_NAME = Secrets.gsheet_name
HOLIDAYS_2020 = {'test_holiday': '07/29/2020', 'thanksgiving': '11/26/2020', 'christmas': '12/25/2020'}
HOLIDAYS_2021 = {"valentine_day": '02/14/2021', "assistant_day": '04/21/2021', "mother_day": '05/09/2021', 'thanksgiving': '11/25/2021', 'christmas': '12/25/2021'}
HOLIDAYS_2022 = {"valentine_day": '02/14/2022', "assistant_day": '04/27/2022', "mother_day": '05/08/2022', 'thanksgiving': '11/24/2022', 'christmas': '12/25/2022'}
HOLIDAYS_2023 = {"valentine_day": '02/14/2023', "assistant_day": '04/26/2023', "mother_day": '05/14/2023', 'thanksgiving': '11/23/2023', 'christmas': '12/25/2023'}
DATABASE_NAME= "Contacts"
CONTAINER_NAME = "Contacts"
DATABASE = CLIENT.get_database_client(DATABASE_NAME)
CONTAINER = DATABASE.get_container_client(CONTAINER_NAME)

def gsheet_export(GSHEET_CREDS, GSHEET_NAME):
    customers = []
    special_name = ''
    scope = [
        'https://spreadsheets.google.com/feeds', 
        'https://www.googleapis.com/auth/drive'
        ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GSHEET_CREDS, scope)
    gclient = gspread.authorize(credentials)
    gsheet = gclient.open(GSHEET_NAME).sheet1
    gsheet_data = gsheet.get_all_values()
    for row in gsheet_data[1:]:
        if row[7] == 'Birthday':
            special_name = row[11]
        elif row[7] == 'Anniversary':
            special_name = row[5]

        first_name, email, ann_name, holidays, ann_date, birthday_date, birthday_name = row[5], row[3], row[6], row[1], row[2], row[10], row[-1]

        customer_json = {
            'id': '1',
            'first_name': first_name, 
            'email': email, 
            'holidays': holidays, 
            'ann_date': ann_date,
            'birthday_date': birthday_date,
            'ann_name': ann_name,
            'birthday_name': birthday_name
            }
        customers.append(customer_json)

    return(customers)

def cosmos_import(customers):
    print('Importing customers to CosmosDB....')
    for customer_json in customers:
        try:
            CONTAINER.create_item(body=customer_json)
            print('Customer added successfully')
        except Exception as e:
            s = str(e)
            if "id already exists in the system" in s:
                print('The customer already exists in the database')
            else:
                print(s)

def reminder_date_check(special_date):
    pattern = re.compile('(\d+)\/(\d+)\/(\d+)')
    try:
        special_month, special_day, special_year = int(re.search(pattern, special_date).group(1)), int(re.search(pattern, special_date).group(2)), int(re.search(pattern, special_date).group(3))
        special_date_obj = datetime.date(year=special_year, month=special_month, day=special_day)
    except AttributeError:
        return False
    today = datetime.date.today()
    date_diff = str(special_date_obj - today)
    try:
        date_diff = int(re.search('(.*) day', date_diff).group(1))
    except AttributeError:
        return False
    if date_diff <= 6 and date_diff >= 0:
        return True
    return False

def get_new_customer_reminders():
    documents = list(CONTAINER.read_all_items(max_item_count=8000))
    print('Found {0} items'.format(item_list.__len__()))
    birthday_reminders = {}
    ann_reminders = {}
    holiday_reminders = {}
    pattern = re.compile('(\d+)\/(\d+)\/(\d+)')
    for cust_doc in documents:
        # print(cust_doc)
        try:
            birthday_date = cust_doc['birthday_date']
            birthday_name = cust_doc['birthday_name']
            if reminder_date_check(birthday_date):
                birthday_reminders[cust_doc['email']] = (birthday_name, birthday_date)
        except KeyError:
            pass
        try: 
            ann_date = cust_doc['ann_date']
            ann_name = cust_doc['ann_name']
            if reminder_date_check(ann_date):
                ann_reminders[cust_doc['email']] = (ann_name, ann_date)
        except KeyError:
            pass
        try:
            holidays = cust_doc['holidays']
            for holiday in holidays:
                if reminder_date_check(holiday):
                    holiday_reminders[cust_doc['email']] = holiday
        except KeyError:
            pass
    return birthday_reminders, ann_reminders, holiday_reminders

def cosmos_query_items(email_address):
    for item in CONTAINER.query_items(
        query="SELECT * FROM Contacts p WHERE p.email = '{}'".format(query_email),
        enable_cross_partition_query=True,
    ):
        return(json.dumps(item, indent=True))

def email_customers(from_address, to_address, template_id, special_name=None):
    curl_cmd = """
            curl -X "POST" "https://api.sendgrid.com/v3/mail/send" \
            -H 'Authorization: Bearer {}' \
            -H 'Content-Type: application/json' \
            -d '{{
        "from":{{
            "email":"{}"
        }},
        "personalizations":[ 
            {{
                "to":[
                    {{
                    "email":"{}"
                    }}
                ],
                "dynamic_template_data":{{
                    "special_name":"{}"
                }}
            }}
        ],
        "template_id":"{}"
        }}'
        """.format(SENDGRID_KEY, from_address, to_address, template_id, special_name)
    subprocess.check_output(curl_cmd, shell=True, universal_newlines=True)


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    bday_template = sendgrid_template_ids['bday']
    mothers_day_template = sendgrid_template_ids['mothers']
    valentines_day_template = sendgrid_template_ids['valentines']
    thanksgiving_template = sendgrid_template_ids['thanksgiving']
    xmas_template = sendgrid_template_ids['xmas']
    assistant_day_template = sendgrid_template_ids['assistant']
    anniversary_template = sendgrid_template_ids['anniversary']
    customer_list = gsheet_export(GSHEET_CREDS, GSHEET_NAME)
    cosmos_import(customer_list)
    birthday_reminders, ann_reminders, holiday_reminders = get_new_customer_reminders()
    from_address = TEST_FROM_EMAIL
    if birthday_reminders:
        for k,v in birthday_reminders.items():
            email_customers(from_address, k, bday_template, k[v][0])
    if ann_reminders:
        for k,v in ann_reminders.items():
            email_customers(from_address, k, anniversary_template, k[v][0])
    if holiday_reminders:
        for k,v in holiday_reminders.items():
            if v == 'Thanksgiving':
                email_customers(from_address, k, thanksgiving_template)
            if v == "Mother's Day":
                email_customers(from_address, k, mothers_day_template)
            if v == 'Christmas':
                email_customers(from_address, k, xmas_template)
            if v == "Professional Assistant's Day":
                email_customers(from_address, k, assistant_day_template)
            if v == "Valentine's Day":
                email_customers(from_address, k, valentines_day_template)

