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
import botocore
from pprint import pprint as p
import subprocess
import remote_fstab
import time
import click
import gluster

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

def get_instance_by_tagged_name(server_name):
    # Theoretically something like this should work
    # ec2 = boto3.resource('ec2')
    # instances = ec2.instances.filter(Filters=[{'Name': 'Name', 'Values': ['running']}])
    # print instances
    # for instance in instances:
    #     print(instance.id, instance.instance_type)
    instance_id = ""
    instance_dict = None
    instance = None
    ec2_connection = boto3.client('ec2', region_name='us-west-2')
    ec2_instances = ec2_connection.describe_instances()["Reservations"]
    for instance in ec2_instances:
      for x in instance["Instances"]:
        if "Tags" in x:
          tags = {y["Key"]:y["Value"] for y in x["Tags"]}
          instance_name = tags["Name"]
          if server_name == instance_name and boto3.resource('ec2', region_name='us-west-2').Instance(x["InstanceId"]).state["Name"] != "terminated":
              instance_id = x["InstanceId"]
              instance_dict = x
              print "Found server instance ID of '{instance_id}' for server named '{server_name}'".format(instance_id=instance_id, server_name=server_name)
              return instance_id, instance_dict

    if instance_id == "":
        print "A server with name '{server_name}' could not be mapped to an instance id.".format(server_name=server_name)
        return None, None

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def siteman():
    pass

@siteman.command()
@click.option('--host-to-mimic', prompt='Hostname of instance to mimic', help='Hostname of instance to mimic e.g. gluster05.newmediadenver.com')
@click.option('--image-type', prompt='AMI search string', help='A basic search string that partially matches an AMI label', type=click.Choice(['gluster', 'proxy', 'percona', 'web']))
@click.option('--new-instance-name', prompt='New instance name', help='The FQDN of the new instance e.g. gluster01.nmdev.us')
@click.option('--debug', is_flag=True)
def create_instance_like(host_to_mimic, image_type, new_instance_name, debug):
  create_instance_like_fnc(host_to_mimic, image_type, new_instance_name, recreate_all_volumes=True, debug=debug)

