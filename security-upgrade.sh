#!/bin/bash
#HOSTNAME="monitor01.nmdev.us"
#USER=""

#Retain whitespace in variables
IFS='%'
# We override this string only if the package isn't installed.
INSTALL_CMD=""
echo $JENKINS_HOME
PROXY_CMD="$($JENKINS_HOME/workspace/jenkins-scripts/determine-proxy.sh $HOSTNAME)"
echo $PROXY_CMD
# Try an SSH command to ubuntu first (faster that if root first)
RETURN=$(ssh -q -i /var/jenkins_home/.ssh/aws.pem $PROXY_CMD -o StrictHostKeyChecking=no -o NumberOfPasswordPrompts=0 ubuntu@$HOSTNAME 'exit')
if [ $? -eq 0 ]; then
  echo "This is an ubuntu machine."
  USER="ubuntu"
  UP_CMD="sudo -i
  unattended-upgrade -v"
  INSTALL_CMD="sudo -i
    typeset -f | if ! apt_package_exists unattended-upgrade ; then
	  apt-get -y update &&
	  echo unattended-upgrades unattended-upgrades/enable_auto_updates boolean true | debconf-set-selections &&
	  apt-get -y install unattended-upgrades &&
	  dpkg-reconfigure -f noninteractive unattended-upgrades;
	fi"
	INSTALL_FUNCTION="function apt_package_exists() {
	return dpkg -l "\$1" &> /dev/null
}"
else
	echo "We *think* this is a CentOS box."
  USER="root"
  UP_CMD="yum update -y --security;"
  INSTALL_CMD="typeset -f | if ! yum_package_exists yum-plugin-security ; then
    yum install -y yum-plugin-security
	fi"
		INSTALL_FUNCTION="function yum_package_exists() {
  if yum list installed "\$1" &>/dev/null; then
    true
  else
    false
  fi
}"
fi
ssh -T -i /var/jenkins_home/.ssh/aws.pem $PROXY_CMD -o StrictHostKeyChecking=no -o NumberOfPasswordPrompts=0 $USER@$HOSTNAME<<EOF
  $(echo $INSTALL_FUNCTION)
  $(echo $INSTALL_CMD)
  $(echo $UP_CMD)
  echo "The previous commands ran on $( uname -a )"
  exit
EOF
STATUS=$?
unset IFS
exit $STATUS