# Download binary from CircleCI build
curl -o ghlabel https://42-99512752-gh.circle-artifacts.com/0/home/circleci/go/src/github.com/drud/ghlabel/bin/linux/ghlabel$CIRCLE_TOKEN

# TEMP: Print out a log of the filesystem
ls -l

# Set permission to execute binary
# Step 2: Execute binary using Drud as our organization and community as our reference repository.
chmod +x ./ghlabel && ./ghlabel --org=drud --ref=community -r
