#!/bin/bash
# Build a new agent-handler.zip layer archive for upload / use within the CFT
# Tested on Darwin
#
if [ -z "$1" ]
then
  echo "Usage: build-helper.sh [BUCKET_NAME]"
else
  rm agent-helper.zip
  curl -o falconpy-layer.zip https://falconpy.io/downloads/falconpy-layer.zip
  unzip falconpy-layer
  cp ../cs_install_automation.py python/.
  cd python
  zip -r ../agent-handler *
  cd ..
  rm -fR python
  rm falconpy-layer.zip
  HASH=$(openssl dgst -sha256 agent-handler.zip | cut -f 2 -d ' ')
  aws s3 cp agent-handler.zip s3://$1/script/
  echo "Build / Upload complete. New file hash: $HASH"  
fi