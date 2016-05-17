import databag
import newrelic

monitors = {x['uri']:x for x in newrelic.get_synthetics_monitors()}
proxy_databag = databag.get_databag(bag_name="upstream", container="nmdproxy")
prod_site_entries = proxy_databag['production']['webcluster01']['apps']
staging_site_entries = proxy_databag['staging']['web01']['apps']

for site_url, entry in prod_site_entries.items():
  # Determine protocol from proxy databag
  if "ssl" in entry or "ssl_force" in entry:
    protocol = "https"
  else:
    protocol = "http"
  full_url = "{protocol}://{site_url}".format(protocol=protocol, site_url=site_url)
  print "Working on {url}...".format(url=full_url)
  if full_url in monitors.keys():
    # Monitor exists
    if "auth" in entry:
      # A monitor exists behind an auth wall
      print "\tFound a protected monitor at '{url}' with '{id}'. Removing.".format(url=full_url, id=monitors[full_url]['id'])
      newrelic.remove_synthetics_monitor(monitors[full_url]['id'])
    else:
      print "\t'{url}' is already being properly monitored. Skipping.".format(url=full_url)
  else:
    # Monitor doesn't exist
    if "auth" in entry:
      # Skip a site behind auth wall
      print "\tSite '{url}' is protected by an authentication wall. Not adding...".format(url=full_url)
    else:
      # Add a valid site
      print "\tAdding site to monitor."
      newrelic.create_synthetics_monitor(site_url, full_url)