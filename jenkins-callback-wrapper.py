#!/usr/bin/python
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.custom_exceptions import JenkinsAPIException
from jenkinsapi.constants import STATUS_SUCCESS
import click
import os
import requests

@click.command()
@click.option('--environment', prompt='Environment', help='Environment e.g. production, staging')
@click.option('--chef-action', prompt='Chef action', help='e.g. update, backup')
def trigger_web_jobs(environment, chef_action):
    """
    Trigger a mass web job based on environment
    :param environment - Which environment would you like to try executing this job on?
    :param 
    """
    jenkins_url = 'https://leroy.nmdev.us'

    print "Connecting to Jenkins"
    try:
        # Preumably username / password will come back as a ConfigMap.
        J = Jenkins(jenkins_url, username=os.environ.get('JENKINS_GUEST_USERNAME'), password=os.environ.get('JENKINS_GUEST_PASSWORD'))
        print "Connection successful"
    except requests.exceptions.ConnectionError as e:
        print "Could not establish connection to Jenkins server at {jenkins_url}".format(jenkins_url=jenkins_url)
        exit(1)

    print "Fetching list of jobs to be run:"
    jenkins_job_list = J.get_jobs_list()
    print "Looking for jobs that contain '{environment}'".format(environment=environment)
    for job_name in jenkins_job_list:
        if environment in job_name:
            job = J.get_job(job_name)
            # Set build parameters, kick off a new build, and block until complete.
            params = {'name': job_name, 'CHEF_ACTION': chef_action }
            # Block so the jobs execute one-at-a-time
            qi = job.invoke(build_params=params, block=True)
            #build = qi.get_build()

    # Determine if the job already exists on this jenkins instance. If not, clone
    # a new job from the 'sitepack' seed job so each build has it's own history.



    # # Check for success and return a build.
    # if build.get_status() == STATUS_SUCCESS:
    #     build_number = build.get_number()
    #     print "BUILD {number} OF {job} WAS SUCCESSFUL".format(number=build_number, job=job_name)
    #     return True
    # else:
    #     print "THERE WAS AN ERROR WITH THE BUILD OF {job}".format(job=job_name)

if __name__ == '__main__':
    trigger_web_jobs()