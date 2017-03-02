import proxy as proxy_lib
import requests
import os, sys
import re
import dns.resolver
import dns.query
import dns.zone
import boto
from boto import connect_route53
from boto.route53.record import ResourceRecordSets
from pprint import pformat as p
import logging

def recompute_proxy_data(nmdproxy, deploy_env):
    """
    The proxy layer is arranged so that when you are trying to
    find the information for a specific application, it is not
    predictably in the same place. nmdproxy[environment] works, 
    but X in nmdproxy[environment][X][apps] is not a predictable
    variable. This function takes the proxy data and reorganizes
    it into something more digestible by ansible Jinja2 templates
    """
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
                            proxy[app_name]['protocol'] = 'https' if 'ssl_force' in app else 'http'
                else:
                    print "Could not process {app}".format(app=pool_name)
    return proxy

def get_urls():
    # TODO - 
    nmdproxy = proxy_lib.get_proxy()
    proxy = recompute_proxy_data(nmdproxy, 'production')
    proxy.update(recompute_proxy_data(nmdproxy, 'staging'))
    for url, app in proxy.items():
        protocol = app['protocol']
        full_url = "{protocol}://{url}".format(protocol=protocol,url=url)
        yield full_url, len(proxy)

def pointed_at_us(url, r, r1):
    host = url.split("://")[1]
    answers = ['']
    # Do a dig!
    try:
        answers = dns.resolver.query(host, "CNAME")
    except dns.resolver.NXDOMAIN:
        logging.error("There were no CNAME records found for {host}".format(host=host))
    except dns.resolver.NoAnswer:
        logging.error("There were no CNAME records found for {host}".format(host=host))
    answer = str(answers[0])
    if answer in ["hosting.newmediadenver.com.", "hosting.nmdev.us.", "hosting.drud.com."]:
        return True
    else:
        logging.error("There was a CNAME record found for {host}, BUT it's is pointing to {answer}!".format(host=host, answer=str(answer)))

    # It could also be pointed at cloudflare - we have to DIG DEEPER (get it?)
    # Check for one of our standard headers
    if "X-Proxy-Host" in r.headers.keys() or "X-Proxy-Host" in r1.headers.keys():
        return True

    return False

def diagnose_url(url, success, redirect, error, inconsistencies, authentication):
    try:
        # Call the request twice in case a cache prime is needed
        r1 = requests.get(url, auth=(user, password))
        r = requests.get(url, auth=(user, password))
        if r.status_code != r1.status_code:
            logging.error("{status1} returned for {url} the first time, but {status} was returned the second time.".format(status=r.status_code, url=url, status1=r1.status_code))
            logging.debug(p(r.headers))
            inconsistencies[url] = {'status': r.status_code, 'status1': r1.status_code}
            return "inconsistent"
        if not pointed_at_us(url, r, r1):
            error['wrong_dns'].append(url)
            logging.error("The CNAME www record does not appear to be pointed at us for {url}".format(url=url))
            logging.debug(p(r.headers))
            return "wrong dns"
        if r.status_code == 200:
            success.append(url)
            #logging.info("Success returned for {url}")
            return "success"
        elif r.status_code == 301:
            logging.error("Unhandled redirect on {url} - the requests module *should* have followed this").format(url=url)
            logging.debug(p(r.headers))
            return "unhandled_redirect"
        elif r.status_code == 401:
            print "The credentials for {url} did not work. A 401 error was recieved. Please fix the credentials for the site.".format(url=url)
            logging.debug(p(r.headers))
            sys.exit("Discontinuing run as it could lock out a user account.")
        else:
            error[r.status_code].append(url)
            # If we can get an actual error message, let's do it
            matches = regex.search(r.text)
            if matches and matches.groupdict():
                message = matches.groupdict()['message'].replace("{status} ".format(status=r.status_code), "")
                title = matches.groupdict()['title'].replace("{status} ".format(status=r.status_code), "")
                logging.error("{url} returned {status} {title}: {message}".format(status=r.status_code, url=url, title=title, message=message))
                logging.debug(p(r.headers))
            else:
                logging.error("{url} returned {status}".format(status=r.status_code, url=url))
                logging.debug(p(r.headers))
    except requests.exceptions.ConnectionError as e:
        if "certificate verify failed" in str(e):
            error["cert"].append(url)
            logging.error("The cert file looks wrong on {url}.".format(url=url))
            logging.debug(p(repr(e)))
            return "bad cert"
        elif "nodename nor servname provided, or not known" in str(e):
            error["offline"].append(url)
            logging.error("Site is offline - 'name or service not known' on {url}".format(url=url))
            logging.debug(p(repr(e)))
            return "offline"
        elif "Connection refused" in str(e) and "https://" in url:
            # If the connection was refused, try again with http
            r3 = requests.get(url.replace("https://", "http://"), auth=(user, password))
            if r3.status_code == 200:
                logging.error("The URL {url} could not be reached by https, but was OK when trying with HTTP.".format(url))
                logging.debug(p(repr(e)))
                inconsistencies[url] = {'status': r.status_code, 'status1': r3.status_code}
                return "inconsistent"
            else:
                error['unknown'].append(url)
                logging.error("Unknown Error when resolving {url}".format(url=url))
                logging.debug(p(repr(e)))
                return "unknown"
            #diagnose_url(url, success, redirect, error, inconsistencies, authentication)
        elif "doesn't match":
            error["cert"].append(url)
            logging.error("The cert file looks wrong on {url}.".format(url=url))
            logging.debug(p(repr(e)))
            return "bad cert"
        elif "Name or service not known":
            error["offline"].append(url)
            logging.error("Site is offline - 'name or service not known' on {url}".format(url=url))
            logging.debug(p(repr(e)))
            return "offline"
        else:
            logging.error("Unknown Error when resolving {url}".format(url=url))
            logging.debug(p(repr(e)))
            error["unknown"].append(url)
            return "unknown"

