#!/usr/bin/env python3
from os import environ
from time import sleep
from typing import cast

import requests
from boto3 import client, resource
from boto3.dynamodb.conditions import Attr

from scraper import get_entries


TEMPLATE = """:newspaper: {title}
:calendar: {date}
:link: {link}
"""

TABLE_NAME = environ['TABLE_NAME']
PARAMETER_NAME = environ['PARAMETER_NAME']

ssm = client('ssm')
dynamodb = client('dynamodb')

table = resource('dynamodb').Table(TABLE_NAME)
endpoint = cast(dict, ssm.get_parameter(Name=PARAMETER_NAME, WithDecryption=True))['Parameter']['Value']


for entry in get_entries():
    try:
        table.put_item(
            Item=entry,
            ConditionExpression=Attr('title').not_exists(),
        )
    except dynamodb.exceptions.ConditionalCheckFailedException:
        continue
    data = {
        'Content': TEMPLATE.format(**entry),
    }
    response = requests.post(endpoint, json=data)
    if not response.ok:
        response.raise_for_status()
    sleep(1.5)
