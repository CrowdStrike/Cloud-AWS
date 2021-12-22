#!/bin/sh
figlet -w 220 -f cricket Findings
echo -e "Findings in $(echo ${BUCKET/s3:\/\//}) for the past hour:\n"
st=$(date -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')
en=$(date -d 'now' '+%Y-%m-%dT%H:%M:%SZ')
FILTER='{"ResourceId":[{"Value":"'$(echo ${BUCKET/s3:\/\//})'","Comparison":"PREFIX"}]'
FILTER="$FILTER,\"CreatedAt\":[{\"Start\":\"$st\",\"End\":\"$en\"}]}"
REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq .region -r)
aws securityhub get-findings --region=$REGION \
    --filters $FILTER \
    --sort-criteria '{"Field": "LastObservedAt","SortOrder": "desc"}' \
    --page-size 5 --max-items 100 --output json \
    | jq --raw-output '.Findings[] | "\(.Title)\n\(.Description)"'