def create_instance_like_fnc(host_to_mimic, image_type, new_instance_name, recreate_all_volumes=True, debug=False):
  """
  Creates an instance with the same settings as the instance ID specified and provisions the machine with the most recent pre-built AMI specified in the search string.
  """
  # Connect to EC2
  ec2 = boto3.resource('ec2', region_name='us-west-2')
  
  # Sanity checks before we get started
  new_instance_id, new_instance_dict = get_instance_by_tagged_name(new_instance_name)
  instance_id, instance_dict = get_instance_by_tagged_name(host_to_mimic)
  if instance_id == None:
    exit("Cannot continue without a valid instance")
  # Get existing box's metadata
  instance_to_replace = ec2.Instance(instance_id)
  
  # If there's no matching instance to the new name
  if new_instance_id == None:
    security_group_ids = [x['GroupId'] for x in instance_to_replace.security_groups]
    device_map = []
    for device in instance_to_replace.block_device_mappings:
      this_vol = ec2.Volume(device["Ebs"]["VolumeId"])
      device_name = device["DeviceName"] if "/dev/sda" not in device["DeviceName"] else "/dev/sda1"
      
      if recreate_all_volumes:
        device_map.append({ "DeviceName": device_name,
          "Ebs": {
            'VolumeSize': this_vol.size,
            'DeleteOnTermination': this_vol.attachments[0]['DeleteOnTermination'],
            'VolumeType': this_vol.volume_type
          }
        })
      elif recreate_all_volumes == False and "xvda" in device_name:
        # Append only the primary volume
        device_map.append({ "DeviceName": device_name,
          "Ebs": {
            'VolumeSize': this_vol.size,
            'DeleteOnTermination': this_vol.attachments[0]['DeleteOnTermination'],
            'VolumeType': this_vol.volume_type
          }
        })

    # "Upgrade" to the newest generation of servers
    if instance_to_replace.instance_type.startswith('m1'):
      new_instance_type = instance_to_replace.instance_type.replace('m1', 'm3')
    elif instance_to_replace.instance_type.startswith('m2'):
      new_instance_type = instance_to_replace.instance_type.replace('m2', 'r3')
    else:
      new_instance_type = instance_to_replace.instance_type

    if debug:
      # If we're debugging, we don't need a large instance.
      new_instance_type = "t2.micro"
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
      BlockDeviceMappings=device_map,
      SubnetId=instance_to_replace.subnet_id)
      
    new_instance = instances[0]
  else:
    print "An instance named {name} already exists. Not re-creating instance, but running post-processor hooks.".format(name=new_instance_name)
    new_instance = boto3.resource('ec2', region_name='us-west-2').Instance(new_instance_id)
  # Get the tags figured out for the new instance
  tags = instance_to_replace.tags
  for i, tag in enumerate(instance_to_replace.tags):
    if tag["Key"] == "Name":
      tags[i]["Value"] = new_instance_name
      break
  
  if image_type in ['gluster', 'percona', 'proxy']:
    tags.append({
      "Key": "DeployUser",
      "Value": "ubuntu"
      })
  elif "percona" in image_type:
    pass

  #print subprocess.check_output('sudo ssh-keygen -f "/root/.ssh/known_hosts" -R {ip}'.format(ip=new_instance.private_ip_address).split(" ")) 
  #print subprocess.check_output('sudo ssh-keygen -f "/root/.ssh/known_hosts" -R {host}'.format(host=new_instance_name).split(" "))
  # To Tag the instance
  # Ensure the instance is "running"
  new_instance.wait_until_running()
  # Tag the instance with CreateTags()
  new_instance.create_tags(Tags=tags)

  # Determine the hosted zone ID by the instance ID
  hosted_zone_id = "Z2WYJTE6C15CN4" if "nmdev.us" in new_instance_name else "ZS8SECWEXOKXH"

  print "Creating 'A' record: {name}->{ip} in {dns_id}".format(name=new_instance_name, ip=new_instance.private_ip_address, dns_id=hosted_zone_id)
  try:
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
  except botocore.exceptions.ClientError as e:
    print "There was an error creating the A record. You will have to create it manually"
    print "Error: %s" % e
    exit(0)
  user = boto3.client('ec2', region_name='us-west-2').describe_tags(Filters=[{"Name":"resource-id","Values":[new_instance.instance_id]}, {"Name":"key","Values":["DeployUser"]}])['Tags']
  user = "root" if len(user)<1 else str(user[0]['Value'])
  if "gluster" in image_type:
    print "There are some Jenkins jobs that need to be run for gluster. Kicking them off after waiting for it to respond to a ping.\nNote: If this doesn't respond, you may need to manually intervene by restarting the server."
    gluster.poll_server_with_ping(new_instance_name)
    gluster.add_gluster_repo(user, new_instance_name)
    # If it's of type gluster, there are some Jenkins jobs we have to run
    gluster.configure_new_gluster_instance_fnc(user, new_instance_name)

  # if len(device_map) > 1:
  #   time.sleep(60)
  #   for device in device_map:
  #     if "sda" not in device["DeviceName"] and "xvda" not in device["DeviceName"]:
  #       # Non-primary partition that needs formatting

  return new_instance

