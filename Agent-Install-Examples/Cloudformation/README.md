# Instructions 

* Create s3 bucket and upload lambda files contained in the lambda directory to the bucket

* Upload the agent install file for Amazon AMI to the same bucket

* Create API keys in falcon console for managing hosts

* Complete the CFT

## Overview
* Template will deploy an ASG with a host count of one.   An example install script using "user-data" is included. 
* The install script will pull the install file from the s3 bucket.
* API keys are stored in Env variables in lambda but should be stored in SSM parameter store for production
* Lambda Instance lifecycle hooks are used to remove the host from the falcon console when it is terminated.
