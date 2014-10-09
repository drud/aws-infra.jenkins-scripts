#!/bin/bash -ex

export CHEF_VALIDATION_KEY=/var/jenkins_home/.chef/chef_validationkey.pem
export CHEF_VALIDATION_CLIENT_NAME=newmediadenver-validator
export CHEF_CLIENT_KEY=/var/jenkins_home/.chef/chef_clientkey.pem
export CHEF_NODE_NAME=jenkins_ac
export CHEF_SERVER_URL=https://api.opscode.com/organizations/newmediadenver
export AWS_ACCESS_KEY='AKIAJXWDNYTONJLIGLYQ'
export AWS_SECRET_KEY='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'
export EC2_HOME='/var/jenkins_home/workspace/jenkins-scripts/ec2-api-tools'
export JAVA_HOME='/usr/lib/jvm/java-7-openjdk-amd64'
export EC2_URL='https://ec2.us-west-2.amazonaws.com'
export EC2_REGION='us-west-2'
export KEYNAME=cyberswat
env
# This will validate everything is connected.
ec2-api-tools/bin/ec2-describe-regions
INSTANCE=$(ec2-api-tools/bin/ec2-run-instances $IMAGE --subnet $SUBNET --key $KEYNAME --group $SECURITYGROUPS --instance-type $INSTANCE_TYPE --block-device-mapping "/dev/sda=:${DISKSIZE}:true:gp2" | sed -n '2p' | awk '{print $2}')
if [ -z "$INSTANCE" ]; then
  echo "Could not get an instance id."
  exit 1
fi

ec2-api-tools/bin/ec2-describe-instances ${INSTANCE}

echo "[$(date)] Waiting for running state ..."
STATE=''
while [ "$STATE" != 'running' ]
do
  DESCRIPTION=$(ec2-api-tools/bin/ec2-describe-instances ${INSTANCE})
  PRIVATEIP=$(echo "$DESCRIPTION" | awk '{printf $15}')
  STATE_RAW=$(echo "$DESCRIPTION" | awk '{print $5}' | head -2)
  STATE=$(echo $STATE_RAW | sed 's/^\s*//')
  echo "[$(date)] $STATE"
  x=$(( $x + 1 ))
done

echo "[$(date)] Waiting for ping ..."
while ! ping -c1 $PRIVATEIP &>/dev/null; do :; done
echo "[$(date)] $INSTANCE is $STATE on $PRIVATEIP"
sleep 30
echo "[$(date)] $INSTANCE resizing disk."
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP "resize2fs /dev/xvde"
echo "[$(date)] $INSTANCE update /etc/sysconfig/network"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP "sed -i 's/localhost.localdomain/${NEWHOSTNAME}/' /etc/sysconfig/network && cat /etc/sysconfig/network"
echo "[$(date)] $INSTANCE update /etc/sysconfig/clock"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP sed -i 's#ZONE=\"UTC\"#ZONE=\"America/Denver\"#' /etc/sysconfig/clock
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP "sed -i 's#UTC=True#UTC=False#' /etc/sysconfig/clock && ln -sf /usr/share/zoneinfo/America/Denver /etc/localtime && cat /etc/sysconfig/clock"
echo "[$(date)] $INSTANCE create /etc/chef/encrypted_data_bag_secret"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'mkdir -p /etc/chef'
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'echo "0o4LcdbuNZmATnMoXeZDdZmgkCO9YiHsHsyNNtiMgJ94eSimiL74HuXWdGKXeVVGypEvaxy/JpmXdwydICDHH9qsIWbfgH0hTMqImU/2EBm8Bn4q8tlJ4WyxNl1cFtsG+vicyv6dQB5B9rlltECj+cvCIf0pjakqwVswMchm4iWqhipGVceyMQ8b7f8zIAwfQTCbfOxhQoAp5Gd89e5pT+qR2KpREtyDXSZflGsxd6MipTw+nj3WFrUfNrGh0wIBfM1r8q7x3uMRF6DgofwrYgNUuaAHh0Ky8SFrRTyYlLY37pS4QPI5kRjVI94jlK6SRkRxoHrVENiLYEswhLydAY8xg9u+kIpyqpg0fHakkqMb0FTIqpuuf4jG6VgzyPZg51Q6ZfRnQolnutk0Kth67riQAPAp+sRnxIFCDkbB5A696/GVdqBdWDzMeXVN1bWhF7lSxhzlHYVLzRIF1S6pLGduEjKRJFdxpFoYS31kGxwUoAPEACT/6QxGCvfTGo0wgMY+2e1QR2EZobqKlTqcNVpTNlaDP40wPtLf+Y+Rx62IDAp491plnYbOZH9kR3wdCqw/EVFipvvrXQ8BV0BbfRKn7RYDmaTlGZ6Xjfv1Pwnr2THZpHj+DbeOAU1W4ednjHlJhCqyt+Z4TZfY1pUOhECAnGQh5pddft6rydB+8mE=" > /etc/chef/encrypted_data_bag_secret'
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'cat /etc/chef/encrypted_data_bag_secret'
echo "[$(date)] $INSTANCE update /etc/hosts"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'sed -i "2i/${PRIVATEIP} ${NEWHOSTNAME} ${NEWHOST}/" /etc/hosts'
echo "[$(date)] $INSTANCE yum update"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'yum update -y && reboot'
echo "[$(date)] $INSTANCE rebooting."
echo "[$(date)] Waiting for running state ..."
STATE=''
while [ "$STATE" != 'running' ]
do
  DESCRIPTION=$(ec2-api-tools/bin/ec2-describe-instances ${INSTANCE})
  PRIVATEIP=$(echo "$DESCRIPTION" | awk '{printf $15}')
  STATE_RAW=$(echo "$DESCRIPTION" | awk '{print $5}' | head -2)
  STATE=$(echo $STATE_RAW | sed 's/^\s*//')
  echo "[$(date)] $STATE"
  x=$(( $x + 1 ))
done
echo "[$(date)] Waiting for ping ..."
while ! ping -c1 $PRIVATEIP &>/dev/null; do :; done
sleep 30
echo "[$(date)] $INSTANCE ssh availability check"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'hostname && date'
echo "[$(date)] delete node from chef if it exists"
knife node $NEWHOSTNAME delete -y
echo "[$(date)] delete client from chef if it exists"
knife client $NEWHOSTNAME delete -y
echo "[$(date)] bootstrap the instance"
knife bootstrap $PRIVATEIP -u root -N $NEWHOSTNAME -E $TARGETENVIRONMENT -i /var/jenkins_home/.ssh/aws.pem --no-host-key-verify
echo "[$(date)] $INSTANCE update /etc/chef/client.rb"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'echo "ssl_verify_mode :verify_peer" >> /etc/chef/client.rb'
echo "[$(date)] chef-client"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'chef-client'
