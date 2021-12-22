![CrowdStrike](https://raw.github.com/CrowdStrike/Cloud-AWS/main/docs/img/cs-logo.png)

[![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)](https://twitter.com/CrowdStrike)

# On-demand AWS S3 bucket scanner
This example provides a stand-alone solution for scanning a S3 bucket before implementing protection.
While similar to the serverless function, this solution will only scan the bucket's _existing_ file contents.

> This example requires the `boto3` and `crowdstrike-falconpy` (v0.8.7+) packages.

## Example output

```shell
PENDING
```

## Running the program
In order to run this solution, you will need a partial hostname for the target system and access to CrowdStrike API keys with the following scopes:
| Service Collection | Scope |
| :---- | :---- |
| Quick Scan | __READ__, __WRITE__ |
| Sample Uploads | __READ__, __WRITE__ |

### Execution syntax
The following command will execute the solution against the bucket you specify using default options.

```shell
python3 quickscan_target.py -k CROWDSTRIKE_API_KEY -s CROWDSTRIKE_API_SECRET -t s3://TARGET_BUCKET_NAME -r AWS_REGION
```

A small command-line syntax help utility is available using the `-h` flag.

```shell
√ on-demand % piprun quickscan_target.py -h
usage: Falcon Quick Scan [-h] [-l LOG_LEVEL] [-d CHECK_DELAY] [-b BATCH] -r REGION -t TARGET -k KEY -s SECRET

optional arguments:
  -h, --help            show this help message and exit
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        Default log level (DEBUG, WARN, INFO, ERROR)
  -d CHECK_DELAY, --check-delay CHECK_DELAY
                        Delay between checks for scan results
  -b BATCH, --batch BATCH
                        The number of files to include in a volume to scan.
  -r REGION, --region REGION
                        Region the target bucket resides in
  -t TARGET, --target TARGET
                        Target folder or bucket to scan. Bucket must have 's3://' prefix.
  -k KEY, --key KEY     CrowdStrike Falcon API KEY
  -s SECRET, --secret SECRET
                        CrowdStrike Falcon API SECRET
```
