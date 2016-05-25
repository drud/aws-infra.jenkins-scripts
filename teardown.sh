#!/bin/bash -x

MAX_TESTS=20
SLEEP_AMOUNT=10

SECURITYGROUPS=$(echo $SECURITYGROUPS | sed 's/ .*//')
IMAGE=$(echo $IMAGE | sed 's/ .*//')
INSTANCE_TYPE=$(echo $INSTANCE_TYPE | sed 's/ .*//')
NEWROLE=$(echo $NEWROLE | sed 's/ .*//')
SECURITYGROUPS=$(echo $SECURITYGROUPS | sed 's/ .*//')
SUBNET=$(echo $SUBNET | sed 's/ .*//')
TARGETENVIRONMENT=$(echo $TARGETENVIRONMENT | sed 's/ .*//')
INSTANCE=$(<$WORKSPACE/INSTANCE)

rm -rf archive
mkdir -p archive/var

DESCRIPTION=$(ec2-api-tools/bin/ec2-describe-instances $INSTANCE --filter "image-id=$IMAGE" --filter "instance.group-id=$SECURITYGROUPS" --filter "instance-type=$INSTANCE_TYPE")
export INSTANCE=$(echo "$DESCRIPTION" | sed -n '2p' | awk '{print $2}')
PRIVATEIP=$(echo "$DESCRIPTION" | sed -n -e '/^PRIVATEIPADDRESS/p' | awk '{print $2}')

if [[ -z "$DESCRIPTION" ]]; then
  echo "Could not get an instance id."
  exit 1
fi

ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP 'setenforce 0'
rsync -avz -e "ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no" root@$PRIVATEIP:/var/log archive/var/
rsync -avz --exclude '/etc/shadow' --exclude '/etc/gshadow' --exclude '/etc/shadow-' -e "ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no" root@$PRIVATEIP:/etc archive/

ec2-api-tools/bin/ec2-terminate-instances $INSTANCE
rm -f $WORKSPACE/INSTANCE archive/
echo $DESCRIPTION > archive/INSTANCE
