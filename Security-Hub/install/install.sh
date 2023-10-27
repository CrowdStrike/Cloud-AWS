#!/bin/bash
# Falcon Ingestion Gateway installation utility
we_are_root=$(whoami)
if [[ "$we_are_root" == "root" ]]
then
        echo "Creating service user"
        groupadd fig
        adduser -g fig fig
    	echo "Installing pre-requisites"
        yum -y install python3 python3-pip
        sudo -u fig pip3 install --user crowdstrike-falconpy
        sudo -u fig pip3 install --user boto3
        echo "Setting permissions"
        chown -R fig:fig /usr/share/fig
        chmod 644 /usr/share/fig/*.py
        echo "Installing service"
        cp fig.service /lib/systemd/system
        systemctl daemon-reload
        systemctl enable fig
        systemctl start fig
        echo "Cleaning up"
        rm /usr/share/fig/fig.service
        rm /usr/share/fig/install.sh
        rm /usr/share/fig/README.md
        echo "Installation complete"
else
    	echo "This script must be executed as root. Perhaps try sudo?"
fi
