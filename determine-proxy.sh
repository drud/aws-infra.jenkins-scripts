#!/bin/bash
if [ -z $1 ]; then
	echo "Usage: determine-proxy.sh HOSTNAME"
	exit
fi
HOSTNAME=$1
# Get proxy option flag if necessary
if [[ $HOSTNAME == *"overlaybastion"* ]]; then
	# Bastion - just go straight to bastion for the fun
	PROXY_CMD=""
elif [[ $HOSTNAME == *"overlay"* ]]; then
	# Overlay server - we have to tunnel
	# overlayweb01.nmdev.us
	PROXY_CMD="-o ProxyCommand='ssh -v -i /var/jenkins_home/.ssh/aws.pem ubuntu@overlaybastion2.nmdev.us nc $HOSTNAME 22'"
else
	# Normal server
	PROXY_CMD=""
fi
echo $PROXY_CMD