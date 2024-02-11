from os import environ

import aws_cdk as cdk

from stack import Stack

region = environ['REGION']
account = environ['ACCOUNT']
stack_name = environ['STACK_NAME']
image_repository = environ['IMAGE_REPOSITORY']
sender_address_parameter_name = environ['SENDER_ADDRESS_PARAMETER_NAME']
recipients_addresses_parameter_name = environ['RECIPIENTS_ADDRESSES_PARAMETER_NAME']

app = cdk.App()
env = cdk.Environment(region=region, account=account)
stack = Stack(
    app, 
    'Stack',
    env=env, 
    region=region,
    account=account,
    stack_name=stack_name,
    image_repository=image_repository,
    sender_address_parameter_name=sender_address_parameter_name, 
    recipients_addresses_parameter_name=recipients_addresses_parameter_name,
)

cdk.Tags.of(stack).add('stack-name', stack_name)
app.synth()
