#!ruby

require 'rubygems'
require 'chef/rest'
require 'chef/search/query'

Chef::Config.from_file(File.expand_path("/var/jenkins_home/workspace/jenkins-scripts/.chef/knife.rb"))
query = Chef::Search::Query.new
nodes = query.search('node', ARGV.shift).first rescue []

puts nodes.map(&:name).join("\n")
