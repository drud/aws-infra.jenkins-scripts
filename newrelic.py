#!/usr/bin/python
from os import environ
import requests
import click
import databag_local as databag
import base64

admin_key = environ.get("NEWRELIC_API_KEY")

def create_synthetics_monitor(monitor_name, monitor_url, monitor_type="BROWSER", monitor_frequency=15):
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
  payload = build_monitor(monitor_name, monitor_type, monitor_url=monitor_url, frequency=monitor_frequency)
  r = requests.post(synthetics_endpoint, json=payload, headers=headers)
  if r.status_code != 201:
    print "Status Code is {code}".format(code=r.status_code)
    print r.text
    return False

  print "\tSuccessfully added {monitor} -> {monitor_url}".format(monitor=monitor_name, monitor_url=monitor_url)
  #return True

  if monitor_type == "SCRIPT_BROWSER":
    # Get the monitor ID
    # Get the monitor location URL (which has the ID at the end of it)
    location_url=r.headers['Location']
    monitor_id = location_url.replace(synthetics_endpoint+"/", "")
    add_script_to_synthetics_monitor(monitor_id, monitor_url)

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
    print "\tSuccessfully removed monitor with id {id}".format(id=monitor_id)
    return True

def update_existing_synthetics_monitor(monitor_id, new_monitor):
  synthetics_endpoint=r"https://synthetics.newrelic.com/synthetics/api/v1/monitors/{id}".format(id=monitor_id)
  headers = {
    'X-Api-Key': admin_key,
    'Content-Type': 'application/json'
  }
  r = requests.put(synthetics_endpoint, json=new_monitor, headers=headers)
  if r.status_code != 204:
    print "Failed to update monitor with id {id}".format(id=monitor_id)
    print "Status code is {code}".format(code=r.status_code)
    print r.text
    return False
  else:
    print "\tSuccessfully updated monitor with id {id}".format(id=monitor_id)
    return True

def add_script_to_synthetics_monitor(monitor_id, monitor_url):
  synthetics_endpoint=r"https://synthetics.newrelic.com/synthetics/api/v1/monitors/{id}/script".format(id=monitor_id)
  
  # Generate the base64 string for the basic HTTP authentication
  decoded_auth_string = "{user}:{password}".format(user=environ.get("NEWRELIC_QUERY_USER"), password=environ.get("NEWRELIC_QUERY_PASSWORD"))
  encoded_auth_string = base64.b64encode(decoded_auth_string)
  
  # Here's a little Selenium/Node.JS to pass through the HTTP auth and query the site
  scripted_browser="""
var assert = require('assert');
$browser.addHeader("Authorization", "Basic " + "%s");
$browser.get("%s").then(function(){
});
"""
  scripted_browser = scripted_browser % (encoded_auth_string, monitor_url)
  scripted_browser_encoded=base64.b64encode(scripted_browser)
  payload = {
    "scriptText": scripted_browser_encoded
  }
  headers = {
    'X-Api-Key': admin_key,
    'Content-Type': 'application/json'
  }
  r = requests.put(synthetics_endpoint, json=payload, headers=headers)
  if r.status_code != 204:
    print "Failed to add script to monitor with id {id}".format(id=monitor_id)
    print "Status code is {code}".format(code=r.status_code)
    print r.text
    return False
  else:
    print "\tSuccessfully added script to monitor with id {id}".format(id=monitor_id)
    return True

def build_monitor(monitor_name, monitor_type, monitor_url=None, frequency=60, locations=["AWS_US_WEST_2"]):
  monitor = {
    "name": monitor_name,
    "type": monitor_type,
    "frequency": frequency,
    "locations": locations,
    "status": "ENABLED"
  }
  if monitor_url != None:
    monitor["uri"] = monitor_url
  return monitor

def has_synthetics_monitor_script(monitor_id):
  """
  curl -v
     -H 'X-Api-Key: {Admin_User_Key}' 
     https://synthetics.newrelic.com/synthetics/api/v1/monitors/{id}/script
  """
  synthetics_endpoint=r"https://synthetics.newrelic.com/synthetics/api/v1/monitors/{id}/script".format(id=monitor_id)
  
  headers = {
    'X-Api-Key': admin_key
  }
  r = requests.get(synthetics_endpoint, headers=headers)
  if int(r.status_code) not in [200, 403, 404]:
    print "Invalid status code recieved".format(id=monitor_id)
    print "Status code is {code}".format(code=r.status_code)
    print r.text
    return False
  elif r.status_code == 200:
    print "\tMonitor has a script associated with it already"
    return True
  elif r.status_code == 403:
    print "The monitor is not the correct type"
    return False
  elif r.status_code == 404:
    print "\tThe monitor has no script associated with it."
    return False

@click.command()
@click.option("--operation", help="Add/list/remove/update")
@click.option("--add", 'operation', flag_value='add')
@click.option("--list", 'operation', flag_value='list')
@click.option("--remove", 'operation', flag_value='remove')
@click.option("--update", 'operation', flag_value='update')
@click.option("--add-script", 'operation', flag_value='add-script')
@click.option("--monitor-name", help="The human friendly name of the synthetics monitor")
@click.option("--monitor-url", help="The URL that you would like to monitor")
@click.option("--monitor-id", help="Monitor id is needed for remove/update")
@click.option("--monitor-type", default="BROWSER", help="The type of monitor", type=click.Choice(["SIMPLE", "BROWSER", "SCRIPT_API", "SCRIPT_BROWSER"]))
def synthetics_router(operation, monitor_name, monitor_url, monitor_id, monitor_type):
  if operation == "add":
    create_synthetics_monitor(monitor_name, monitor_url)
  elif operation == "list":
    get_synthetics_monitors()
  elif operation == "remove":
    remove_synthetics_monitor(monitor_id)
  elif operation == "update":
    new_monitor = build_monitor(monitor_name, monitor_type, monitor_url)
    update_existing_synthetics_monitor(monitor_id, new_monitor)
  elif operation == "add-script":
    add_script_to_synthetics_monitor(monitor_id, monitor_url)

if __name__ == '__main__':
  synthetics_router()