@siteman.command()
@click.option('--volume-id', prompt='ID of volume to move', help='ID of volume to move')
@click.option('--old-host', prompt='Old Hostname', help='Instance ID that volume is currently attached to')
@click.option('--new-host', prompt='New Hostname', help='Instance ID that you would like to attach the volume to')
@click.option('--device-name', prompt='Device Name', help='Name of device in AWS and FSTAB. Note - if these names don\'t match, this will not work.')
@click.option('--volume-type', default="standard", help="Specifying a different volume type can trigger custom actions. See help for choices.", type=click.Choice(['standard', 'gluster', 'percona', 'proxy']))
def move_volume(volume_id, old_host, new_host, device_name, volume_type):
  # Setup the SSH commands
  ssh_cmd = "ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no {user}@{host}"
  umount_cmd = ssh_cmd + " sudo umount {device}"
  mkdir_cmd = ssh_cmd + " sudo mkdir -p {folder}"
  mount_cmd = ssh_cmd + " sudo mount {device}"
  
  # Figure out the old instance ID by hostname tags
  old_instance_id, old_instance_dict = get_instance_by_tagged_name(old_host)
  if old_instance_id == None:
    exit("Cannot continue without a valid instance to get the volume from")
  old_user = boto3.client('ec2', region_name='us-west-2').describe_tags(Filters=[{"Name":"resource-id","Values":[old_instance_id]}, {"Name":"key","Values":["DeployUser"]}])['Tags']
  old_user = "root" if len(old_user)<1 else str(old_user[0]['Value'])

  # Figure out the new instance ID by hostname tags
  new_instance_id, new_instance_dict = get_instance_by_tagged_name(new_host)
  # If we couldn't find the instance, spawn a new one
  if new_instance_id == None:
    print "Since no match found, assuming that you want a brand new instance"
    # We have to have a string to find the AMI, so if we don't have one, fail
    if volume_type == "standard":
      raise Exception("Cannot create a new instance unless you specify a non-standard volume-type")
    # Create the new instance
    new_instance = create_instance_like_fnc(host_to_mimic=old_host, image_type=volume_type, new_instance_name=new_host, recreate_all_volumes=False)
    new_instance_id = new_instance.instance_id
    new_user = boto3.client('ec2', region_name='us-west-2').describe_tags(Filters=[{"Name":"resource-id","Values":[new_instance_id]}, {"Name":"key","Values":["DeployUser"]}])['Tags']
    new_user = "root" if len(new_user)<1 else str(new_user[0]['Value'])

  print "Moving {vol} - detaching from {old} and attaching to {new}".format(vol=volume_id, old=old_instance_id, new=new_instance_id)

  new_user = boto3.client('ec2', region_name='us-west-2').describe_tags(Filters=[{"Name":"resource-id","Values":[new_instance_id]}, {"Name":"key","Values":["DeployUser"]}])['Tags']
  new_user = "root" if len(new_user)<1 else new_user[0]['Value']

  # Connect to EC2
  ec2 = boto3.resource('ec2', region_name='us-west-2')
  # Get the volume we're moving
  vol = ec2.Volume(volume_id)

  print "Moving {device} from {ouser}@{ohost} to {nuser}@{nhost}".format(device=device_name,ouser=old_user,ohost=old_host,nuser=new_user,nhost=new_host)

  try:
    if volume_type == "gluster":
      # Determine the gluster node we'll run against later
      environment = "staging" if "nmdev.us" in new_host else "production"
      gluster_user = "root" if environment == "staging" else "ubuntu"
      gluster_host = "gluster01.nmdev.us" if environment == "staging" else "gluster06.newmediadenver.com"
      if old_host == "gluster01.nmdev.us":
        gluster_host = "gluster02.nmdev.us"
      elif old_host == "gluster06.newmediadenver.com":
        gluster_host = "gluster05.newmediadenver.com"
        
      gluster.kill_gluster_fnc(old_user, old_host)
    # SSH into the old instance and umount the volume.
    ret = subprocess.check_output(umount_cmd.format(user=old_user,host=old_host,device=device_name).split(" "), stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    # If the volume wasn't mounted
    if "not mounted" in e.output:
      print "The volume wasn't mounted. Continuing..."
    else:
      exit(e.output)

  # SSH into the old instance and delete the fstab entry.
  fstab_entry, fstab_entry_line = remote_fstab.find_and_remove_fstab_entry(old_user, old_host, device_name)
  
  # Detach it
  old_info = vol.detach_from_instance(InstanceId=old_instance_id)
  aws_device_name = old_info['Device']

  while vol.state != "available":
    print "Current volume state is '{state}'. Waiting for available state.".format(state=vol.state)
    time.sleep(5)
    vol.reload()
  
  # Attach it to the new instance
  vol.attach_to_instance(InstanceId=new_instance_id, Device=old_info['Device'])
  
  # SSH into the new instance and create an fstab entry
  remote_fstab.append_fstab_entry(new_user, new_host, fstab_entry_line)

  # SSH into the new instance and mkdir -p the directory
  subprocess.check_output(mkdir_cmd.format(user=new_user, host=new_host, folder=fstab_entry[1]).split(" "))
  
  while vol.state != "in-use":
    print "Current volume state is '{state}'. Waiting for 'in-use' state.".format(state=vol.state)
    time.sleep(5)
    vol.reload()
  # SSH into the new instance and mount it
  subprocess.check_output(mount_cmd.format(user=new_user, host=new_host, device=device_name).split(" "))

  if volume_type == "gluster":
    gluster.kill_gluster_fnc(new_user, new_host)
    gluster.start_gluster_fnc(new_user, new_host)
    gluster.peer_connect_fnc(gluster_user, gluster_host, peer=new_host)
    gluster.replace_brick_fnc(old_host, old_user, fstab_entry[1], new_host, new_user, fstab_entry[1])


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
  #move_volume(volume_id='vol-bf658d36', old_instance_id='i-45854cea', new_instance_id='i-52854cfd', device_name='/dev/xvdf')
  siteman()