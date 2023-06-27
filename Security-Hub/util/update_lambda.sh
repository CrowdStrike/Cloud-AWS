#!/bin/bash

TARGET="sechub-identify-detections_lambda.zip"

# Remove existing zip file from cs-fig-identify-detection and install directories
[ -f ../install/$TARGET ] && rm ../install/$TARGET
[ -f ../cs-fig-identify-detection/$TARGET ] && rm ../cs-fig-identify-detection/$TARGET

# Create zip file in cs-fig-identify-detection directory
cd ../cs-fig-identify-detection
zip -r $TARGET ./*

# Copy zip file to install directory
cp $TARGET ../install/$TARGET

echo "Update completed."
