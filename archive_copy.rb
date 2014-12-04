require 'aws-sdk'
require 'base64'
args = Hash[ ARGV.flat_map{|s| s.scan(/--?([^=\s]+)(?:=(\S+))?/) } ]
AWS.config({
  :access_key_id => args['aws_access_key'], 
  :secret_access_key => args['aws_secret_key']
})
utf_key = args['aws_utf_symmetric_key']
symmetric_key = Base64.decode64(utf_key).encode('ascii-8bit')

# Find the latest from file
s3 = AWS::S3.new
latest = nil
objects = s3.buckets[args['bucket']].objects
objects.with_prefix("#{args['sitename']}/#{args['from']}-").each do |o|
  latest = o
end
raise "There is no file to copy from." if latest.nil?

# Can only do an object copy if file size is less than 5gb.
puts latest.inspect
if latest.content_length < 5000000000
  options = { 
    :server_side_encryption => :aes256,
    :client_side_encrypted => true
  }
else
  options = { 
    :server_side_encryption => :aes256,
    :use_multipart_copy => true,
    :content_length => latest.content_length,
    :client_side_encrypted => true,
    :content_type => 'application/x-gzip'
  }
end
puts "Copying #{latest.key} to #{latest.key.gsub(args['from'], args['to'])}"
objects[latest.key.gsub(args['from'], args['to'])].copy_from(latest.key, options) 

difference = objects.with_prefix("#{args['sitename']}/#{args['from']}-").count - args['aws_s3_backups'].to_i
if difference > 0
  i = 0
  objects.with_prefix("#{args['sitename']}/#{args['from']}-").each do |obj|
    obj.delete if i < difference
    i +=1
  end
end
