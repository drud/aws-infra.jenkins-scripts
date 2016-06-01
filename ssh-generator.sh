# !/bin/bash
# HOSTNAME
# $1=SCRIPTNAME
# Usage
# SSH_CMD=$("./ssh-generator.sh SCRIPTNAME ENVOVERLOAD")
# eval "$SSH_CMD"
# STATUS=$?
# exit $STATUS
if [ -z "$1" -o -z "$2" ]; then
	echo "This script requires that you pass in a scriptname to run."
	echo "Usage: ./ssh-generator.sh SCRIPTNAME ENVOVERLOAD HOST OS"
	exit 1;
fi
SCRIPTNAME=$1
ENVOVERLOAD=$2
if [ -z "$3" ]; then
  HOST=$HOSTNAME
else
  HOST=$3
fi

if [ "$4" = "UBUNTU" -o "$4" = "CENTOS" ]; then
  OS=$4
else
  OS="`$JENKINS_SCRIPTS/determine-os.sh $HOST`"
fi

PROXY_CMD="`$JENKINS_SCRIPTS/determine-proxy.sh $HOST`"

if [ "$OS" = "UBUNTU" ]; then
	USER="ubuntu"
else
	USER="root"
fi

SSH_OPTIONS="-o StrictHostKeyChecking=no $PROXY_CMD -o NumberOfPasswordPrompts=0"
SSH_CMD="ssh -T -i /var/jenkins_home/.ssh/aws.pem $SSH_OPTIONS $USER@$HOST 'sudo -Eib $ENVOVERLOAD bash -s --' < $JENKINS_SCRIPTS/$SCRIPTNAME $OS"
echo $SSH_CMD
