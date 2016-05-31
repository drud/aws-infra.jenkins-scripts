#!/usr/bin/python

import click
import os
import requests
import time
import boto
import boto3


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
    ec2_connection = boto3.client('ec2')
    ec2_instances = ec2_connection.describe_instances()["Reservations"]
    for instance in ec2_instances:
        for x in instance["Instances"]:
            instance_name = ""
            # Parse the instance name out of the tags. This is a hacky way - is there a more elegant solution?
            instance_name = [y["Value"] for y in x["Tags"] if y["Key"] == "Name"][0]
            #servers[instance_name] = x["InstanceId"]
            if server_name == instance_name:
                instance_id = x["InstanceId"]
                instance_dict = x
                print "Found server instance ID of '{instance_id}' for server named '{server_name}'".format(instance_id=instance_id, server_name=server_name)
                return instance_id, instance_dict

    if instance_id == "":
        print "A server with name '{server_name}' could not be mapped to an instance id.".format(server_name=server_name)
        exit(1)

def stop_instance(instance):
    # Stop the instance before taking a snapshot - it's more accurate
    # If any transitions are occuring, just hold on
    while instance.state["Name"] == "pending" or instance.state["Name"] == "stopping" or instance.state["Name"] == "starting":
        time.sleep(5)
        instance.reload()
    if instance.state["Name"] != "stopped" and instance.state["Name"] != "stopping":
        # Stop EC2 instance
        try:
            print "Stopping instance"
            instance.stop()
        except:
            print "There was a problem stopping the instance."
            print "Instance state: {instance_state}".format(instance_state=instance.state)
            exit(1)
    while instance.state["Name"] != "stopped":
        time.sleep(5)
        instance.reload()

def start_instance(instance):
    # Start the instance if needed
    # If any transitions are occuring, just hold on
    while instance.state["Name"] == "pending" or instance.state["Name"] == "stopping" or instance.state["Name"] == "starting":
        time.sleep(5)
        instance.reload()
    if instance.state["Name"] != "started" and instance.state["Name"] != "starting":
        try:
            print "Starting instance"
            instance.start()
            instance.wait_until_running()
        except:
            print "Instance cannot be started in it's current state."
            print "Instance state: {instance_state}".format(instance_state=instance.state["Name"])

def show_attached_volumes(instance):
    instance.reload()
    mapping = instance.block_device_mappings
    if len(mapping) <= 0:
        print "No map found. Please check the instance manually to ensure there is at least one valid volume currently attached"
        exit(1)
    devices = {m["DeviceName"]: m["Ebs"]["VolumeId"] for m in mapping}
    devices_by_id= {m["Ebs"]["VolumeId"]: m["DeviceName"] for m in mapping}
    print "Device List:"
    for name, vol_id in devices.iteritems():
        vol = boto3.resource('ec2').Volume(vol_id)
        print "\t{name}:\t{vol_id}\t{vol_size} GiB".format(name=name, vol_id=vol_id, vol_size=vol.size)

@click.command()
@click.option('--server-name', prompt='Server name', help='The FQDN of the server (e.g. web01.newmediadenver.com')
@click.option('--new-size', prompt='New size (GiB)', help='The new size of the volume desired.')
@click.option('--device-name', default='/dev/xvda', help='The name of the device according to the EC2 console.')
def grow_ebs_volume(server_name, new_size, device_name):
    """
    Grow the primary EBS volume for the specified instance
    """
    boto3.setup_default_session(region_name='us-west-2')
    # Order of operations
    # Find instance AMI ID by server name tag
    instance_id, instance_dict = get_instance_by_tagged_name(server_name)
    
    # Get EC2 instance object
    instance = boto3.resource('ec2').Instance(instance_id)

     
    # Get the device mappings for that instance and find the volume's ID
    mapping = instance.block_device_mappings
    if len(mapping) <= 0:
        print "No map found. Please check the instance manually to ensure there is at least one valid volume currently attached"
        exit(1)

    devices = {m["DeviceName"]: m["Ebs"]["VolumeId"] for m in mapping}
    devices_by_id= {m["Ebs"]["VolumeId"]: m["DeviceName"] for m in mapping}
    vol_device_name = ""
    if len(devices) != 1:
        print "More than 1 device found."
        if device_name in devices.keys():
            show_attached_volumes(instance)
            print "Using '{device_name}' (you can override this with the --device-name flag)".format(device_name=device_name)
            vol_id=devices[device_name]
            vol_device_name = devices_by_id[vol_id]
        else:
            print "Select a device:"
            index=0
            vols={}
            for name, vol_id in devices.iteritems():
                vol = boto3.resource('ec2').Volume(vol_id)
                print "\t{index}:\t{name}:\t{vol_id}\t{vol_size} GiB".format(index=index, name=name, vol_id=vol_id, vol_size=vol.size)
                vols[index] = vol_id
                index=index+1
            print "Re-run this job with one of the selected devices above."
            exit(1)
            #Commenting this out since we can't be interactive in Jenkins
            #selected_vol_index = click.prompt("Select a device for '{server_name}'".format(server_name=server_name),type=int)
            #vol_id = vols[selected_vol_index]
            #vol_device_name = devices_by_id[vol_id]
    else:
        # If there's just a single entry, then just pop the item out of the dict (it's the only item)
        vol_device_name, vol_id = devices.popitem()
        print "Using '{vol_name}'/'{vol_id}' since it was the only attached volume found.".format(vol_name=vol_device_name, vol_id=vol_id)
    
    # Now you have the volume
    vol = boto3.resource('ec2').Volume(vol_id)

    # Snapshot the volume
    print "Creating a snapshot of the instance..."
    snapshot = vol.create_snapshot()
    while snapshot.state != "completed":
        time.sleep(5)
        snapshot.reload()
        print "Creating snapshot: {progress}%% complete".format(progress=snapshot.progress)
    # This "waiter" will only wait 10 minutes and error out...which is far too short.
    # snapshot.wait_until_completed()

    # Create a new volume from that snapshot - TODO MATCH AVAILABILITY ZONE WITH INSTANCE
    print "Creating a new volume using the snapshot"
    new_volume = boto3.resource('ec2').create_volume(Size=int(new_size), SnapshotId=snapshot.id, AvailabilityZone=vol.availability_zone)
    while new_volume.state != "available":
        time.sleep(5)
        new_volume.reload()

    # Stop the instance
    stop_instance(instance)
    # Detach the old volume noting where it was stored, waiting for it to fully detach
    print "Detaching the old volume"
    vol.detach_from_instance()
    while vol.state != "available":
        time.sleep(5)
        vol.reload()

    # Attach the new volume to the same place
    print "Attaching the new volume"
    new_volume.attach_to_instance(InstanceId=instance_id, Device=vol_device_name)

    # Delete the old volume
    print "Deleting the old volume"
    vol.delete()
    # Delete the snapshot
    print "Deleting the snapshot"
    snapshot.delete()

    # Start the instance
    start_instance(instance)

    print "Instance restarted. Here are the devices -"
    show_attached_volumes(instance)
    
if __name__ == '__main__':
    grow_ebs_volume()