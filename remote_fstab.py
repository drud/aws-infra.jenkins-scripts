#!/usr/bin/python
import subprocess

def get_fstab(user, host="gluster01.nmdev.us"):
  aws_key='/var/jenkins_home/.ssh/aws.pem'
  # ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no {{ USERNAME }}@{{ HOST }}
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user, host=host)]
  ssh_cmd += 'sudo cat /etc/fstab'.split(" ")

  fstab_file_contents = subprocess.check_output(ssh_cmd)
#   fstab_file_contents="""LABEL=centos_root   /        ext4      defaults         0 0
# devpts     /dev/pts  devpts  gid=5,mode=620   0 0
# tmpfs      /dev/shm  tmpfs   defaults         0 0
# proc       /proc     proc    defaults         0 0
# sysfs      /sys      sysfs   defaults         0 0
# /dev/xvdf /srv/sdb1 ext4 defaults 0 2"""
  if 'Please login as the user "ubuntu" rather than the user "root".' in fstab_file_contents:
    raise Exception("Please set the 'DeployUser' tag in EC2 to 'ubuntu' so that we can SSH into this machine in the future")
    # We could recover THIS gracefully, but chances are, other functions will fail without this.
    #fstab_file_contents = get_fstab('ubuntu', host)
  return fstab_file_contents

def set_fstab(user, host, fstab_file_contents):
  chmod_fstab(user, host, '0777')
  aws_key='/var/jenkins_home/.ssh/aws.pem'
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user,host=host)]
  ssh_cmd += 'sudo echo "{fstab}" > /etc/fstab'.format(fstab=fstab_file_contents).split(" ")
  fstab_file_contents = subprocess.check_output(ssh_cmd)
  chmod_fstab(user, host, '0644')

def find_and_remove_fstab_entry(user, host, device_name):
  fstab_file_contents = get_fstab(user, host)
  fstab_lines = fstab_file_contents.split("\n")
  fstab_entry = []
  fstab_entry_index = None
  print "Listing fstab on old machine:"
  for index, line in enumerate(fstab_lines):
    print "Entry: {entry}".format(entry=line)
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
  chmod_fstab(user, host, '0777')
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user,host=host)]
  ssh_cmd += 'sudo echo "{fstab}" >> /etc/fstab'.format(fstab=fstab_entry_line).split(" ")
  subprocess.check_output(ssh_cmd)
  chmod_fstab(user, host, '0644')

def move_fstab_entry(old_user, old_host, new_user, new_host, device_to_move='/dev/xvdf'):
  fstab_entry, fstab_entry_line = find_and_remove_fstab_entry(old_user, old_host, device_to_move)
  add_fstab_entry(new_user, new_host, fstab_entry_line)

def chmod_fstab(user, host, chmod):
  aws_key = '/var/jenkins_home/.ssh/aws.pem'
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user,host=host)]
  ssh_cmd += 'sudo chmod {chmod} /etc/fstab'.format(chmod=chmod).split(" ")
  subprocess.check_output(ssh_cmd)

if __name__ == '__main__':
  # AWS devices /dev/sda and /dev/xvdf
  move_fstab_entry()

