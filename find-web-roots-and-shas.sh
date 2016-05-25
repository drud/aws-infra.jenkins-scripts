# Find the SHA of the current site pointer
find /var/www -type l -name current -print -exec git --git-dir={}/.git rev-parse HEAD \;

# Trigger jenkins update for each job
  # Parse apart the file string - get the databag name
  # Parse apart the git remote -v - get the repo name

  # Trigger {env}-{databag} jenkins job

# Copy with rsync





web02 catch-up - done: staging-gradeem,staging-thestonecollection,staging-dig-smart,staging-ca
todo: staging-gretty