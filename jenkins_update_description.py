#!/usr/bin/python
import os
import requests
from jenkinsapi.jenkins import Jenkins
import click
import re

class JenkinsSlack(object):
  def __init__(self):
    self.job_name = ""
    self.job_config = ""
    self.job = None
    self.bag_name = ""
    self.jenkins_url = 'https://leroy.nmdev.us'
    self.jenkins_server = None
    self.env = ""


  def run(self):
    self.jenkins_server = Jenkins(self.jenkins_url, username = os.environ.get('JENKINS_SERVICE_USERNAME'), password = os.environ.get('JENKINS_SERVICE_PASSWORD'))
    jenkins_jobs = self.get_jenkins_jobs()
    #jobs[bag_name] = slack_channel
    jobs = {}
    for job in jenkins_jobs:
      if (job.startswith('production') or job.startswith('staging')) and job != "" and len(job) != 0:
        self.job_name = job
        self.job = self.jenkins_server.get_job(self.job_name)
        self.job_config = self.job.get_config()
        self.env, self.bag_name = job.split('-', 1)
        self.add_desc_to_jenkins()

  def get_jenkins_jobs(self):
    return self.jenkins_server.get_jobs_list()

  def add_desc_to_jenkins(self):
    description_tag = """<description></description>
  <keepDependencies>"""
    replace = """<description>Runs drud/drudfab against the {env} branch of the newmediadenver/{bag} GitHub project.</description>
  <keepDependencies>""".format(env=self.env,bag=self.bag_name)
    if description_tag in self.job_config:
      print "Adding description to {job}".format(job=self.job_name)
      #print self.job_config
      new_tag = self.job_config.replace(description_tag, replace)
      self.job.update_config(new_tag)
      #print new_tag
    return True    

if __name__ == '__main__':
  j = JenkinsSlack()
  j.run()