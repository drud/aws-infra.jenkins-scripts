import databag
import requests
import os
import re



def recompute_proxy_data(deploy_env):
    """
    The proxy layer is arranged so that when you are trying to
    find the information for a specific application, it is not
    predictably in the same place. nmdproxy[environment] works, 
    but X in nmdproxy[environment][X][apps] is not a predictable
    variable. This function takes the proxy data and reorganizes
    it into something more digestible by ansible Jinja2 templates
    """
    nmdproxy = databag.get_databag('upstream', 'nmdproxy')
    proxy = {}
    for env_name, env in nmdproxy.items():
        if env_name == "id":
            continue
        elif env_name == "_redirect":
            for app_name, app in env['apps'].items():
                proxy[app_name] = app
                proxy[app_name]['env_name'] = env_name
                proxy[app_name]['servers'] = '_redirect' if env_name == "_redirect" else top_level_app['servers']
                proxy[app_name]['dest'] = '' if 'dest' not in app else app['dest']
                proxy[app_name]['protocol'] = 'https' if 'ssl' in app else 'http'
        else:
            for pool_name, top_level_app in env.items():
                if 'apps' in top_level_app:
                    apps = top_level_app['apps']
                    for app_name, app in apps.items():
                        if env_name == deploy_env:
                            proxy[app_name] = app
                            proxy[app_name]['pool_name'] = pool_name
                            proxy[app_name]['env_name'] = env_name
                            proxy[app_name]['servers'] = '_redirect' if env_name == "_redirect" else top_level_app['servers']
                            proxy[app_name]['dest'] = '' if 'dest' not in app else app['dest']
                            proxy[app_name]['protocol'] = 'https' if 'ssl' in app else 'http'
                else:
                    print "Could not process {app}".format(app=pool_name)
    return proxy

def get_urls(deploy_env):
	proxy = recompute_proxy_data(deploy_env)
	for url, app in proxy.items():
		protocol = app['protocol']
		full_url = "{protocol}://{url}".format(protocol=protocol,url=url)
		yield full_url

def diagnose_url(url, success, redirect, error, inconsistencies, authentication):
	try:
		# Call the request twice in case a cache prime is needed
		r1 = requests.get(url, auth=(user, password))
		r = requests.get(url, auth=(user, password))
		if r.status_code == 200:
			success.append(url)
		elif r.status_code == 301:
			print "Unhandled redirect - the requests module should have followed this"
			print r.json()
		elif r.status_code == 401:
			print "The credentials for {url} did not work. A 401 error was recieved. Please fix the credentials for the site.".format(url=url)
			exit("Discontinuing run as it could lock out a user account.")
		else:
			error[r.status_code].append(url)
			# If we can get an actual error message, let's do it
			matches = regex.search(r.text)
			if matches and matches.groupdict():
				message = matches.groupdict()['message'].replace("{status} ".format(status=r.status_code), "")
				title = matches.groupdict()['title'].replace("{status} ".format(status=r.status_code), "")
				print "{url} returned {status} {title}: {message}".format(status=r.status_code, url=url, title=title, message=message)
			else:
				print "{url} returned {status}".format(status=r.status_code, url=url)

		if r.status_code != r1.status_code:
			print "{status1} returned for {url} the first time, but {status} was returned the second time.".format(status=r.status_code, url=url, status1=r1.status_code)
			inconsistencies[url] = {'status': r.status_code, 'status1': r1.status_code}
	except requests.exceptions.ConnectionError as e:
		if "certificate verify failed" in str(e):
			error["cert"].append(url)
		elif "nodename nor servname provided, or not known" in str(e):
			error["offline"].append(url)
		elif "Connection refused" in str(e) and "https://" in url:
		 	# If the connection was refused, try again with http
		 	r3 = requests.get(url.replace("https://", "http://"), auth=(user, password))
		 	if rprint "The URL {url} could not be reached by https, but was OK when trying with HTTP.".format(url)
				inconsistencies[url] = {'status': r.status_code, 'status1': r3.status_code}
		 	else:
		 		error['unknown'].append(url)
		 	#diagnose_url(url, success, redirect, error, inconsistencies, authentication)
		else:
			print "Issue resolving {url}".format(url=url)
			print "[{e}]".format(e=e)
			error["unknown"].append(url)

if __name__ == '__main__':
	deploy_env = "production"
	user=os.environ.get("JENKINS_SERVICE_USERNAME")
	password=os.environ.get("JENKINS_SERVICE_PASSWORD")
	success = []
	redirect = []
	error = {403 : [], 500: [], 503: [], 504: [], 'cert': [], 'offline': [], 'unknown': []}
	inconsistencies = {}
	authentication = []
	regex = re.compile("<title>(?P<title>.*)</title>[\s\S]*<h1>(?P<message>.*)</h1>")
	count = 1
	for url in get_urls(deploy_env=deploy_env):
		message = ""
		title = ""
		count += 1
		# if count == 6:
		# 	break
		diagnose_url(url, success, redirect, error, inconsistencies, authentication)

	print "\nRECAP:"
	print "\nSites that are fine:"
	print "\t"+"\n\t".join(success)

	print "\nSites that returned different error codes from the 1st request to the 2nd request:"
	print "\tURL\tFirst Status\tSecond Status"
	for url, result in inconsistencies.items():
		print "\t{url}\t{status}\t{status1}".format(url=url, status=result['status'], status1=result['status1'])

	print "\nSites with 403 codes (probably deleted but need to be cleaned from the proxy layer)"
	print "\t"+"\n\t".join(error[403])

	print "\nSites with 500 codes: (probably need repair or deletion)"
	print "\t"+"\n\t".join(error[500])

	print "\nSites with 503 codes: (probably need repair or deletion)"
	print "\t"+"\n\t".join(error[503])

	print "\nSites with 504 codes: (probably need repair or deletion)"
	print "\t"+"\n\t".join(error[504])

	print "\nOffline sites:"
	print "\t"+"\n\t".join(error['offline'])

	print "\nSites with certificate errors:"
	print "\t"+"\n\t".join(error['cert'])

	print "\nSites with unknown errors:"
	print "\t"+"\n\t".join(error['unknown'])










