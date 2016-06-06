#!/usr/bin/python
#from jenkinsapi.jenkins import Jenkins
#from jenkinsapi.custom_exceptions import JenkinsAPIException
#from jenkinsapi.constants import STATUS_SUCCESS
import jenkins
import jenkinspoll
import click
import os
import requests

@click.command()
@click.option('--environment', prompt='Environment', help='Environment e.g. production, staging')
@click.option('--chef-action', prompt='Chef action', help='e.g. update, backup', type=click.Choice(['update', 'delete', 'backup']))
@click.option('--bag-name', default=None, help="If set, will only trigger the job on the single bag specified")
def trigger_web_jobs(environment, chef_action, bag_name):
    """
    Trigger a mass web job based on environment
    :param environment - Which environment would you like to try executing this job on?
    :param chef_action - What would you like to perform on this environment?
    :param bag_name - Optional - what bag woud you specifically like to work on in this environment?
    """
    jenkins_url = 'https://leroy.nmdev.us'

    print "Connecting to Jenkins..."
    try:
        # Preumably username / password will come back as a ConfigMap.
        J = jenkins.Jenkins(jenkins_url, username=os.environ.get('JENKINS_SERVICE_USERNAME'), password=os.environ.get('JENKINS_SERVICE_PASSWORD'))
        print "Connection successful"
    except jenkins.JenkinsException as e:
        print "Could not establish connection to Jenkins server at {jenkins_url}".format(jenkins_url=jenkins_url)
        exit(1)

    jenkins_job_list = J.get_jobs()
    jenkins_job_list = [str(x["name"]) for x in jenkins_job_list]
    if bag_name is not None:
        job_name = "{environment}-{bag_name}".format(environment=environment, bag_name=bag_name)
        # Make sure the job exists
        if job_name not in jenkins_job_list:
            print "Job '{job_name}' could not be found in the jenkins job list. Available jobs are:\n\t{jobs}".format(job_name=job_name,jobs=",".join(jenkins_job_list))
            exit(1)
        # Set build parameters, kick off a new build, and block until complete.
        params = {'CHEF_ACTION': chef_action }
        # Block so the jobs execute one-at-a-time
        try:
            print "Invoking job {job_name}...".format(job_name=job_name)
            J.build_job(job_name, params)
            jenkinspoll.wait_for_job_to_finish(job_name, jenkins_connection=J)
            print "Done!"
            exit(0)
        except Exception as e:
            print e
            exit(1)
    else:
        print "Looking for jobs that contain '{environment}'".format(environment=environment)
        for job_name in jenkins_job_list:
            if job_name != "" and job_name != "{environment}-".format(environment=environment) and job_name.startswith(environment) and "drud" not in job_name:
                print "Invoking {job_name}".format(job_name=job_name)
                # Set build parameters, kick off a new build, and block until complete.
                params = {'name': job_name, 'CHEF_ACTION': chef_action }
                # Block so the jobs execute one-at-a-time
                try:
                    J.build_job(job_name, params)
                    jenkinspoll.wait_for_job_to_finish(job_name, jenkins_connection=J)
                except Exception as e:
                    print e


    # Determine if the job already exists on this jenkins instance. If not, clone
    # a new job from the 'sitepack' seed job so each build has it's own history.

if __name__ == '__main__':
    trigger_web_jobs()