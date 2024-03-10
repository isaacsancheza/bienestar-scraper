import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_applicationautoscaling as appscaling
from aws_cdk import aws_ecs_patterns as ecs_patterns
from constructs import Construct


class Config(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            /,
        ) -> None:
        super().__init__(
            scope,
            construct_id,
        )

        sender_domain = ssm.StringParameter.from_string_parameter_attributes(
            self,
            'SenderDomain',
            parameter_name='/bienestar-scraper/sender-domain',
        )

        sender_address = ssm.StringParameter.from_string_parameter_attributes(
            self,
            'SenderAddress',
            parameter_name='/bienestar-scraper/sender-address',
        )

        image_repository = ssm.StringParameter.from_string_parameter_attributes(
            self,
            'ImageRepository',
            parameter_name='/bienestar-scraper/image-repository',
        )

        sender_display_name = ssm.StringParameter.from_string_parameter_attributes(
            self,
            'SenderDisplayName',
            parameter_name='/bienestar-scraper/sender-display-name',
        )

        recipients_addresses = ssm.StringListParameter.from_list_parameter_attributes(
            self,
            'RecipientsAddresses',
            parameter_name='/bienestar-scraper/recipients-addresses',
        )
        
        self._sender_domain = sender_domain
        self._sender_address = sender_address
        self._image_repository = image_repository
        self._sender_display_name = sender_display_name
        self._recipients_addresses = recipients_addresses

    @property
    def sender_domain(self) -> str:
        return self._sender_domain.string_value
    
    @property
    def sender_address(self) -> str:
        return self._sender_address.string_value
    
    @property
    def image_repository(self) -> str:
        return self._image_repository.string_value
    
    @property
    def sender_display_name(self) -> str:
        return self._sender_display_name.string_value

    @property
    def recipients_addresses(self) -> list[str]:
        return self._recipients_addresses.string_list_value


class Stack(cdk.Stack):
    def __init__(
            self, 
            scope: Construct, 
            construct_id: str, 
            /,
            *,
            env: cdk.Environment,
            stack_name: str,
        ) -> None:
        super().__init__(
            scope, 
            construct_id,
            env=env,
            stack_name=stack_name,
        )
        config = Config(
            self,
            'Config',
        )

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

        ssm.StringParameter(
            self,
            'TableNameParameter',
            string_value=table.table_name,
            parameter_name='/bienestar-scraper/table-name',
        )

        image = ecs.EcrImage.from_registry(config.image_repository)

        vpc = ec2.Vpc.from_lookup(
            self,
            'Vpc',
            is_default=True,
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
            ),
            schedule=appscaling.Schedule.cron(hour='10', minute='0'),
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        role = scheduled_fargate_task.task_definition.task_role

        table.grant_read_write_data(role)

        role.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'ssm:GetParametersByPath',
                ],
                resources=[
                    f'arn:aws:ssm:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:parameter/bienestar-scraper',
                ],
            ),
        )

        role.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'ses:SendEmail',
                ],
                resources=[
                    f'arn:aws:ses:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:identity/{config.sender_domain}',
                ],
                conditions={
                    'StringEquals': {
                        'ses:FromAddress': config.sender_address,
                        'ses:FromDisplayName': config.sender_display_name,
                    },
                },
            ),
        )

        cdk.CfnOutput(
            self,
            'TableName',
            value=table.table_name,
        )
