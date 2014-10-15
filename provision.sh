#!/bin/bash -x

env

wait_state_running ()
{
echo "[$(date)] Waiting for running state ..."
MAX_TESTS=20
SLEEP_AMOUNT=10
OVER=0
TESTS=0
while [[ $OVER != 1 ]] && [[ $TESTS -le $MAX_TESTS ]]; do
  DESCRIPTION=$(ec2-api-tools/bin/ec2-describe-instances ${INSTANCE})
  PRIVATEIP=$(echo "$DESCRIPTION" | awk '{printf $15}')
  STATE_RAW=$(echo "$DESCRIPTION" | awk '{print $5}' | head -2)
  STATE=$(echo $STATE_RAW | sed 's/^\s*//')

  if [[ "$STATE" == ip-* ]]; then
    STATE_RAW=$(echo "$DESCRIPTION" | awk '{print $6}' | head -2)
    STATE=$(echo $STATE_RAW | sed 's/^\s*//')
  fi

  echo "[$(date)] $STATE"
  if [[ "$STATE" != "running" ]]; then
    OVER=0
    TESTS=$(echo $(( TESTS+=1 )))
    sleep $SLEEP_AMOUNT
  else
    OVER=1
  fi
done
}

wait_ping ()
{
echo "[$(date)] Waiting for ping ..."
MAX_TESTS=20
SLEEP_AMOUNT=10
OVER=0
TESTS=0
while [[ $OVER != 1  ]] && [[ $TESTS -le $MAX_TESTS ]]; do
  ping -c1 $PRIVATEIP
  if [[ $? == 0 ]]; then
    OVER=1
  else
    TESTS=$(echo $(( TESTS+=1 )))
    sleep $SLEEP_AMOUNT
  fi
done
}

wait_ssh ()
{
MAX_TESTS=20
SLEEP_AMOUNT=10
OVER=0
TESTS=0
echo "[$(date)] Waiting for ssh ..."
while [[ $OVER != 1 ]] && [[ $TESTS -le $MAX_TESTS ]]; do
    ssh -q -o StrictHostKeyChecking=no -i /var/jenkins_home/.ssh/aws.pem root@$PRIVATEIP exit
    if [[ $? != 255 ]]; then
        OVER=1
    else
        TESTS=$(echo $(( TESTS+=1 )))
        sleep $SLEEP_AMOUNT
    fi
done
}

SECURITYGROUPS=$(echo $SECURITYGROUPS | sed 's/ .*//')
IMAGE=$(echo $IMAGE | sed 's/ .*//')
INSTANCE_TYPE=$(echo $INSTANCE_TYPE | sed 's/ .*//')
NEWROLE=$(echo $NEWROLE | sed 's/ .*//')
SECURITYGROUPS=$(echo $SECURITYGROUPS | sed 's/ .*//')
SUBNET=$(echo $SUBNET | sed 's/ .*//')
TARGETENVIRONMENT=$(echo $TARGETENVIRONMENT | sed 's/ .*//')

# This will validate everything is connected.
ec2-api-tools/bin/ec2-describe-regions

export INSTANCE=$(ec2-api-tools/bin/ec2-run-instances $IMAGE --subnet $SUBNET --key $KEYNAME --group $SECURITYGROUPS --instance-type $INSTANCE_TYPE --block-device-mapping "/dev/sda=:${DISKSIZE}:true:gp2" | sed -n '2p' | awk '{print $2}')
if [[ -z "$INSTANCE" ]]; then
  echo "Could not get an instance id."
  exit 1
fi
echo $INSTANCE > /var/jenkins_home/workspace/provision-teardown/INSTANCE

ec2-api-tools/bin/ec2-describe-instances ${INSTANCE}

wait_state_running
wait_ping
wait_ssh

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

wait_state_running
wait_ping
wait_ssh

echo "[$(date)] delete node from chef if it exists"
knife node $NEWHOSTNAME delete -y
echo "[$(date)] delete client from chef if it exists"
knife client $NEWHOSTNAME delete -y
echo "[$(date)] bootstrap the instance"
knife bootstrap $PRIVATEIP -u root -N $NEWHOSTNAME -E $TARGETENVIRONMENT -i /var/jenkins_home/.ssh/aws.pem --no-host-key-verify
echo "[$(date)] $INSTANCE update /etc/chef/client.rb"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'echo "ssl_verify_mode :verify_peer" >> /etc/chef/client.rb'
echo "[$(date)] $INSTANCE apply role."
knife node run_list add $NEWHOSTNAME "role[$NEWROLE]"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -t -t root@$PRIVATEIP 'chef-client -l debug'
