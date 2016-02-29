#!/bin/bash
# HOSTNAME must be set in the env
# Example Usage OS=$(./determine_os.sh)
# Try an SSH command to ubuntu first (faster that if root first)
PROXY_CMD=$(${JENKINS_HOME}/workspace/jenkins-scripts/determine-proxy.sh)
RETURN=$(ssh -q -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -o NumberOfPasswordPrompts=0 $PROXY_CMD ubuntu@$HOSTNAME 'exit' 2>/dev/null)
if [ $? -eq 0 ]; then
  echo "UBUNTU"
else
  echo "CENTOS"
fi