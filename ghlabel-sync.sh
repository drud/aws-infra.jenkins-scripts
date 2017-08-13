# Download binary from CircleCI build
curl -i https://circleci.com/api/v1.1/project/github/nmccrory/ghlabel/42/artifacts$CIRCLE_TOKEN | grep -o 'https://[^"]*' > artifacts.txt
<artifacts.txt xargs -P4 -I % wget %$CIRCLE_TOKEN

# TEMP: Print out a log of the filesystem
ls -l

# Set permission to execute binary
# Step 2: Execute binary using Drud as our organization and community as our reference repository.
chmod +x ./ghlabel$CIRCLE_TOKEN && ./ghlabel$CIRCLE_TOKEN --org=drud --ref=community -r
