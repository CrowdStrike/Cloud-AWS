# Python Utility to Create AWS Systems Manager Package

##Instructions
The python script "packager.py" will create files required to create a custom automation package in AWS Systems Manager. 

1) Create a directory for each os that you wish to generate a custom package. 

2) Each directory should contain the following
    1) Install script
    2) Uninstall script

3) The root folder should contain an "agent_list.json" file. The agent_list.json file should list all the directories 
    that will be included in the package.
    The file should be in json format and contain a list of objects containing the following keys 
    * os
    * dir
    * file
 
    [Supported package platforms and architectures](https://docs.aws.amazon.com/systems-manager/latest/userguide/distributor.html#what-is-a-package-platforms)

    An example 'agent_list.json' file. 
  ```yaml
[
  {
    "os": "windows",
    "dir": "CS_WINDOWS",
    "file": "CS_WINDOWS.zip"
  },
  {
    "os": "amazon",
    "dir": "CS_AMAZON",
    "file": "CS_AMAZON.zip"
  },
  {
    "os": "ubuntu",
    "dir": "CS_UBUNTU",
    "file": "CS_UBUNTU.zip"
  }
]
  ```

4) Generating the Package 
   
   Usage
    ```code
    % python3 generate_ssm_package_files.py -h 

    usage: generate_ssm_package_files.py [-h] -r AWS_REGION -b S3BUCKET
   ```
    Script execution
    
    1) Iterates over the "dir's" and creates a Zip file of the contents with the name of "file".
    2) Checks for the existence of the S3 bucket and creates it if it does not exist
    3) Uploads the Zip files to a /falcon folder in the bucket.
    
    




