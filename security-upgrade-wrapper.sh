#Retain whitespace in variables
IFS='%'
# SCRIPTNAME, HOSTNAME, ENVOVERLOAD
ENVOVERLOAD=""
SCRIPTNAME="security-upgrade-remote.sh"
# We override this string only if the package isn't installed.
INSTALL_CMD=""
PROXY_CMD=$($JENKINS_HOME/workspace/jenkins-scripts/determine-proxy.sh $HOSTNAME)
OS=$($JENKINS_HOME/workspace/jenkins-scripts/determine-os.sh $HOSTNAME)
if [ $OS = "UBUNTU" ]; then
	$USER="ubuntu"
else
	$USER="root"
fi
SSH_CMD=$($JENKINS_HOME/workspace/jenkins-scripts/ssh-generator.sh $SCRIPTNAME $ENVOVERLOAD)
echo "Here is the SSH CMD: $SSH_CMD"
eval "$SSH_CMD"
