#!/usr/bin/env python
import click
import boto
from boto.route53.record import ResourceRecordSets

@click.group()
def context():
    pass

@context.command()
@click.option('--name', 
    help='The name of the dns entry to create.'
)
@click.option('--value', 
    help='The value of the dns entry to create.'
)
@click.option('--type',
    help='The type of DNS Record to Create',
    type=click.Choice(['A', 'CNAME'])
)
@click.option('--zone', 
    help='The Hosted Zone ID to create the entry in'
)
def create_record(name, value, type, zone):
    """Create DNS entries in route53"""
    conn = boto.connect_route53()
    change_set = ResourceRecordSets(conn, zone)
    change = change_set.add_change("CREATE", name, type)
    change.add_value(value)
    result = change_set.commit()

@context.command()
@click.option('--name', 
    help='The name of the dns entry to delete.'
)
@click.option('--type',
    help='The type of DNS Record to delete',
    type=click.Choice(['A', 'CNAME'])
)
@click.option('--zone', 
    help='The Hosted Zone ID to delete the entry from'
)
def delete_record(name, type, zone):
    """Delete DNS entries in route53"""
    conn = boto.connect_route53()
    zones = {z.id : z for z in conn.get_zones()}
    if type == "CNAME":
        status = zones[zone].delete_cname(name)
    elif type == "A":
        status = zones[zone].delete_a(name)
    else:
        exit("Unsupported record type")

if __name__ == '__main__':
    context()
