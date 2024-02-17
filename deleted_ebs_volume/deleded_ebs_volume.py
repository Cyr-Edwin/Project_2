# import modules
import boto3
import datetime

# initiate resources
ec2_instance = boto3.client('ec2')
sns = boto3.client('sns')

# get all the EBS  snapshots
response = ec2_instance.describe_snapshots(OwnerIds = ['self']) ['Snapshots']

# get EC2 instance IDs with running state
ec2_instance_ids = ec2_instance.describe_instances(Filters=[
        {
            'Name': 'instance-state-name',
            'Values': [
                'running',
            ]
        },
    ],)

# varibale ids
ids = set()

# deleted snapshots list
deleted_snapshots =[]

# subscribe to the sns topic
def subscribers(sns , topic_arn , emails):
    for email in emails:
        sns.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=  email
    )


