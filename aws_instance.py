# Spin up new gluster instance WITHOUT a brick
# Move the brick from old machine to new machine
# Deprecate old machine

# Spin up the new gluster instance without a brick

# Start by taking a snapshot of the currently running machine
# Create a new instance from the snapshot
# TAG the instance with the correct tags
# Run the Jenkins gluster production playbook

# Move a gluster brick

# Killall glusterd procs on the machine in question
# Unmount the brick
# Detach the volume from the old instance
# Attach the volume to the new instance
# Start glusterd
# Replacebrick old new

#!/usr/bin/python

import boto3
from pprint import pprint as p
import subprocess

def create_instance_like(instance_id='i-318ca4c6', image_type="gluster", new_instance_name='gluster0test.nmdev.us'):
  # Connect to EC2
  ec2 = boto3.resource('ec2')

  # Get existing box's metadata
  instance_to_replace = ec2.Instance(instance_id)
  security_group_ids = [x['GroupId'] for x in instance_to_replace.security_groups]
  old_block_device_mapping = instance_to_replace.block_device_mappings
  vol_id = old_block_device_mapping[0]['Ebs']['VolumeId']
  old_primary_volume = ec2.Volume(vol_id)

  # "Upgrade" to the newest generation of servers
  if instance_to_replace.instance_type.startswith('m1'):
    new_instance_type = instance_to_replace.instance_type.replace('m1', 'm3')
  else:
    new_instance_type = instance_to_replace.instance_type

  # Connect to EC2
  ec2 = boto3.client('ec2')

  # Get a list of all images that are close to the name passed in, made by us
  possible_images = ec2.describe_images(Owners=['503809752978'], Filters=[{'Name': 'name', 'Values': ["*{image_type}*".format(image_type=image_type)]}])
  # Sort the images by creation date
  sorted_images = sorted(possible_images['Images'], key=lambda k: k['CreationDate'])
  # Select the last image in the list
  most_recent_image = sorted_images[-1]

  ec2 = boto3.resource('ec2')
  # Create a new instance based on the AMI we just found
  instances = ec2.create_instances(ImageId=most_recent_image['ImageId'],
    MinCount=1,
    MaxCount=1,
    KeyName=instance_to_replace.key_pair.key_name,
    SecurityGroupIds=security_group_ids,
    InstanceType=new_instance_type,
    Placement=instance_to_replace.placement,
    BlockDeviceMappings=[{
      'DeviceName': "/dev/sda1",
      'Ebs': {
        'VolumeSize': old_primary_volume.size,
        'DeleteOnTermination': old_primary_volume.attachments[0]['DeleteOnTermination'],
        'VolumeType': old_primary_volume.volume_type
      }
    }],
    SubnetId=instance_to_replace.subnet_id)
    
  new_instance = instances[0]
  # Get the tags figured out for the new instance
  tags = instance_to_replace.tags
  for tag in tags:
    for i, (tag, val) in enumerate(tag.items()):
      if val == "Name":
        tags[i-1]["Value"] = new_instance_name
        break

  # To Tag the instance
  # Ensure the instance is "running"
  new_instance.wait_until_running()
  # Tag the instance with CreateTags()
  new_instance.create_tags(Tags=tags)

  hosted_zone_id="Z2WYJTE6C15CN4" if "nmdev.us" in new_instance_name else "ZS8SECWEXOKXH"

  # Create the corresponding DNS entry for this server
  boto3.client('route53').change_resource_record_sets(
    HostedZoneId=hosted_zone_id,
    ChangeBatch={
      Changes: [{
        'Action': 'UPSERT',
        'ResourceRecordSet': {
          'Name': new_instance_name,
          'Type': 'A',
        },
        'ResourceRecords': [{'Value': new_instance.private_ip_address}]
      }]
    }
  )


def move_volume(volume_id, old_instance_id, new_instance_id, fstab_entry):
  print "Moving {vol} - detaching from {old} and attaching to {new}".format(vol=volume_id, old=old_instance_id, new=new_instance_id)
  user="user"
  host="host"
  # ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no {{ USERNAME }}@{{ HOST }}
  ssh_cmd = ['ssh', '-p22', '-i', '/var/jenkins_home/.ssh/aws.pem', '-o', 'StrictHostKeyChecking=no', "{user}@{host}".format(user=user,host=host)]
  # SSH into the old instance and umount the volume.
  umount_cmd = ssh_cmd + ['"umount', '/dev/sda1"']
  # SSH into the old instance and delete the fstab entry.

  # Connect to EC2
  ec2 = boto3.resource('ec2')
  # Get the volume we're moving
  vol = ec2.Volume(volume_id)
  
  # Detach it
  old_info = vol.detach_from_instance(InstanceId=old_instance_id)
  
  # Attach it to the new instance
  vol.attach_to_instance(InstanceId=new_instance_id, Device=old_info['Device'])
  
  # SSH into the new instance and create an fstab entry
  # SSH into the new instance and mount the brick

  # If gluster
  # SSH into ANOTHER gluster instance, and from it, run a replace-brick and a peer-disconnect

# instance.detech_volume(VolumeId="")
if __name__ == '__main__':
  fstab_entry = {
    "file_system":"/dev/sda1",
    "dir":"/mnt",
    "type":"ext4",
    "options":"defaults",
    "dump":"0",
    "pass":"1"
  }
  user=tags['DeployUser']
  host=tags['Name']
  
  #ssh_exec_cmd = ['"umount', '{dev}'.format(dev=)]
  #print subprocess.check_output(ssh_cmd)