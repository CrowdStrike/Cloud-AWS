# Packaging Utilities

## Create your AWS SSM package

Scripts and example files for creating your
ssm [Distributor](https://docs.aws.amazon.com/systems-manager/latest/userguide/distributor.html) package.

Two zip files are included that contain example files and documentation for creating a CrowdStrike package for AWS
Systems Manager.

zip-files - A folder containing two zip files

* `Package-sensor-download.zip` contains the files required to create a package where the sensor is downloaded from the
  CrowdStrike sensor download API.

* `Package-with-binary.zip` contains the files required to create a package where the sensor is bundled with the
  installer scripts and pushed to the host using the systems manager agent.

Select one of the above zip files and unzip its contents to a new location. Once unzipped follow the instructions in the
README.md file.