#!/usr/bin/python
from os import environ
import requests
import json
admin_key = environ.get("NEWRELIC_API_KEY")

def get_server(server_name):
  """
  curl -X GET 'https://api.newrelic.com/v2/servers.json' \
     -H 'X-Api-Key:d0e90bdbf93840ffb33c3dbb53a7786f' -i \
     -G -d 'filter[name]=web01.newmediadenver.com'
  Returns the first matching server
  """
  server_endpoint = r"https://api.newrelic.com/v2/servers.json"
  headers = {
    'X-Api-Key': admin_key,
  }
  payload = {"filter[name]":str(server_name)}
  r = requests.post(server_endpoint, headers=headers, data=payload)

  if r.status_code != 200:
    print "Failed to get server"
    print "Status code is {code}".format(code=r.status_code)
    print r.text
  else:
    return r.json()["servers"][0]

if __name__ == '__main__':
  print get_server("web01.newmediadenver.com")