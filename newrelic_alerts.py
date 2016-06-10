#!/usr/bin/python
from os import environ
import requests
import json
admin_key = environ.get("NEWRELIC_API_KEY")

def get_alert_policy(alert_policy_id):
  """
  curl -X GET 'https://api.newrelic.com/v2/alert_policies/480465.json' \
     -H 'X-Api-Key:d0e90bdbf93840ffb33c3dbb53a7786f' -i 
  """
  alert_endpoint = "https://api.newrelic.com/v2/alert_policies/{id}.json".format(id=alert_policy_id)
  headers = {
    'X-Api-Key': admin_key,
  }
  r = requests.get(alert_endpoint, headers=headers)
  if r.status_code != 200:
    print "Failed to get list"
    print "Status code is {code}".format(code=r.status_code)
    print r.text
  else:
    return r.json()["monitors"]

def change_alert_monitor(server_name):
  alert_policy_id = newrelic_server.get_server(server_name)['links']['alert_policy']
  alert_policy = newrelic_alerts.get_alert_policy(alert_policy_id)
  #TODO - modify the policy

if __name__ == '__main__':
  change_alert_monitor("web01.newmediadenver.com")