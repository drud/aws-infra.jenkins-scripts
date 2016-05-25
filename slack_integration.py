#!/usr/bin/python
import os
import requests
from jenkinsapi.jenkins import Jenkins
import click
import re

slack_token = "xoxp-3793324342-27004929527-40807612819-67664ed1cb"

def create_slack_channel(channel_name):
  # TODO
  # Create slack channel
  # Channel names can only contain lowercase letters, numbers, hyphens, and underscores, and must be 21 characters or less.
  url = r"https://slack.com/api/channels.create"
  args = {
  "token": slack_token,
  "name": channel_name
  }
  r = requests.post(url, data=args)
  # Returns:
  # {
  #     "ok": true,
  #     "channel": {
  #         "id": "C024BE91L",
  #         "name": "fun",
  #         "created": 1360782804,
  #         "creator": "U024BE7LH",
  #         "is_archived": false,
  #         "is_member": true,
  #         "is_general": false,
  #         "last_read": "0000000000.000000",
  #         "latest": null,
  #         "unread_count": 0,
  #         "unread_count_display": 0,
  #         "members": [  ],
  #         "topic": {  },
  #         "purpose": {  }
  #     }
  # }
  if r.json()["ok"] == true:
    print "Created {channel} in Slack.".format(channel=channel_name)
    return True
  else:
    print "Unable to create {channel} in Slack. Response:\n{response}".format(channel=channel_name,response=r.json())
    return False

# Add jenkins integration
# For each jenkins job
# OR For each chat room

