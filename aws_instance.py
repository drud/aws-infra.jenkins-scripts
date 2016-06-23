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
import remote_fstab
import time

def create_instance_like(instance_id, image_type, new_instance_name='tester'):
  """
  instance_id The instance to be mimicked
  image_type A basic search string that partially matches an AMI label
  new_instance_name The FQDN of the new instance e.g. gluster01.nmdev.us
  """
  # Connect to EC2
  ec2 = boto3.resource('ec2', region_name='us-west-2')

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
  ec2 = boto3.client('ec2', region_name='us-west-2')

  # Get a list of all images that are close to the name passed in, made by us
  possible_images = ec2.describe_images(Owners=['503809752978'], Filters=[{'Name': 'name', 'Values': ["*{image_type}*".format(image_type=image_type)]}])
  # Sort the images by creation date
  sorted_images = sorted(possible_images['Images'], key=lambda k: k['CreationDate'])
  # Select the last image in the list
  most_recent_image = sorted_images[-1]

  ec2 = boto3.resource('ec2', region_name='us-west-2')
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

  # Determine the hosted zone ID by the instance ID
  hosted_zone_id = "Z2WYJTE6C15CN4" if "nmdev.us" in new_instance_name else "ZS8SECWEXOKXH"

  print "A {name}->{ip} in {dns_id}".format(name=new_instance_name, ip=new_instance.private_ip_address, dns_id=hosted_zone_id)
  # Create the corresponding DNS entry for this server
  boto3.client('route53').change_resource_record_sets(
    HostedZoneId=hosted_zone_id,
    ChangeBatch={
      'Changes': [{
        'Action': 'UPSERT',
        'ResourceRecordSet': {
          'Name': new_instance_name,
          'Type': 'A',
          'TTL': 300,
          'ResourceRecords': [{'Value': new_instance.private_ip_address}]
        },
      }]
    }
  )
  return new_instance


def move_volume(volume_id, old_instance_id, new_instance_id, device_name):
  print "Moving {vol} - detaching from {old} and attaching to {new}".format(vol=volume_id, old=old_instance_id, new=new_instance_id)

  # Setup the SSH commands
  ssh_cmd = "ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no {user}@{host}"
  umount_cmd = ssh_cmd + " sudo umount {device}"
  mmkdir_cmd = ssh_cmd + " sudo mkdir -p {folder}"
  mount_cmd = ssh_cmd + " sudo mount {device}"
  #boto3.client('ec2').describe_tags(Filters=[{"Name":"resource-id","Values":["i-318ca4c6"]}, {"Name":"key","Values":["Environment"]}])['Tags'][0]['Value']
  old_host = boto3.client('ec2', region_name='us-west-2').describe_tags(Filters=[{"Name":"resource-id","Values":[old_instance_id]}, {"Name":"key","Values":["Name"]}])['Tags'][0]['Value']
  old_user = boto3.client('ec2', region_name='us-west-2').describe_tags(Filters=[{"Name":"resource-id","Values":[old_instance_id]}, {"Name":"key","Values":["DeployUser"]}])['Tags']
  old_user = "root" if len(old_user)<1 else old_user[0]['Value']
  old_user = "root" if old_user == "" else old_user
  new_host = boto3.client('ec2', region_name='us-west-2').describe_tags(Filters=[{"Name":"resource-id","Values":[new_instance_id]}, {"Name":"key","Values":["Name"]}])['Tags'][0]['Value']
  new_user = boto3.client('ec2', region_name='us-west-2').describe_tags(Filters=[{"Name":"resource-id","Values":[new_instance_id]}, {"Name":"key","Values":["DeployUser"]}])['Tags']
  new_user = "root" if len(new_user)<1 else new_user[0]['Value']

  print "Moving {device} from {ouser}@{ohost} to {nuser}@{nhost}".format(device=device_name,ouser=old_user,ohost=old_host,nuser=new_user,nhost=new_host)

  try:
    # SSH into the old instance and umount the volume.
    ret = subprocess.check_output(umount_cmd.format(user=old_user,host=old_host,device=device_name).split(" "), stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    print e
    print e.output
    print e.returncode 
    # If the volume wasn't mounted
    if "not mounted" in e.output:
      print "The volume wasn't mounted. Continuing..."
    else:
      exit(e.output)

  # SSH into the old instance and delete the fstab entry.
  fstab_entry, fstab_entry_line = remote_fstab.find_and_remove_fstab_entry(old_user, old_host, device_name)

  # Connect to EC2
  ec2 = boto3.resource('ec2', region_name='us-west-2')
  # Get the volume we're moving
  vol = ec2.Volume(volume_id)
  
  # Detach it
  old_info = vol.detach_from_instance(InstanceId=old_instance_id)
  aws_device_name = old_info['Device']

  while vol.state != "available":
    print "Current volume state it {state}. Waiting for available state.".format(state=vol.state)
    time.sleep(5)
    vol.reload()
  
  # Attach it to the new instance
  vol.attach_to_instance(InstanceId=new_instance_id, Device=old_info['Device'])
  
  # SSH into the new instance and create an fstab entry
  remote_fstab.append_fstab_entry(new_user, new_host, fstab_entry_line)


  # SSH into the new instance and mkdir -p the directory
  subprocess.check_output(mkdir_cmd.format(user=new_user, host=new_host, folder=fstab_entry[1]).split(" "))
  
  # SSH into the new instance and mount it
  subprocess.check_output(mount_cmd.format(user=new_user, host=new_host, device=device_name).split(" "))

  # TODO If gluster
  # SSH into ANOTHER gluster instance, and from it, run a replace-brick and a peer-disconnect

# instance.detech_volume(VolumeId="")
if __name__ == '__main__':
  #ssh_exec_cmd = ['"umount', '{dev}'.format(dev=)]
  #print subprocess.check_output(ssh_cmd)

  # instance_id = 'i-318ca4c6' # gluster01.nmdev.us
  # image_type = "gluster"
  # old_host = "gluster01.nmdev.us"
  # new_host = 'gluster0test.nmdev.us'
  # new_instance_name = new_host
  # user="root" if "nmdev.us" in host else "ubuntu"
  
  #create_instance_like(instance_id='i-318ca4c6', image_type="gluster", new_instance_name='gluster03.nmdev.us')
  #create_instance_like(instance_id='i-318ca4c6', image_type="gluster", new_instance_name='gluster04.nmdev.us')
  # gluster03.nmdev.us->10.0.3.153 in Z2WYJTE6C15CN4
  # ec2.Instance(id='i-45854cea')
  # gluster04.nmdev.us->10.0.3.27 in Z2WYJTE6C15CN4
  # ec2.Instance(id='i-52854cfd')
  move_volume(volume_id='vol-bf658d36', old_instance_id='i-45854cea', new_instance_id='i-52854cfd', device_name='/dev/xvdf')