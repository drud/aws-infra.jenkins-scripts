#!/usr/bin/python
import aws_instance
import subprocess

instance_id = 'i-318ca4c6'
image_type = "gluster"
old_host = "gluster01.nmdev.us"
new_host = 'gluster0test.nmdev.us'
user="root" if "nmdev.us" in host else "ubuntu"
#create_instance_like(instance_id='i-318ca4c6', image_type="gluster", new_instance_name='gluster0test.nmdev.us')

def get_fstab(user, host="gluster01.nmdev.us"):
  aws_key='/var/jenkins_home/.ssh/aws.pem'
  # ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no {{ USERNAME }}@{{ HOST }}
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += "{user}@{host}".format(user=user, host=host)
  ssh_cmd += 'sudo cat /etc/fstab'.split(" ")

  fstab_file_contents = subprocess.check_output(ssh_cmd)
#   fstab_file_contents="""LABEL=centos_root   /        ext4      defaults         0 0
# devpts     /dev/pts  devpts  gid=5,mode=620   0 0
# tmpfs      /dev/shm  tmpfs   defaults         0 0
# proc       /proc     proc    defaults         0 0
# sysfs      /sys      sysfs   defaults         0 0
# /dev/xvdf /srv/sdb1 ext4 defaults 0 2"""
  return fstab_file_contents

def set_fstab(user, host, fstab_file_contents):
  aws_key='/var/jenkins_home/.ssh/aws.pem'
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user,host=host)]
  ssh_cmd += 'sudo echo "{fstab}" > /etc/fstab'.format(fstab=fstab_file_contents).split(" ")
  fstab_file_contents = subprocess.check_output(ssh_cmd)

def find_and_remove_fstab_entry(user, host, device_name):
  fstab_file_contents = get_fstab(user, host)
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
    raise Exception("Cannot continue without a valid fstab entry here")
    #return None, fstab_file_contents
  
  # Remove entry
  del fstab_lines[fstab_entry_index]

  # Reassemble the file contents
  fstab_modified_file_contents = "\n".join(fstab_lines)
  set_fstab(user, host, fstab_modified_file_contents)
  return fstab_entry, fstab_entry_line

def append_fstab_entry(user, host, fstab_entry_line):
  aws_key = '/var/jenkins_home/.ssh/aws.pem'
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += "{user}@{host}".format(user=user,host=host)
  ssh_cmd += 'sudo echo "{fstab}" >> /etc/fstab'.format(fstab=fstab_entry_line).split(" ")
  fstab_file_contents = subprocess.check_output(ssh_cmd)

def move_fstab_entry(old_user, old_host, new_user, new_host, device_to_move='/dev/xvdf')
  fstab_entry, fstab_entry_line = find_and_remove_fstab_entry(old_user, old_host, device_to_move)
  add_fstab_entry(new_user, new_host, fstab_entry_line)

if __name__ == '__main__':
  # AWS devices /dev/sda and /dev/xvdf
  move_fstab_entry()

