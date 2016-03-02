# !/bin/bash
# HOSTNAME
# $1=SCRIPTNAME
if [ -z "$1" -o -z "$2" ]; then
	echo "This script requires that you pass in a scriptname to run."
	echo "Usage: ./ssh-generator.sh SCRIPTNAME ENVOVERLOAD"
	exit 1;
fi
SCRIPTNAME=$1
ENVOVERLOAD=$2
PROXY_CMD="`$JENKINS_HOME/workspace/jenkins-scripts/determine-proxy.sh $HOSTNAME`"
OS="`$JENKINS_HOME/workspace/jenkins-scripts/determine-os.sh $HOSTNAME`"
if [ "$OS" = "UBUNTU" ]; then
	USER="ubuntu"
else
	USER="root"
fi
SSH_OPTIONS="-o StrictHostKeyChecking=no $PROXY_CMD -o NumberOfPasswordPrompts=0"
SSH_CMD="ssh -T -i /var/jenkins_home/.ssh/aws.pem $SSH_OPTIONS $USER@$HOSTNAME 'sudo -Eib $ENVOVERLOAD bash -s --' < $JENKINS_HOME/workspace/jenkins-scripts/$SCRIPTNAME $OS"
echo $SSH_CMD
