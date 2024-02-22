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

#  send sns message
def send_sns(sns , snapshot_id):
    topic_name="topic"
    # create a topic if does not exist
    try:
        response = sns.create_topic(Name=topic_name)
        topic_arn= response['TopicArn']
        print("response:"+ topic_arn)

        # subscribe the recipient to the topic
        subscribers(sns , topic_arn , ['cyredwin1@gmail.com'])
        
        # create  subject and message  variables
        subject = "EBS Snaspshot has/have deleted"
        message = f"Following the policy, the snapshots were deleted.\n\nsnapshot_id:  {snapshot_id}\n\nTimestamp: {datetime.datetime.now()} UTC"
        
        # published the topic
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
    except sns.exceptions.TopicLimitExceededException:
        # assume topics already exist
        topic_list = sns.list_topics()["Topics"]
        topic_arn = next((topic_list["TopicArn"]for topic in topic_list if topic_list["TopicArn"].endswith(":" + topic_name)), None)
        # print topic_arn
        print(topic_arn)
        
# retrieved instance IDs
        for reservation in ec2_instance_ids["Reservations"]:
            for instance in reservation["Instances"]:
                ids.add(instance['InstanceId'])

# create attached_volume and status variables
attached_volume = []
status =[] 

# get attached volume ids
for id in ec2_instance_ids['Reservations']:
    for instance in id["Instances"]:
        attached_volume.append(instance['BlockDeviceMappings'][0]['Ebs']['VolumeId'])
        status.append(instance['BlockDeviceMappings'][0]['Ebs']['Status'])
print("attached Volume: " , attached_volume )
print("status :" , status )
print("\n\n")

# ietare from the describe snapshots
for resp in response:
    # get the value of key= 'VolumeId'
    vol_id = resp.get('VolumeId')
    print(vol_id)
    snaps_id = resp['SnapshotId']
    if vol_id not in attached_volume:
        ec2_instance.delete_snapshot(SnapshotId=snaps_id)
        print(f"Snapshot ID : {snaps_id} is being deleted since it is not attached to any volume.")
        send_sns(sns , snaps_id)
        deleted_snapshots.append(snaps_id)
    else:
        try:
            # check if the volume still exist
            volume = ec2_instance.describe_volumes(VolumeIds=[vol_id])
            if not volume['Volumes'][0]['Attachments']:
                ec2_instance.delete_snapshot(SnapshotId=snaps_id)
                print(f"Snapshot ID : {snaps_id} being deleted since it is not attached to any volume.")
                send_sns(sns , snaps_id)
        except ec2_instance.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "InvalidVolume.NotFound":
                # volume associated with snapshot is not found
                ec2_instance.delete_snapshot(SnapshotId=snaps_id)
                print(f"Snapshot ID : {snaps_id} since its associate volume was not find")
