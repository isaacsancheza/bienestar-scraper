import aws_cdk as cdk
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_applicationautoscaling as appscaling
from aws_cdk import aws_ecs_patterns as ecs_patterns
from constructs import Construct


class Stack(cdk.Stack):
    def __init__(
            self, 
            scope: Construct, 
            construct_id: str, 
            *,
            region: str,
            account: str,
            image_repository: str,
            sentry_dsn: str,
            sender_address_parameter_name: str,
            recipients_addresses_parameter_name: str,
            **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = dynamodb.TableV2(
            self,
            'Table',
            partition_key=dynamodb.Attribute(
                name='title',
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name='timestamp',
                type=dynamodb.AttributeType.NUMBER,
            ),
            billing=dynamodb.Billing.on_demand(),
            removal_policy=cdk.RemovalPolicy.DESTROY,
            time_to_live_attribute='ttl',
        )

        sender_address_parameter = ssm.StringParameter.from_secure_string_parameter_attributes(
            self,
            'SenderAddressParameter',
            parameter_name=sender_address_parameter_name,
        )

        recipients_addresses_parameter = ssm.StringParameter.from_secure_string_parameter_attributes(
            self,
            'RecipientsAddressesParameter',
            parameter_name=recipients_addresses_parameter_name,
        )

        image = ecs.EcrImage.from_registry(image_repository)
        
        vpc = ec2.Vpc.from_lookup(
            self, 
            'Vpc', 
            region=region,
            is_default=True, 
            owner_account_id=account, 
        )
        
        cluster = ecs.Cluster(
            self, 
            'Cluster', 
            vpc=vpc,
        )
        cluster.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        scheduled_fargate_task = ecs_patterns.ScheduledFargateTask(
            self, 
            'ScheduledFargateTask', 
            cluster=cluster, 
            scheduled_fargate_task_image_options=ecs_patterns.ScheduledFargateTaskImageOptions(
                image=image, 
                memory_limit_mib=2048, 
                environment={
                    'SENTRY_DSN': sentry_dsn,
                    'TABLE_NAME': table.table_name,
                    'SENDER_ADDRESS_PARAMETER_NAME': sender_address_parameter.parameter_name,
                    'RECIPIENTS_ADDRESSES_PARAMETER_NAME': recipients_addresses_parameter.parameter_name,
                },
            ),
            schedule=appscaling.Schedule.cron(hour='10', minute='0'),
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        table.grant_read_write_data(scheduled_fargate_task.task_definition.task_role)
        sender_address_parameter.grant_read(scheduled_fargate_task.task_definition.task_role)
        recipients_addresses_parameter.grant_read(scheduled_fargate_task.task_definition.task_role)

        cdk.CfnOutput(
            self,
            'TableName',
            value=table.table_name,
        )