class JenkinsSlack(object):
  def __init__(self):
    self.job_name = ""
    self.job_config = ""
    self.job = None
    self.bag_name = ""
    self.slack_channel = ""
    self.jenkins_url = 'https://leroy.nmdev.us'
    self.jenkins_server = None


  def run(self):
    self.jenkins_server = Jenkins(self.jenkins_url, username = os.environ.get('JENKINS_GUEST_USERNAME'), password = os.environ.get('JENKINS_GUEST_PASSWORD'))
    self.match_channels_to_jobs()

  def get_slack_channels(self):
    # Get list of chat rooms from Slack
    url=r"https://slack.com/api/channels.list"
    args = {
      "token": slack_token,
      "exclude_archived": 1
    }
    r = requests.post(url, data=args)
    channels_with_id = [{"name":channel["name"],"id":channel["id"]} for channel in r.json()["channels"]]
    channels = [channel["name"].lower() for channel in r.json()["channels"]]
    return channels

  def job_defines_slack(self):
    if "SlackNotifier" in self.job_config:
      print "SlackNotifier already exists in {job}".format(job=self.job_name)
      slack_pos = self.job_config.find("SlackNotifier")
      room_pos = self.job_config.find("<room>#", slack_pos)
      end_room = self.job_config.find("</room>", room_pos)
      self.slack_channel = self.job_config[room_pos+7:end_room]
      if self.slack_channel == "" or len(self.slack_channel) == 0:
        print "Empty channel detected"
        return False
      else:
        self.bag_name = self.slack_channel
      return True
    else:
      print "Adding SlackNotifier to {job}".format(job=self.job_name)
      return False

  def get_jenkins_jobs(self):
    return self.jenkins_server.get_jobs_list()

  def add_slack_to_jenkins(self):
    # TODO - enable save back to Jenkins
    hipchat_close_tag = "</jenkins.plugins.hipchat.HipChatNotifier>"
    slack_tag = """<jenkins.plugins.slack.SlackNotifier plugin="slack@2.0.1">
          <teamDomain></teamDomain>
          <authToken></authToken>
          <buildServerUrl>https://leroy.nmdev.us/</buildServerUrl>
          <room>#%s</room>
          <startNotification>true</startNotification>
          <notifySuccess>true</notifySuccess>
          <notifyAborted>false</notifyAborted>
          <notifyNotBuilt>false</notifyNotBuilt>
          <notifyUnstable>false</notifyUnstable>
          <notifyFailure>true</notifyFailure>
          <notifyBackToNormal>false</notifyBackToNormal>
          <notifyRepeatedFailure>false</notifyRepeatedFailure>
          <includeTestSummary>false</includeTestSummary>
          <commitInfoChoice>AUTHORS_AND_TITLES</commitInfoChoice>
          <includeCustomMessage>false</includeCustomMessage>
          <customMessage></customMessage>
        </jenkins.plugins.slack.SlackNotifier>"""
    find = hipchat_close_tag
    channel_slack_tag = slack_tag % self.slack_channel
    replace = "{hipchat_close_tag}{slack_tag}".format(hipchat_close_tag=hipchat_close_tag,slack_tag=channel_slack_tag)

    if "SlackNotifier" not in self.job_config:
      print "Adding SlackNotifier to {job}".format(job=self.job_name)
      #print self.job_config
      new_tag = self.job_config.replace(find, replace)
      self.job.update_config(new_tag)
      #print new_tag
    elif "SlackNotifier" in self.job_config and self.slack_channel == "":
      print "SlackNotifier is in {job}. Replacing the hunk".format(job=self.job_name)
      find = slack_tag % ""
      replace = slack_tag % self.slack_channel
      self.job_config.replace(find, replace)
      return True
    return True

  def match_channels_to_jobs(self):
    jenkins_jobs = self.get_jenkins_jobs()
    #jobs[bag_name] = slack_channel
    jobs = {}
    for job in jenkins_jobs:
      self.slack_channel = ""
      if (job.startswith('production') or job.startswith('staging')) and job != "" and len(job) != 0:
        self.job_name = job
        self.job = self.jenkins_server.get_job(self.job_name)
        self.job_config = self.job.get_config()
        env, self.bag_name = job.split('-', 1)
        # If the job already has a slack definition
        if self.job_defines_slack():
          if self.slack_channel != "" and len(self.slack_channel)!=0 and self.bag_name != "" and len(self.bag_name)!=0:
            print "jobs['{bag}']='#{channel}'".format(bag=self.bag_name, channel=self.slack_channel)
            jobs[self.bag_name] = self.slack_channel
          continue
        elif self.slack_channel == "" or len(self.slack_channel)==0:
          print "Fixing empty Slack channel"

        # Found existing channel definition
        if self.bag_name in jobs:
          self.slack_channel = jobs[self.bag_name]
        else:
          self.slack_channel = self.match_channel_with_bag()
          jobs[self.bag_name] = self.slack_channel
        if self.slack_channel:
          if not self.add_slack_to_jenkins():
            print "Had an issue with attaching {job} to {slack_channel}".format(job=self.job_name, slack_channel=self.slack_channel)
          else:
            print "Attached {job} to #{slack_channel}".format(job=self.job_name, slack_channel=self.slack_channel)

  def match_channel_with_bag(self):
    """
    Given a bag name, try to figure out which slack channel it should go with.
    Returns the name of the slack channel or empty string
    """
    if self.bag_name == "" or len(self.bag_name) == 0:
      print "Empty bag detected. Skipping."
    slack_channels = self.get_slack_channels()
    possible_channels = []
    default_channel = "N"
    if self.bag_name.lower() in slack_channels:
      slack_channel = self.bag_name.lower()
    else:
      print "\nNo channels found matching '{job}/{bag}'".format(job=self.job_name, bag=self.bag_name)
      print "Other channels that start with the same letter:"
      for channel in slack_channels:
        if channel.startswith(self.bag_name[0]):
          possible_channels.append(channel)
          print "\t%s" % channel
          channel_initials = ''.join([x[0] for x in re.sub("[\-!_,]", '-', channel).split('-') if len(x)>0])
          channel_no_symbols = re.sub("[\-!_,]", '', channel)
          if self.bag_name == channel_initials:
            default_channel = channel
          elif self.bag_name == channel_no_symbols:
            default_channel = channel
          elif channel.startswith(self.bag_name):
            default_channel = channel
          elif self.bag_name in channel:
            default_channel = channel
          elif self.bag_name in channel_no_symbols:
            default_channel = channel
      possible_channels.append("N")
      possible_channels.append("O")
      self.slack_channel = click.prompt("Type a channel name for {bag} ('N' for None or 'O' for Other)".format(bag=self.bag_name),type=click.Choice(possible_channels),default=default_channel)
      if self.slack_channel == "N":
        print "Skipping {bag}".format(bag=self.bag_name)
        return None
      elif self.slack_channel == "O":
        self.slack_channel = click.prompt("Enter other channel name (no hashtag)")
    print "Matched #{channel} with {bag}.".format(channel=self.slack_channel,bag=self.bag_name)
    return self.slack_channel



def new_site():
  # New Site
  # Create Jenkins contact
  # Create Sendgrid contact
  # Create SSL certificate
  # Create JIRA project
  # Create Slack Channel
  # Integrate Slack + JIRA
  # Integrate Slack + Jenkins
  # Integrate Slack + GitHub
  return True

if __name__ == '__main__':
  j = JenkinsSlack()
  j.run()
