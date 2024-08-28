# check_env.sh
#!/bin/bash

if [ ! -f .env ]; then
  echo ".env file not found!"
  exit 1
fi
