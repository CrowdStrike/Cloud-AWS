# Troubleshooting scripts
These python scripts provide examples for how to leverage the CrowdStrike API to perform development operations within your CrowdStrike deployment. There are two current examples that leverage different components of the [FalconPy SDK](https://github.com/CrowdStrike/falconpy). Command line usage for these two examples is exactly the same and detailed below.

## Usage
These scripts must be executed using python.
```bash
$ python3 falcon_discover_accounts.py -f [falcon_client_id] -s [falcon_client_secret] -c [command] --external_id {external_id} -a {local_account} -r {cloudtrail_bucket_region} -o {cloudtrail_bucket_owner_id} -i {iam_role_arn} -q 100 -l
```
__*or*__
```bash
$ python3 fd_accounts.py -f [falcon_client_id] -s [falcon_client_secret] -c [command] --external_id {external_id} -a {local_account} -r {cloudtrail_bucket_region} -o {cloudtrail_bucket_owner_id} -i {iam_role_arn} -q 100 -l
```

### Required arguments
+ `falcon_client_id` - Falcon Client API key ID
+ `falcon_client_secret` - Falcon Client API key secret
+ `command` - Command to perform
    - Valid commands are register, update, check and delete

### Optionally required arguments
+ `external_id` - The external ID used for IAM Role assumption. When using the update or register command, this value is required.
+ `local_account` - The local account used for the CloudTrail logging bucket. When using the update or register command, this value is required.
+ `cloudtrail_bucket_region` - The AWS region for the bucket used for CloudTrail logging. When using the update or register command, this value is required.
+ `cloudtrail_bucket_owner_id` - The AWS IAM ID of the owner of the bucket used for CloudTrail logging. When using the update or register command, this value is required.
+ `iam_role_arn` - The IAM Role to assume when attempting to connect to the CloudTrail logging bucket. When using the update or register command, this value is required.

### Always optional arguments
+ `log_enabled` - When enabled, the accounts identified in the __check__ command are output to a JSON file. (_falcon_discover_accounts.json_) Has no impact on other commands.
+ `query_limit` - Limits the number of results returned when performing the __check__ command. Has no impact on other commands.
+ `help` - Provides limit help for arguments and script usage.

## Examples

#### Checking all accounts in your environment (and outputting the results to a file)
```bash
$ python3 fd_accounts.py -f CLIENT_ID -s CLIENT_SECRET -c check -l
```
##### Result
```json
Account 123456789012 has a problem: Assume role failed. IAM role arn and/or external is invalid.
Current settings {
    "id": "123456789012",
    "iam_role_arn": "arn:aws:iam::123456789012:role/FalconDiscover",
    "external_id": "IwXs93to8iHEkl0",
    "cloudtrail_bucket_owner_id": "123456789012",
    "cloudtrail_bucket_region": "eu-west-1"
}

Account 210987654321 has a problem: Assume role failed. IAM role arn and/or external is invalid.
Current settings {
    "id": "210987654321",
    "iam_role_arn": "arn:aws:iam::210987654321:role/FalconDiscover",
    "external_id": "J8duIpna56Lpe2",
    "cloudtrail_bucket_owner_id": "210987654321",
    "cloudtrail_bucket_region": "eu-west-1"
}

Account 987654321012 is ok!
```

#### Deleting an account
```bash
$ python3 falcon_discover_accounts.py -f CLIENT_ID -s CLIENT_SECRET -c delete -a 123456789012
```

##### Result
```bash
Successfully deleted account.
```

#### Registering an account
```bash
$ python3 fd_accounts.py -f CLIENT_ID -s CLIENT_SECRET -c register --external_id IwXs93to8iHEkl0 -a 123456789012 -r eu-west-1 -o 123456789012 -i arn:aws:iam::123456789012:role/FalconDiscover
```

##### Result
```bash
Successfully registered account.
```

#### Updating an account
```bash
$ python3 falcon_discover_accounts.py -f CLIENT_ID -s CLIENT_SECRET -c update --external_id IwXs93to8iHEkl0 -a 123456789012 -r eu-west-1 -o 123456789012 -i arn:aws:iam::123456789012:role/FalconDiscover
```

##### Result
```bash
Successfully updated account.
```
