#!/usr/bin/python
import aws_instance
import subprocess
from os.path import exists as exists
instance_id = 'i-318ca4c6'
image_type = "gluster"
new_instance_name = 'gluster0test.nmdev.us'
new_instance_name = "gluster01.nmdev.us"
#create_instance_like(instance_id='i-318ca4c6', image_type="gluster", new_instance_name='gluster0test.nmdev.us')

def get_fstab(host="gluster01.nmdev.us"):
  user="root" if "nmdev.us" in host else "ubuntu"
  aws_key='/var/jenkins_home/.ssh/aws.pem'
  # ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no {{ USERNAME }}@{{ HOST }}
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user,host=host)]
  ssh_cmd += 'sudo cat /etc/fstab'.split(" ")
  # Commenting out the actual callback during testing
  #fstab_file_contents = subprocess.check_output(ssh_cmd)
  fstab_file_contents="""LABEL=centos_root   /        ext4      defaults         0 0
devpts     /dev/pts  devpts  gid=5,mode=620   0 0
tmpfs      /dev/shm  tmpfs   defaults         0 0
proc       /proc     proc    defaults         0 0
sysfs      /sys      sysfs   defaults         0 0
/dev/xvdf /srv/sdb1 ext4 defaults 0 2"""
  return fstab_file_contents

def set_fstab(fstab_file_contents, host="gluster01.nmdev.us"):
  user="root" if "nmdev.us" in host else "ubuntu"
  aws_key='/var/jenkins_home/.ssh/aws.pem'
  ssh_cmd = ['ssh', '-p22', '-vv', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user,host=host)]
  # TODO - Change fstab2 to fstab
  ssh_cmd += 'sudo echo "{fstab}" > /etc/fstab2'.format(fstab=fstab_file_contents).split(" ")
  fstab_file_contents = subprocess.check_output(ssh_cmd)

def find_and_remove_fstab_entry(device_name, fstab_file_contents):
  fstab_lines = fstab_file_contents.split("\n")
  fstab_entry = []
  fstab_entry_index = None
  for index, line in enumerate(fstab_lines):
    # Find the line with the device on it
    if line.startswith(device_name):
      fstab_entry_line = line
      fstab_entry = line.split(' ')
      fstab_entry_index = index
      break
  # if we cannot find the entry, return nothing
  if fstab_entry_index is None:
    print "FSTAB ENTRY NOT FOUND"
    return None, fstab_file_contents
  
  # Remove entry
  del fstab_lines[fstab_entry_index]

  # Reassemble the file contents
  fstab_modified_file_contents = "\n".join(fstab_lines)
  return fstab_entry, fstab_modified_file_contents

fstab_file_contents = get_fstab()
fstab_entry, fstab_modified_file = find_and_remove_fstab_entry('/dev/xvdf', fstab_file_contents)
if fstab_entry == None:
  raise Exception("Cannot continue without a valid fstab entry here")
set_fstab(fstab_modified_file)


# AWS devices /dev/sda and /dev/xvdf
# [csterling@gluster01 ~]$ cat /etc/fstab
# LABEL=centos_root   /        ext4      defaults         0 0
# devpts     /dev/pts  devpts  gid=5,mode=620   0 0
# tmpfs      /dev/shm  tmpfs   defaults         0 0
# proc       /proc     proc    defaults         0 0
# sysfs      /sys      sysfs   defaults         0 0
# /dev/xvdf /srv/sdb1 ext4 defaults 0 2

# # Get the fstab entry
# with open('/etc/fstab', 'r') as fp:
#   # Find the entry we want to operate on
#   lines = fp.readlines()
# for line in lines:
#   if line.startswith('/dev/xvdf'):
#     fstab_entry_line = line
#     fstab_entry = line.split(' ')
#     break

# # Write the fstab entry
# with open("/etc/fstab","r") as current_fstab:
#   with open("/tmp/fstab","wb") as tmp_fstab: 
#     for line in current_fstab:
#       # Skip over the entry
#       if line != fstab_entry_line
#         tmp_fstab.write(line)
# # TODO - Move tmp fstab into place on old machine
