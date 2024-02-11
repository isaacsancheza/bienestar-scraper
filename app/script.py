#!/usr/bin/env python3
from os import environ
from typing import cast

from boto3 import client, resource
from boto3.dynamodb.conditions import Attr

from scraper import get_entries

template = """📰 {title}
📆 {date}
🔗 {link}
"""
table_name = environ['TABLE_NAME']
sender_address_parameter_name = environ['SENDER_ADDRESS_PARAMETER_NAME']
recipients_addresses_parameter_name = environ['RECIPIENTS_ADDRESSES_PARAMETER_NAME']

ssm = client('ssm')
ses = client('sesv2')
dynamodb = client('dynamodb')

table = resource('dynamodb').Table(table_name)
sender_address = cast(dict, ssm.get_parameter(Name=sender_address_parameter_name, WithDecryption=True))['Parameter']['Value']
recipients_addresses = cast(dict, ssm.get_parameter(Name=recipients_addresses_parameter_name, WithDecryption=True))['Parameter']['Value']

for entry in get_entries():
    try:
        table.put_item(
            Item=entry,
            ConditionExpression=Attr('title').not_exists(),
        )
    except dynamodb.exceptions.ConditionalCheckFailedException:
        continue
    
    ses.send_email(
        FromEmailAddress=sender_address,
        Destination={
            'ToAddresses': recipients_addresses.split(', '),
        },
        Content={
            'Simple': {
                'Subject': {
                    'Data': 'Nuevo anuncio de bienestar',
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
