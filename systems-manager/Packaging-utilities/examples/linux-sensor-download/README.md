# Creating a package without the installer

* The DEFAULT for install will be (latest-release)-2. For example if the latest release of the linux sensor is 5.34.9918
  the DEFAULT version installed would be 5.33.9808.  
  It is expected that once installed, sensor versions will be managed via the falcon console.

This guide describes how to setup AWS systems manager where the CrowdStrike binary is downloaded from the CrowdStrike
API.

## Preparing the Package

1) Create a new directory
2) Unzip the file package-without-binary.zip

```text
user@host linux-sensor-binary % ls -al
total 40
drwxr-xr-x  9 jharris  staff    288  9 Mar 20:07 .
drwx------@ 9 jharris  staff    288  9 Mar 20:04 ..
drwxr-xr-x  6 jharris  staff    192  8 Mar 18:35 CS_AMAZON
drwxr-xr-x  5 jharris  staff    160  5 Mar 17:14 CS_WINDOWS
-rw-r--r--  1 jharris  staff   1725  5 Mar 17:11 README.md
-rw-r--r--@ 1 jharris  staff    167  8 Mar 16:08 agent_list.json
drwxr-xr-x  3 jharris  staff     96  5 Mar 18:13 aws-automation-doc
-rw-r--r--  1 jharris  staff  10040  9 Mar 11:00 packager.py
drwxr-xr-x  4 jharris  staff    128  9 Mar 20:05 s3-bucket
```

The example contains the directories CS_AMAZON and CS_WINDOWS. Each directory should contain the following

* Install script that downloads the binary from the CrowdStrike API
* Uninstall script

```text
user@host CS_WINDOWS % ls -al
total 82056
drwxr-xr-x  5 jharris  staff       160  5 Mar 17:14 .
drwxr-xr-x  9 jharris  staff       288  9 Mar 20:38 ..
-rwxr-xr-x@ 1 jharris  staff      5784 25 Jun  2019 install-no-binary.ps1
-rwxr-xr-x@ 1 jharris  staff        50 25 Jun  2019 uninstall.ps1
```      

The root folder should contain an "agent_list.json" file. The agent_list.json file should list all the directories that
will be included in the package. The file should be in json format and contain a list of objects containing the
following keys * os * dir * file

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
  }
]
  ```

## Generating the Required Package Files

Execute the script "packager.py". The file performs the following functions dependent on the parameters provided

* No Params - The script will parse the agent_list.json file and generate the *.zip and manifest.json file that is added
  to the s3bucket folder.


* AWS_REGION and S3BUCKET Params - The script will generate the zip and manifest files and upload them to an s3bucket


* AWS_REGION and S3BUCKET and PACKAGE_NAME Params - The script will generate the zip and manifest files upload to the
  bucket and generate the package document in systems manager.

Usage

```txt
   % python3 packager.py -h

    usage: packager.py [-h] -r AWS_REGION -b S3BUCKET -p PACKAGE_NAME

    Script execution
    
    1) Iterates over the "dir's" and creates a Zip file of the contents with the name of "file".
    2) Checks for the existence of the S3 bucket and creates it if it does not exist
    3) Uploads the Zip files to a /falcon folder in the bucket.
```   

Example of the generated files in the s3bucket folder

```text
user@host s3-bucket % ls -al
total 86072
drwxr-xr-x  7 jharris  staff       224  9 Mar 20:58 .
drwxr-xr-x  9 jharris  staff       288  9 Mar 20:38 ..
-rw-r--r--  1 jharris  staff   2072000  9 Mar 20:42 CS_AMAZON.zip
-rw-r--r--  1 jharris  staff  41759324  9 Mar 20:42 CS_WINDOWS.zip
-rw-r--r--  1 jharris  staff     10038  5 Mar 18:13 Local-CrowdStrike-Automation-Doc.yml
-rw-r--r--  1 jharris  staff       414  9 Mar 20:42 manifest.json
-rw-r--r--  1 jharris  staff       148  9 Mar 20:42 packager.log
```
    




