#!/usr/bin/python
import aws_instance
import subprocess
instance_id = 'i-318ca4c6'
image_type = "gluster"
new_instance_name = 'gluster0test.nmdev.us'
#create_instance_like(instance_id='i-318ca4c6', image_type="gluster", new_instance_name='gluster0test.nmdev.us')

user="root"
host="gluster01.nmdev.us"
aws_key='/var/jenkins_home/.ssh/aws.pem'
aws_key='/Users/csterling/.ssh/nmd/jenkins_ac.pem'
# ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no {{ USERNAME }}@{{ HOST }}
ssh_cmd = ['ssh', '-p22', '-i', aws_key, '-o', 'StrictHostKeyChecking=no', "{user}@{host}".format(user=user,host=host)]
ssh_cmd = ssh_cmd + '"cat /etc/fstab"'.split(" ")
a = subprocess.check_output(ssh_cmd)

print ">>>>a<<<<"




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
