![CrowdStrike](https://raw.github.com/CrowdStrike/Cloud-AWS/main/docs/img/cs-logo.png)

[![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)](https://twitter.com/CrowdStrike)

# S3 Bucket Protection Lambda function
This is the serverless function that is executed when a file is added or changed in the protected bucket.

## Contents
This lambda leverages the [CrowdStrike Python SDK](https://github.com/CrowdStrike/falconpy) to interact with the CrowdStrike Falcon API.

+ `falconpy-layer.zip` - Lambda layer containing the crowdstrike-falconpy package and all related dependencies.
+ `functions.py` - Function library containing the methods used to interact with AWS Security Hub.
+ `julian.py` - Helper library used to calculate julian dates used for unique IDs within AWS Security Hub.
+ `lambda_function.py` - The S3 Bucket Protection lambda handler.