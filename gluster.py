#!/usr/bin/python

import click
import aws_instance
import jenkins
import jenkinspoll
import subprocess
import os
import time

aws_key='/var/jenkins_home/.ssh/aws.pem'
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def siteman():
    pass

def build_and_run_command(user, host, command):
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user,host=host)]
  ssh_cmd += 'sudo {command}'.format(command=command).split(" ")
  try:
    return subprocess.check_output(ssh_cmd, stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    # Gracefully handle previously stopped procs
    if "stop: Unknown instance" in e.output:
      return ""
    elif "no process found" in e.output or "no process killed" in e.output:
      return ""
    elif "command not found" in e.output:
      return "command not found"
    elif "/etc/init.d/glusterfs-server: No such file or directory" in e.output:
      return "command not found"
    exit(e.output)

@siteman.command()
@click.option('--user')
@click.option('--host')
@click.option('--peer')
def peer_disconnect(user, host, peer):
  peer_disconnect_fnc(user, host, peer)

def peer_disconnect_fnc(user, host, peer):
  """
  gluster peer detach gluster02.newmediadenver.com
  """
  command="gluster peer detach {peer}".format(peer=peer)
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
@click.option('--peer')
def peer_connect(user, host, peer):
  peer_connect_fnc(user, host, peer)

def peer_connect_fnc(user, host, peer):
  """
  gluster peer probe gluster02.newmediadenver.com
  """
  command="gluster peer probe {peer}".format(peer=peer)
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
def kill_gluster(user, host):
  kill_gluster_fnc(user, host)

def kill_gluster_fnc(user, host):
  print "Killing gluster..."
  out = build_and_run_command(user, host, "/etc/init.d/glusterfs-server stop")
  if out == "command not found":
    print build_and_run_command(user, host, "service glusterd stop")
    print build_and_run_command(user, host, "service glusterfsd stop")
  print build_and_run_command(user, host, "killall glusterfsd")
  print build_and_run_command(user, host, "killall glusterfs")

@siteman.command()
@click.option('--user')
@click.option('--host')
def start_gluster(user, host):
  start_gluster_fnc(user, host)

def start_gluster_fnc(user, host):
  out = build_and_run_command(user, host, "/etc/init.d/glusterfs-server start")
  if out == "command not found":
    print build_and_run_command(user, host, "service glusterd start")
    print build_and_run_command(user, host, "service glusterfsd start")    

@siteman.command()
@click.option('--user')
@click.option('--host')
def gluster_status(user, host):
  gluster_status_fnc(user, host)

def gluster_status_fnc(user, host):
  """
  gluster volume status
  """
  command="gluster volume status"
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
def gluster_heal(user, host):
  gluster_heal_fnc(user, host)

def gluster_heal_fnc(user, host):
  """
  gluster volume heal nmd
  """
  command="gluster volume heal nmd"
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
def gluster_heal_info(user, host):
  gluster_heal_info_fnc(user, host)

def gluster_heal_info_fnc(user, host):
  """
  gluster volume heal nmd info
  """
  command="gluster volume heal nmd info"
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
def configure_new_gluster_instance(user, host):
  configure_new_gluster_instance_fnc(user, host)

def configure_new_gluster_instance_fnc(user, host):
  """
  Kick off jenkins-playbook to make sure the software is installed
  """
  J = jenkins.Jenkins('https://leroy.nmdev.us', username=os.environ.get('JENKINS_SERVICE_USERNAME'), password=os.environ.get('JENKINS_SERVICE_PASSWORD'))
  # Set build parameters, kick off a new build, and block until complete.
  environment = "staging" if "nmdev.us" in host else "production"

  # Override - any new gluster instance should be user=ubuntu
  user="ubuntu"

  # Run the ansible installer on the gluster box
  print "Running jenkins-playbook with install options on the gluster box"
  params = {"TARGET_HOST": "gluster", "AWS_ENVIRONMENT": environment, "AWS_SSH_USER": user, "ANSIBLE_TAGS": 'aws,provision,packages'}
  J.build_job("jenkins-playbook", params)
  jenkinspoll.wait_for_job_to_finish("jenkins-playbook", jenkins_connection=J)
  
  # Run just the configuration components of the Jenkins playbook
  print "Running jenkins-playbook with the 'configuration' tag on the gluster box"
  params['ANSIBLE_TAGS'] = "configuration"
  J.build_job("jenkins-playbook", params)
  jenkinspoll.wait_for_job_to_finish("jenkins-playbook", jenkins_connection=J)

@siteman.command()
@click.option('--old-host', prompt='old_host', help='old_host')
@click.option('--old-mount-point', prompt='old_mount_point', help='old_mount_point')
@click.option('--new-host', prompt='new_host', help='new_host')
@click.option('--new-user', prompt='new_user', help='new_user')
@click.option('--new-mount-point', prompt='new_mount_point', help='new_mount_point')
@click.option('--gluster-user', prompt='gluster_user')
@click.option('--gluster-host', prompt='gluster_host')
def replace_brick(old_host, old_mount_point, new_host, new_user, new_mount_point, gluster_user, gluster_host):
  replace_brick_fnc(old_host, old_user, old_mount_point, new_host, new_user, new_mount_point)

def replace_brick_fnc(old_host, old_mount_point, new_host, new_user, new_mount_point, gluster_user, gluster_host):
  """
  gluster volume replace-brick nmd gluster02.newmediadenver.com:/srv/sdb1/nmd gluster06.newmediadenver.com:/srv/sdg1/nmd commit force
  """
  command="gluster volume replace-brick nmd {old_host}:{old_mount_point}/nmd {new_host}:{new_mount_point}/nmd commit force".format(old_user=old_user, old_host=old_host, old_mount_point=old_mount_point, new_user=new_user, new_host=new_host, new_mount_point=new_mount_point)
  print build_and_run_command(gluster_user, gluster_host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
@click.option('--device')
def format_brick_to_ext4(user, host, device):
  format_brick_to_ext4_fnc(user,host,device)

def format_brick_to_ext4(user, host, device):
  command="mkfs.ext4 {device}".format(device=device)
  print build_and_run_command(user, host, command)

def add_gluster_repo(user, host):
  command="add-apt-repository ppa:gluster/glusterfs-3.7"
  print build_and_run_command(user, host, command)

def ping_server(host):
  try:
    out = subprocess.check_output("ping -c 1 {host}".format(host=host).split(" "), stderr=subprocess.STDOUT)
    return True
  except subprocess.CalledProcessError as e:
    if e.returncode != 0:
      return False

def poll_server_with_ping(host):
  print "Polling {host}. Will continue polling until host responds...".format(host=host)
  while ping_server(host) == False:
    time.sleep(5)

if __name__ == '__main__':
  siteman()
