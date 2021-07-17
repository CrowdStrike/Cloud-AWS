# Deployment automation
The [makeself](https://makeself.io/) project was leveraged to build this installer.

> This process has been automated via the build.sh script.

## Package contents
+ `main.py` - Main routine
+ `stream.py` - Stream handling
+ `logger.py` - Logging functionality
+ `api_complete.py` - Falcon Complete API SDK uber class
+ `credvault.py` - SSM credential handling
+ `fig.service` - Systemd service definition (**_Removed as part of installation_**)
+ `install.sh` - Executed post decompression, installation script that installs pre-requisites and cleans up. (**_Removed as part of installation_**)

## Execution
This installer must be executed as the root user (usually via _sudo_, userdata scripts already execute as root).
> If you do not specify the target directory exactly as listed below, this installation will fail

```bash
$ ./fig-2.0.12-install.run --target /usr/share/fig
```

