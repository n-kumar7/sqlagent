#!/bin/bash
# Wait for postgres to become available on port 5432
echo "Waiting for postgres..."
while ! nc -z postgres 5432; do
  sleep 2
done
echo "Postgres is up."

# For debugging, display the contents of the API key file (CAUTION: remove for production)
if [ -f /app/config/api_key.txt ]; then
  echo "DEBUG: API key file content: $(cat /app/config/api_key.txt)"
  export OPENAI_API_KEY=$(cat /app/config/api_key.txt)
  echo "DEBUG: OPENAI_API_KEY is set to '$OPENAI_API_KEY'"
else
  echo "DEBUG: API key file not found."
fi

# Execute the original command passed to the container
exec "$@"
