#!/usr/bin/python
from os import environ
import requests
import click
import databag_local as databag

admin_key = environ.get("NEWRELIC_API_KEY")

def create_synthetics_monitor(monitor_name, monitor_url):
  """
  Source: https://docs.newrelic.com/docs/apis/synthetics-rest-api/monitor-examples/manage-synthetics-monitors-via-rest-api
  Command:
  curl -v \
     -X POST -H 'X-Api-Key:{Admin API key}' \
     -H 'Content-Type: application/json' https://synthetics.newrelic.com/synthetics/api/v1/monitors \
     -d '{  "name" : "Monitor Name",  "frequency" : 15, "uri" : "Monitor URL", "locations" : [ "AWS_US_WEST_2" ], "type" : "SIMPLE"}'
  """
  synthetics_endpoint = r'https://synthetics.newrelic.com/synthetics/api/v1/monitors'
  headers = {
    'X-Api-Key': admin_key,
    'Content-Type': 'application/json'
  }
  payload = {
    "name" : monitor_name,
    "frequency" : 5,
    "uri" : monitor_url,
    "locations" : [ "AWS_US_WEST_2" ],
    "type" : "SIMPLE"
  }
  r = requests.post(synthetics_endpoint, json=payload, headers=headers)
  if r.status_code != 201:
    print "Status Code is {code}".format(code=r.status_code)
    print r.text
    return False
  else:
    print "Successfully added {monitor} -> {monitor_url}".format(monitor=monitor_name, monitor_url=monitor_url)
    return True

def get_synthetics_monitors():
  """
  curl -v
     -H 'X-Api-Key:{Admin_User_Key}' https://synthetics.newrelic.com/synthetics/api/v1/monitors
  """
  synthetics_endpoint = r"https://synthetics.newrelic.com/synthetics/api/v1/monitors"
  headers = {
    'X-Api-Key': admin_key,
  }
  r = requests.get(synthetics_endpoint, headers=headers)
  if r.status_code != 200:
    print "Failed to get list"
    print "Status code is {code}".format(code=r.status_code)
    print r.text
  else:
    return r.json()["monitors"]

def remove_synthetics_monitor(monitor_id):
  """
  curl -v 
     -H 'X-Api-Key:{Admin_User_Key}' 
     -X DELETE https://synthetics.newrelic.com/synthetics/api/v1/monitors/{id}
  """
  synthetics_endpoint = r"https://synthetics.newrelic.com/synthetics/api/v1/monitors/{id}".format(id=monitor_id)
  headers = {
    'X-Api-Key': admin_key,
  }
  r = requests.delete(synthetics_endpoint, headers=headers)
  if r.status_code != 204:
    print "Failed to delete monitor with id {id}".format(id=monitor_id)
    print "Status code is {code}".format(code=r.status_code)
    print r.text
    return False
  else:
    print "Successfully removed monitor with id {id}".format(id=monitor_id)
    return True

@click.command()
@click.option("--operation", help="Add/list/remove")
@click.option("--monitor-name", help="The human friendly name of the synthetics monitor")
@click.option("--monitor-url", help="The URL that you would like to monitor")
@click.option("--monitor-id", help="Monitor id is needed for DELETE")
def synthetics_router(operation, monitor_name, monitor_url, monitor_id):
  if operation == "add":
    create_synthetics_monitor(monitor_name, monitor_url)
  elif operation == "list":
    get_synthetics_monitors()
  elif operation == "remove":
    remove_synthetics_monitor(monitor_id)

if __name__ == '__main__':
  synthetics_router()