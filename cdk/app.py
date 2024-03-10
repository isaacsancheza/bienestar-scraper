from os import environ

import aws_cdk as cdk

from stack import Stack

app = cdk.App()
env = cdk.Environment(
    region=environ['REGION'],
    account=environ['ACCOUNT'],
)
stack = Stack(
    app, 
    'Stack',
    env=env,
    stack_name='bienestar-scraper',
)

cdk.Tags.of(stack).add('project', 'bienestar-scraper')
app.synth()
