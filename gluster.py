#!/usr/bin/python

import click
import aws_instance
import jenkins
import jenkinspoll
aws_key='/var/jenkins_home/.ssh/aws.pem'

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def siteman():
    pass

def build_and_run_command(user, host, command):
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user,host=host)]
  ssh_cmd += '{command}'.format(command=command).split(" ")
  return subprocess.check_output(ssh_cmd)

@siteman.command()
@click.option('--user')
@click.option('--host')
@click.option('--peer')
def peer_disconnect(user, host, peer):
  """
  Ex) gluster peer detach gluster02.newmediadenver.com
  """
  command="gluster peer detach {peer}".format(peer=peer)
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
@click.option('--peer')
def peer_connect(user, host, peer):
  """
  Ex) gluster peer probe gluster02.newmediadenver.com
  """
  command="gluster peer probe {peer}".format(peer=peer)
  print build_and_run_command(user, host, command)

def kill_gluster():
  command="service stop glusterd && service stop glusterfsd && killall glusterd && killall glusterfsd"
  print build_and_run_command(user, host, command)

def start_gluster():
  command="service glusterd start && service glusterfsd start"
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
def gluster_status(user, host):
  """
  gluster volume status
  """
  command="gluster volume status"
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
def gluster_heal(user, host):
  """
  gluster volume heal nmd
  """
  command="gluster volume heal nmd"
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
def gluster_heal_info(user, host):
  """
  gluster volume heal nmd info
  """
  command="gluster volume heal nmd info"
  print build_and_run_command(user, host, command)

@siteman.command()
@click.option('--user')
@click.option('--host')
def configure_new_gluster_instance(user, host):
  J = jenkins.Jenkins('https://leroy.nmdev.us', username=os.environ.get('JENKINS_SERVICE_USERNAME'), password=os.environ.get('JENKINS_SERVICE_PASSWORD'))
  # Set build parameters, kick off a new build, and block until complete.
  environment = "staging" if "nmdev.us" in host else "production"

  # Run the ansible installer on the gluster box
  print "Running jenkins-playbook with install options on the gluster box"
  params = {"TARGET_HOST": host, "AWS_ENVIRONMENT": environment, "AWS_SSH_USER": user, "ANSIBLE_TAGS": 'aws,provision,packages'}
  J.build_job("jenkins-playbook", params)
  jenkinspoll.wait_for_job_to_finish("jenkins-playbook", jenkins_connection=J)
  
  # Run just the configuration components of the Jenkins playbook
  print "Running jenkins-playbook with the 'configuration' tag on the gluster box"
  params['ANSIBLE_TAGS'] = "configuration"
  J.build_job("jenkins-playbook", params)
  jenkinspoll.wait_for_job_to_finish("jenkins-playbook", jenkins_connection=J)

@siteman.command()
@click.option('--user')
@click.option('--host')
def gluster_replace_brick(old_host, old_user, old_mount_point, new_host, new_user, new_mount_point):
  """
  gluster volume replace-brick nmd gluster02.newmediadenver.com:/srv/sdb1/nmd gluster06.newmediadenver.com:/srv/sdg1/nmd commit force
  """
  command="gluster volume replace-brick nmd {old_host}:{old_mount_point}/nmd {new_host}:{new_mount_point}/nmd commit force".format(old_user=old_user, old_host=old_host, old_mount_point=old_mount_point, new_user=new_user, new_host=new_host, new_mount_point=new_mount_point)
  print build_and_run_command(user, host, command)

def move_gluster_brick():
  # Stop glusterd
  # Stop glusterfsd

  # Unmount the volume
  # Delete the old fstab
  # Detach the volume
  # Attach the volume
  # Create the new fstab
  # Mount the volume
  aws_instance.move_volume(volume_id, old_instance_id, new_instance_id, device_name)

  # Start glusterd
  # Start glusterfsd
  # Discover the new peer
  # Replace the old brick with the new one




