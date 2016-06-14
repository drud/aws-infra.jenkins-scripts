#!/usr/bin/python
import click
import os
import time
#import dns
import dns.resolver
import dns.query
import dns.zone

@click.command()
@click.option('--host', prompt="What host would you like to query?")
@click.option('--record-type', prompt="What type of record would you like to look-up?", type=click.Choice(['A', 'CNAME']))
@click.option('--desired-value', prompt="What is the desired value of that")
def dns_lookup(host, record_type, desired_value):
  if record_type == "CNAME" and not desired_value.endswith("."):
    print "CNAME values must end with a '.' Modifying the CNAME from {val1} to {val2}.".format(val1=desired_value,val2=desired_value+'.')
    desired_value = desired_value + "."
  try:
    answers = dns.resolver.query(host, record_type)
  except dns.resolver.NXDOMAIN:
    print "'{host}' did not have any '{type}' records associated with it".format(host=host, type=record_type)
    return False
  except dns.resolver.NoAnswer:
    print "'{host}' did not have any '{type}' records associated with it".format(host=host, type=record_type)
    return False
  
  if len(answers) == 1:
    record_value = answers[0]
    values = [record_value]
  else:
    values = [record_value]

  match_found = False
  for value in values:
    if str(value) == desired_value:
      print "The {type} record for {host} is configured correctly. It is pointing to {desired_value}.".format(type=record_type, host=host, desired_value=desired_value)
      match_found = True
      return True
    else:
      print "There is a {type} record for {host}. It is pointing to {value}".format(type=record_type, host=host, value=str(value))

  if not match_found:
    print "No matching record. Here are the current A and CNAME values for {host}:".format(host=host)
    get_all_records(host)
    return False

def get_all_records(host):
  try:
    a_records = dns.resolver.query(host, 'A')
  except dns.resolver.NXDOMAIN:
    print "'{host}' did not have any 'A' records associated with it".format(host=host)
    a_records = []
  except dns.resolver.NoAnswer:
    print "'{host}' did not have any 'A' records associated with it".format(host=host)
    a_records = []

  try:
    cname_records = dns.resolver.query(host, 'CNAME')
  except dns.resolver.NXDOMAIN:
    print "'{host}' did not have any 'CNAME' records associated with it".format(host=host)
    cname_records = []
  except dns.resolver.NoAnswer:
    print "'{host}' did not have any 'CNAME' records associated with it".format(host=host)
    cname_records = []

  print "A records for {host}:".format(host=host)
  for record in a_records:
    print "\t%s" % record

  print "CNAME records for {host}:".format(host=host)
  for record in cname_records:
    print "\t%s" % record

if __name__ == '__main__':
  dns_lookup()
