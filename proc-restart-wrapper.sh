# PROCNAME
# HOSTNAME
OS=$(${JENKINS_HOME}/workspace/jenkins-scripts/determine-os.sh $HOSTNAME)
if [ "$OS" = "UBUNTU" ]; then
	USER="ubuntu"
else
	USER="root"
fi
ssh -T -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no $USER@$HOSTNAME "sudo -Eib env PROCNAME='$PROCNAME' HOSTNAME='$HOSTNAME' FORCEOP='$FORCEOP' bash -s --" < ${JENKINS_HOME}/workspace/jenkins-scripts/proc-restart.sh