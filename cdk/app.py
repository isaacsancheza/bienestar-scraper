from os import environ

import aws_cdk as cdk

from stack import Stack


region = environ['REGION']
account = environ['ACCOUNT']
stack_name = environ['STACK_NAME']
parameter_name = environ['PARAMETER_NAME']
image_repository = environ['IMAGE_REPOSITORY']

app = cdk.App()
env = cdk.Environment(region=region, account=account)
stack = Stack(
    app, 
    'Stack',
    env=env, 
    region=region,
    account=account,
    stack_name=stack_name, 
    parameter_name=parameter_name,
    image_repository=image_repository,
)

cdk.Tags.of(stack).add('stack-name', stack_name)
app.synth()
