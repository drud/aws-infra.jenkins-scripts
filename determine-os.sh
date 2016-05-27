#!/bin/bash
# Example Usage OS=$(./determine_os.sh HOSTNAME)
if [ -z $1 ]; then
	echo "Usage: determine-os.sh HOSTNAME"
	exit
fi
HOSTNAME=$1
# Try an SSH command to ubuntu first (faster that if root first)
PROXY_CMD=$($JENKINS_HOME/workspace/jenkins-scripts/determine-proxy.sh $HOSTNAME)
RETURN=$(ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -o NumberOfPasswordPrompts=0 $PROXY_CMD ubuntu@$HOSTNAME 'exit' &>/dev/null)
if [ $? -eq 0 ]; then
  echo "UBUNTU"
else
  echo "CENTOS"
fi