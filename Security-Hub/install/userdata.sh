#!/bin/bash
# version 3.0
# This is the userdata script for newly created EC2 instances. 
# This script should not be executed manually
cd /var/tmp
wget -O ${FigFileName} https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Security-Hub/install/${FigFileName}
chmod 755 ${FigFileName}
./${FigFileName} --target /usr/share/fig