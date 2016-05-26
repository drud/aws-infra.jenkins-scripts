import time
import requests
import os
import jenkins
import threading
import signal
import atexit

jenkins_server = None
threading_event = None
jenkins_jobs_run = []

def main():
    global threading_event
    initialize_jenkins()
    threading_event = threading.Event()
    jenkins_poll = threading.Thread(target=get_current_jenkins_builds)
    jenkins_poll.start()
    time.sleep(4*60*60)
    # Signal jenkins poll to stop
    threading_event.set()
    jenkins_poll.join()
    print "All jobs run"
    print jenkins_jobs_run

def initialize_jenkins():
    global jenkins_server
    jenkins_url = 'https://leroy.nmdev.us'

    print "Connecting to Jenkins"
    try:
        # Preumably username / password will come back as a ConfigMap.
        jenkins_server = jenkins.Jenkins(jenkins_url, username=os.environ.get('JENKINS_SERVICE_USERNAME'), password=os.environ.get('JENKINS_SERVICE_PASSWORD'))
        print "Connection successful"
    except requests.exceptions.ConnectionError as e:
        print "Could not establish connection to Jenkins server at {jenkins_url}".format(jenkins_url=jenkins_url)
        exit(1)

def get_current_jenkins_builds():
    global jenkins_jobs_run
    print "Running builds:"
    while not threading_event.is_set():
        running_builds = jenkins_server.get_running_builds()
        running_build_names = [x['name'] for x in running_builds]
        #print running_build_names
        # Union of the 2 sets allows you to merge non-duplicates
        jenkins_jobs_run = list(set(jenkins_jobs_run) | set(running_build_names))
        print "Current running list: {jobs}".format(jobs=",".join(jenkins_jobs_run))
        time.sleep(10)

def shut_it_down(signal, frame):
    print "Shutting it down... (Wait 10 seconds)"
    global threading_event
    threading_event.set()
    print "Current running list: {jobs}".format(jobs=",".join(jenkins_jobs_run))
    exit()

def wait_for_job_to_finish(job_name, jenkins_connection=None, wait_time=10):
    if jenkins_connection == None:
        print "Initializing jenkins connection"
        initialize_jenkins()
        jenkins_connection = jenkins_server
    else:
        running_builds = jenkins_connection.get_running_builds()
    # Preset the running_build_names array so that it enters the loop
    running_build_names = [job_name]
    while job_name in running_build_names:
        time.sleep(wait_time)
        running_builds = jenkins_connection.get_running_builds()
        running_build_names = [x['name'] for x in running_builds]
    return True


if __name__ == '__main__':
    signal.signal(signal.SIGINT, shut_it_down)
    main()