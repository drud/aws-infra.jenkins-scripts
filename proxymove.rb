require 'net/http'
require 'chef/rest'
require 'chef/config'
require 'chef/data_bag'
require 'chef/encrypted_data_bag_item'

bagname = 'encrypted'
appname = 'example'

environment = ARGV[2]
sitename = ARGV[3]
# Get just the subdomain of source/destination arguments
source = /^([^.]*)/.match(ARGV[4]).to_s
destination = /^([^.]*)/.match(ARGV[5]).to_s

# Use the same config as knife uses
Chef::Config.from_file("/var/jenkins_home/workspace/jenkins-chef-client/.chef/knife.rb")

# Get the encrypted data secret
secret = Chef::EncryptedDataBagItem.load_secret(ENV['NMDCHEF_SECRET_FILE'])

# Load the client data bag
client = Chef::EncryptedDataBagItem.load('nmdhosting', sitename, secret)
# Get the server_aliases values we need to move in proxy
aliases = client[environment]['server_aliases']

# Load the proxy data bag
item = Chef::EncryptedDataBagItem.load(bagname, appname, secret)
# Get the environment data we are altering
update = item[environment]

# Modify part of the data bag
aliases.each do |key|
  mover = update[source]['apps'][key]
  update[source]['apps'].delete(key)
  update[destination]['apps'][key] = mover
end

puts "Removed aliases from source"
puts update[source]['apps']
puts "Added aliases to destination"
puts update[destination]['apps']

# Construct a new data bag
bag_item = Chef::DataBagItem.new
bag_item.data_bag(bagname)
bag_item['id'] = appname
bag_item['_default'] = item['_default']
# Determine which environment we are altering in update
bag_item['staging'] = item['staging']
bag_item['staging'] = update unless environment != 'staging'
bag_item['production'] = item['production']
bag_item['production'] = update unless environment != 'production'

# Encrypt and save new data bag
enc_hash = Chef::EncryptedDataBagItem.encrypt_data_bag_item(bag_item, secret)
ebag_item = Chef::DataBagItem.from_hash(enc_hash)
ebag_item.data_bag(bagname)
ebag_item.save

exit 0
