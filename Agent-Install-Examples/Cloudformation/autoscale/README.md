# Background

An example of an autoscale group consisting and Amazon Linux 2 instances in an autoscale group.

We use user-data scripts to install the sensor during intialisation and autoscale Lifecycle hooks to remove the instance from the Falcon Console when it is terminated. 

# Instructions 

1. Create s3 bucket 

2. Upload lambda files contained in the lambda directory to the bucket

    The lambda files required are 

    * manage_instance.zip 
    * layer.zip

3. Upload the relevant Agent install file for Amazon AMI to the same bucket

4. Create API keys in falcon console for managing hosts

5. Complete the CFT

## Overview
* Template will deploy an ASG with a host count of one.   An example install script using "user-data" is included. 
* The install script will pull the install file from the s3 bucket.
* API keys are stored in Env variables in lambda but should be stored in SSM parameter store for production
* Lambda Instance lifecycle hooks are used to remove the host from the falcon console when it is terminated.
