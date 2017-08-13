# Download binary from CircleCI build
curl -o /bin/ghlabel https://42-99512752-gh.circle-artifacts.com/0/home/circleci/go/src/github.com/drud/ghlabel/bin/linux/ghlabel$CIRCLE_TOKEN

# Set permission to execute binary.
# Execute binary using Drud as our organization and community as our reference repository.
# (This is the actual sync)
chmod +x ./bin/ghlabel && ./bin/ghlabel --org=drud --ref=community -r

# Clean up
rm ./bin/ghlabel -f