if __name__ == '__main__':
    logging.basicConfig(filename='trace.log',level=logging.DEBUG)
    user=os.environ.get("GUEST_USER")
    password=os.environ.get("GUEST_PASSWORD")
    success = []
    redirect = []
    error = {403 : [], 500: [], 502: [], 503: [], 504: [], 'cert': [], 'offline': [], 'wrong_dns': [], 'unknown': []}
    inconsistencies = {}
    authentication = []
    regex = re.compile("<title>(?P<title>.*)</title>[\s\S]*<h1>(?P<message>.*)</h1>")
    count = 1
    for i, (url, total) in enumerate(get_urls()):
        # Bypass known problem URLS
        if url in ['https://leroy.nmdev.us', 'http://api.newmediadenver.com']:
            logging.debug("Bypassing check on known issue on {url}".format(url=url))
            continue
        message = ""
        title = ""
        count += 1
        # if count == 6:
        #   break
        ret_status = diagnose_url(url, success, redirect, error, inconsistencies, authentication)
        print "{perc:06.2f}%{count:>5}/{total:<5}{url:<44}{status:<15}".format(perc=(float(i)/float(total))*100,count=i,total=total,url=url,status=ret_status)

    print "\n------------------------------------------------------------"
    print "RECAP:"
    if len(inconsistencies) > 0:
        print "\nSites that returned different error codes from the 1st request to the 2nd request:"
        print "\tURL\tFirst Status\tSecond Status"
        for url, result in inconsistencies.items():
            print "\t{url}\t{status}\t{status1}".format(url=url, status=result['status'], status1=result['status1'])
    if len(error[403]) > 0:
        print "\nSites with 403 codes (probably deleted but need to be cleaned from the proxy layer)"
        print "\t"+"\n\t".join(error[403])
    if len(error[500]) > 0:
        print "\nSites with 500 codes: (probably need repair or deletion)"
        print "\t"+"\n\t".join(error[500])
    if len(error[502]) > 0:
        print "\nSites with 502 codes: (probably need repair or deletion)"
        print "\t"+"\n\t".join(error[502])
    if len(error[503]) > 0:
        print "\nSites with 503 codes: (probably need repair or deletion)"
        print "\t"+"\n\t".join(error[503])
    if len(error[504]) > 0:
        print "\nSites with 504 codes: (probably need repair or deletion)"
        print "\t"+"\n\t".join(error[504])
    if len(error['offline']) > 0:
        print "\nOffline sites:"
        print "\t"+"\n\t".join(error['offline'])
    if len(error['cert']) > 0:
        print "\nSites with certificate errors:"
        print "\t"+"\n\t".join(error['cert'])
    if len(error['wrong_dns']) > 0:
        print "\nSites with bad DNS errors: (These sites don't appear to be pointed at us correctly)"
        print "\t"+"\n\t".join(error['wrong_dns'])
    if len(error['unknown']) > 0:
        print "\nSites with unknown errors:"
        print "\t"+"\n\t".join(error['unknown'])
    if len(success) > 0:
        print "\n\n------------------------------------------------------------"
        print "And of course, all the sites that are fine:"
        print "\t"+"\n\t".join(success)

    print "\nA full trace including headers and errors can be found at file://{fpath}".format(pwd=os.path.join(os.getcwd(), 'trace.log'))









