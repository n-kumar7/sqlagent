#!/bin/bash
# If the API key file exists, set the OPENAI_API_KEY environment variable
if [ -f /app/config/api_key.txt ]; then
  export OPENAI_API_KEY=$(cat /app/config/api_key.txt)
fi

# Execute the original command passed to the container
exec "$@"
