import time
import json
import os

import boto3
from botocore.exceptions import ClientError

# TODO: add logging and debug level and update all prints to loggers that listen to debug level


def get_remote_session(resource_type, session_type, account_id, region, role_name):
    """
    Assume into target account and generate a boto client session

    :param resource_type: Type of AWS resource for your session
    :param session_type: Type of client for your session
    :param account_id: Remote AWS account number where you want to create the session
    :param region: Region where you'll create the session in remote AWS account
    :param role_name: Name of IAM Role you want to assume in remote account
    :return: Boto3 session in remote account of the specified resource
    """

    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    role_session_name = "ec2-isolation-" + str(time.time())

    sts = boto3.client("sts")
    try:
        response = sts.assume_role(RoleArn=role_arn, RoleSessionName=role_session_name)
    except ClientError as e:
        print(f"Failed to assume into account: {e}")

    if session_type == "client":
        try:
            session = boto3.client(
                resource_type,
                aws_access_key_id=response["Credentials"]["AccessKeyId"],
                aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
                aws_session_token=response["Credentials"]["SessionToken"],
                region_name=region,
            )
            return session
        except ClientError as e:
            print(f"Failed to create client session: {e}")

    elif session_type == "resource":
        try:
            session = boto3.resource(
                resource_type,
                aws_access_key_id=response["Credentials"]["AccessKeyId"],
                aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
                aws_session_token=response["Credentials"]["SessionToken"],
                region_name=region,
            )
            return session
        except ClientError as e:
            print(f"Failed to create resource session: {e}")
    else:
        raise Exception("Argument 'session_type' can only be 'client' or 'resource")


def get_vpc_id(ec2_client, instance_id):
    try:
        vpc_id = ec2_client.describe_instances(InstanceIds=[instance_id])["Reservations"][0][
            "Instances"
        ][0]["VpcId"]
        return vpc_id
    except ClientError as e:
        print(f"Failed to get VPC ID for instance: {instance_id}: {e}")


def create_isolation_security_group(ec2_resource, ec2_client, name, description, vpc_id):
    """Creates the isloation Security Group if it doesn't exist"""
    try:
        sg = ec2_resource.create_security_group(
            GroupName=name,
            Description=description,
            VpcId=vpc_id,
            TagSpecifications=[
                {
                    "ResourceType": "security-group",
                    "Tags": [
                        {"Key": "Name", "Value": name},
                    ],
                },
            ],
        )
        sg.revoke_egress(
            IpPermissions=[
                {
                    "IpProtocol": "-1",
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                    "Ipv6Ranges": [],
                    "PrefixListIds": [],
                    "UserIdGroupPairs": [],
                }
            ]
        )
        print(f"Create isolation Security Group: {sg.id}")
        return sg.id
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidGroup.Duplicate":
            print("Security Group already exists, skipping creation")
            response = ec2_client.describe_security_groups(
                GroupNames=[name],
            )
            return response["SecurityGroups"][0]["GroupId"]


def apply_isolation_security_group(ec2_client, instance_id, security_group_id):
    """Replaces all security groups with a security group that deny all network access"""
    try:
        ec2_client.modify_instance_attribute(Groups=[security_group_id], InstanceId=instance_id)
        print(f"Successfully applied isolation Security Group: {security_group_id}")
    except Exception as e:
        print(f"Failed to apply Security Group: {e}")


def remove_instance_profile_associations(ec2_client, instance_id):
    """
    Checks if an Instance Profile is associated to the provided instance and removes it if an
    association exists. This is performed to remove access from a potentially compromised instance.
    """
    associations = ec2_client.describe_iam_instance_profile_associations(
        Filters=[{"Name": "instance-id", "Values": [instance_id]}]
    )["IamInstanceProfileAssociations"]

    if len(associations) > 0:
        for association in associations:
            if association["State"] == "associated":
                instace_profile = association["IamInstanceProfile"]["Arn"]
                association_id = association["AssociationId"]
                ec2_client.disassociate_iam_instance_profile(AssociationId=association_id)
                print(f"Disassociated Instance Profile Role: {instace_profile} from {instance_id}")
    else:
        print(f"No Instance Profiles to detach from instance: {instance_id}")


def create_isolation_instance_profile(iam_client, name):
    """
    Creates the isolation IAM Instance Profile if it's not already created

    :param name: Name of IAM Role and Instance Profile Role
    :return: ARN of the IAM Instance Profile Role
    """

    # Create Role that'll be used for Instance Profile Role
    try:
        assume_role_policy = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        )
        iam_client.create_role(
            RoleName=name,
            Description="Isolation Instance Profile Role created for Incident Response",
            Path="/",
            AssumeRolePolicyDocument=assume_role_policy,
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print("IAM Role already exists, skipping creation")

    iam_client.attach_role_policy(RoleName=name, PolicyArn="arn:aws:iam::aws:policy/AWSDenyAll")

    # Attach Instance Profile to Role or identify existing and return ARN
    try:
        response = iam_client.create_instance_profile(InstanceProfileName=name, Path="/")
        iam_client.add_role_to_instance_profile(InstanceProfileName=name, RoleName=name)
        return response["InstanceProfile"]["Arn"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print("IAM Instance Profile already exists, skipping creation")
            response = iam_client.get_instance_profile(InstanceProfileName=name)
            return response["InstanceProfile"]["Arn"]


def apply_isolation_instance_profile(
    ec2_client, instance_profile_arn, instance_profile_name, instance_id
):
    """Applies the isolation IAM Instance Profile to the malicious EC2 instance"""

    # Handle race condition where new IAM Instance Profiles are not
    # immediately available after creation
    propogated = False
    for i in range(0, 100):
        while not propogated:
            try:
                ec2_client.associate_iam_instance_profile(
                    IamInstanceProfile={"Arn": instance_profile_arn, "Name": instance_profile_name},
                    InstanceId=instance_id,
                )
                propogated = True
                print(
                    f"Successfully applied isolation IAM Instance profile: {instance_profile_arn}"
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "InvalidParameterValue":
                    print("IAM Instance Profile not propogated, trying again")
                    time.sleep(2)


def lambda_handler(event, context):
    print(event)

    # Assign from event message
    instance_id = event["body"]["instance_id"]
    account_id = event["body"]["account_id"]
    region = event["body"]["region"]

    # Assign from environment variables
    target_execution_role_name = os.environ["TARGET_EXECUTION_ROLE_NAME"]
    instance_profile_name = os.environ["INSTANCE_PROFILE_NAME"]
    sg_name = os.environ["SG_NAME"]
    sg_description = os.environ["SG_DESCRIPTION"]

    # Generate remote boto3 sessions
    ec2 = get_remote_session("ec2", "client", account_id, region, target_execution_role_name)
    ec2_r = get_remote_session("ec2", "resource", account_id, region, target_execution_role_name)
    iam = get_remote_session("iam", "client", account_id, region, target_execution_role_name)

    # Create and apply isolation Instance Profile Role to deny all AWS API access
    instance_profile_arn = create_isolation_instance_profile(iam, instance_profile_name)
    remove_instance_profile_associations(ec2, instance_id)
    apply_isolation_instance_profile(ec2, instance_profile_arn, instance_profile_name, instance_id)

    # Create and apply isolation Security Group to deny all network access
    vpc_id = get_vpc_id(ec2, instance_id)
    sg_id = create_isolation_security_group(ec2_r, ec2, sg_name, sg_description, vpc_id)
    apply_isolation_security_group(ec2, instance_id, sg_id)
