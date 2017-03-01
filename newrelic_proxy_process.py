import newrelic
import time
import math
import subprocess
import proxy

monitor_default_frequency=60
monitor_default_type="SIMPLE"

def pointed_at_us():
  out = subprocess.subprocess("dig -t CNAME {site}")
  if "hosting.newmediadenver.com" in out:
    return True
  else:
    return False

def fix_monitor_frequency(frequency_threshold=5, new_frequency=15):
  for monitor in newrelic.get_synthetics_monitors():
    print "Working on {monitor_name}".format(monitor_name=monitor["name"])
    # If the monitor frequency is set too fine.
    if monitor["frequency"] <= frequency_threshold:
        print "\tThis monitor checks too frequently - changing..."
        new_monitor = newrelic.build_monitor(monitor['name'], monitor['type'], monitor_url=monitor['uri'], frequency=new_frequency, locations=monitor["locations"])
        newrelic.update_existing_synthetics_monitor(monitor['id'], new_monitor)
    else:
      print "\tThe frequency is fine."

def fix_monitor_type(wrong_monitor_type, correct_monitor_type, monitor=None):
  # If there's no monitor passed in, do this on all sites
  if monitor == None:
    print "Finding all monitors of type {wrong} and changing to type {correct}.".format(wrong=wrong_monitor_type, correct=correct_monitor_type)
    for monitor in newrelic.get_synthetics_monitors():
      print "Working on {monitor_name}".format(monitor_name=monitor["name"])

      if monitor['type'] == wrong_monitor_type:
        print "\tThis is is a '{type}' monitor, and it needs to be of type '{correct}'.".format(type=monitor['type'], correct=correct_monitor_type)
        print "\tUpdating type..."
        new_monitor = newrelic.build_monitor(monitor['name'], correct_monitor_type, monitor_url=monitor['uri'], frequency=monitor["frequency"], locations=monitor["locations"])
        newrelic.update_existing_synthetics_monitor(monitor['id'], new_monitor)
  else:
    if monitor['type'] == wrong_monitor_type:
      print "\tThis is is a '{type}' monitor, and it needs to be of type '{correct}'.".format(type=monitor['type'], correct=correct_monitor_type)
      print "\tUpdating type..."
      new_monitor = newrelic.build_monitor(monitor['name'], correct_monitor_type, monitor_url=monitor['uri'], frequency=monitor["frequency"], locations=monitor["locations"])
      newrelic.update_existing_synthetics_monitor(monitor['id'], new_monitor)


def calculate_synthetics_timing(site_entries):
  total_checks_per_year = 15000 * 12
  total_number_of_sites = len(site_entries)
  print "We have %d checks available per year" % total_checks_per_year
  print "We have %d sites that we're going to be monitoring" % total_number_of_sites
  total_checks_per_day = float(total_checks_per_year) / float(365)
  print "And %1.3f checks per day for all sites" % total_checks_per_day
  checks_per_site_per_day = float(float(total_checks_per_day) / float(total_number_of_sites))
  print "That means a single site gets %1.3f checks per day" % checks_per_site_per_day
  check_frequency = float(24) / checks_per_site_per_day
  print "That means a single site gets a check every %1.3f hours" % check_frequency
  check_frequency_in_minutes = int(math.floor(check_frequency) * 60)
  print "Or check every %d minutes" % check_frequency_in_minutes
  
  # Find the closest frequency time that matches
  valid_frequencies = [1, 5, 10, 15, 30, 60, 360, 720, 1440]
  best_frequency = 0
  for freq in valid_frequencies:
    if freq >= check_frequency_in_minutes:
      best_frequency = freq
      break
  print "New Relic only accepts the following frequencies: {freqs}".format(freqs=", ".join(str(x) for x in valid_frequencies))
  print "So we will use the closest acceptable number of {best_freq}".format(best_freq=best_frequency)

  return best_frequency



if __name__ == '__main__':
  #fix_monitor_frequency(frequency_threshold=15, new_frequency=60)
  #fix_monitor_type("SIMPLE", "BROWSER")

  # Get all the synthetics monitors
  monitors = {x['uri']:x for x in newrelic.get_synthetics_monitors()}

  # Pull the proxy databag and parse out the staging and production sites
  proxy_layer = proxy.get_proxy()

  monitor_default_frequency = calculate_synthetics_timing(site_entries)
  fix_monitor_frequency(frequency_threshold=monitor_default_frequency-1, new_frequency=monitor_default_frequency)

  for site_url, entry in proxy['production'].items():
    # Determine protocol from proxy databag
    if "ssl" in entry or "ssl_force" in entry:
      protocol = "https"
    else:
      protocol = "http"
    full_url = "{protocol}://{site_url}".format(protocol=protocol, site_url=site_url)
    print "Working on {url}...".format(url=full_url)
    if full_url in monitors.keys():
      print "\tMonitor already exists"
      # Monitor exists - use update or delete
      monitor = monitors[full_url]
      # if "auth" in entry:
      #   # A monitor exists behind an auth wall - use a scripted browser
      #   print "\tFound a protected monitor at '{url}' with '{id}'.".format(url=full_url, id=monitor['id'])
      #   # If it's not a scripted browser, make it one
      #   if monitor['type'] != "SCRIPT_BROWSER":
      #     print "\tThis is not a scripted browser, but needs to be."
      #     print "\tConverting to scripted browser"
      #     new_monitor = newrelic.build_monitor(monitor['name'], "SCRIPT_BROWSER", monitor_url=None, frequency=monitor["frequency"], locations=monitor["locations"])
      #     newrelic.update_existing_synthetics_monitor(monitor['id'], new_monitor)
      #   else:
      #     print "\tFound an existing scripted browser"
      #    # Now check to see if the scripted browser actually has a script attached to it.
      #     if not newrelic.has_synthetics_monitor_script(monitor['id']):
      #       print "\tNo script found. Attaching script."
      #       newrelic.add_script_to_synthetics_monitor(monitor['id'], monitor['uri'])
      #     else:
      #       print "\tScripted browser configured correctly. Continuing."
      # else:
      #   # This is not behind an auth wall, it needs to be a browser, but I'm 
      #   wrong_monitor_type="BROWSER"
      #   correct_monitor_type="SIMPLE"
      #   fix_monitor_type(wrong_monitor_type, correct_monitor_type, monitor=monitor)
      print "Montior exists, doing nothing"
    else:
      # Monitor doesn't exist
      print "\tMonitor does not exist. Creating..."
      # Create the monitor
      #monitor_type = "SCRIPT_BROWSER" if "auth" in entry else "SIMPLE"
      newrelic.create_synthetics_monitor(site_url, full_url, monitor_type, monitor_frequency=monitor_default_frequency)