## Solution testing / debugging utilities

Random pieces of detritus used to put this solution together.

### build.sh

Build automation script that leverages [makeself](https://makeself.io/) to generate a distribution installer.

```bash
./build.sh
```

The build folder is used as a temporary working folder.

The compressed installer is saved to the install folder.

### update_lambda.sh

This script is used to update the `sechub-identify-detections_lamda.zip` zip file.

> *Use this script after making changes to the lambda function code.*

```bash
./update_lambda.sh
```
