#!/usr/bin/env python3
import sentry_sdk
from boto3 import client, resource
from boto3.dynamodb.conditions import Attr
from aws_lambda_powertools.utilities.parameters import get_parameters

from scraper import get_entries

parameters = get_parameters('/bienestar-scraper')

table_name = parameters['table-name']
sentry_dsn = parameters['sentry-dsn']
sender_address = parameters['sender-address']
sender_display_name = parameters['sender-display-name']
recipients_addresses = parameters['recipients-addresses'].split(',')

sentry_sdk.init(
    dsn=sentry_dsn,
)

template = """📰 {title}
📆 {date}
🔗 {link}
"""

ses = client('sesv2')
table = resource('dynamodb').Table(table_name)
dynamodb = client('dynamodb')

for entry in get_entries():
    try:
        table.put_item(
            Item=entry,
            ConditionExpression=Attr('title').not_exists(),
        )
    except dynamodb.exceptions.ConditionalCheckFailedException:
        continue
    
    ses.send_email(
        FromEmailAddress=f'{sender_display_name} <{sender_address}>',
        Destination={
            'ToAddresses': recipients_addresses,
        },
        Content={
            'Simple': {
                'Subject': {
                    'Data': 'Nuevo anuncio',
                    'Charset': 'utf-8',
                },
                'Body': {
                    'Text': {
                        'Data': template.format(**entry),
                        'Charset': 'utf-8',
                    },
                },   
            },
        },
    )
