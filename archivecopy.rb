require 'net/http'
require 'chef/rest'
require 'chef/config'
require 'chef/data_bag'
require 'chef/encrypted_data_bag_item'

sitename = ARGV[4]
from = ARGV[5]
to = ARGV[6]

puts sitename
puts from
puts to

# Use the same config as knife uses
Chef::Config.from_file("/var/jenkins_home/workspace/jenkins-chef-client/.chef/knife.rb")

# Get the encrypted data secret
secret = Chef::EncryptedDataBagItem.load_secret(ENV['NMDCHEF_SECRET_FILE'])

# Load the aws data bag
aws = Chef::EncryptedDataBagItem.load('nmddrupal', 'aws', secret)[from]

s3args = {
  aws_access_key: aws['aws_access_key'],
  aws_secret_key: aws['aws_secret_key'],
  aws_bucket: aws['aws_bucket']
}
aws_auth = "-k #{s3args[:aws_access_key]} -sk #{s3args[:aws_secret_key]}"

latest = `./s3latest #{aws_auth} #{s3args[:aws_bucket]} #{sitename}/#{from}-#{sitename}-`.strip

puts latest

dest = latest.sub! from, to

puts dest

`./s3copy -np 8 -s 75 -f #{aws_auth} s3://#{s3args[:aws_bucket]}/#{latest} s3://#{s3args[:aws_bucket]}/#{dest}`

exit 0