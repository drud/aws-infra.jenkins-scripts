#!/usr/bin/env python
# An implementation of the default route53 cname hooks for more robust validationa
import click
import boto

@click.command()
@click.option('--bag-name', help="The databag name that correlates to the site")
@click.option('--add', 'operation', flag_value='add', default=True)
@click.option('--remove', 'operation', flag_value='remove')
@click.option('--other-cnames', help="A comma-delimited list of other cnames to remove", default=None)
def cname_records(bag_name, operation, other_cnames):
    # Connect to the server
    conn = boto.connect_route53()
    # Go to our primary hosted zone
    zone = conn.get_zone("nmdev.us.")

    # Generate the default cnames
    default_staging_cname = '{bag}.nmdev.us'.format(bag=bag_name)
    default_prod_cname = '{bag}prod.nmdev.us'.format(bag=bag_name)
    
    if operation == "add":
        try:
          zone.add_cname(default_staging_cname, 'hosting.nmdev.us')
          print "Record '{record}' created.".format(record=default_staging_cname)
        except boto.route53.exception.DNSServerError:
          print "Record '{record}' exists.".format(record=default_staging_cname)
        try:
          zone.add_cname(default_prod_cname, 'hosting.newmediadenver.com')
          print "Record '{record}' created.".format(record=default_prod_cname)
        except boto.route53.exception.DNSServerError:
          print "Record '{record}' exists.".format(record=default_prod_cname)
        print "Done adding."
    elif operation == "remove":
        print "Deleting '{record}'...".format(record=default_staging_cname)
        zone.delete_cname(default_staging_cname)
        print "Deleting '{record}'...".format(record=default_prod_cname)
        zone.delete_cname(default_prod_cname)
        if other_cnames is not None:
            # Turn it into a list object
            other_cnames = other_cnames.split(',')
            for cname in other_cnames:
                zone.delete_cname(cname)
        print "Done deleting."

if __name__ == '__main__':
    cname_records()