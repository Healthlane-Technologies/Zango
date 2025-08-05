#!/bin/bash

cd /zango

if [ -z "$AWS_SECRET_NAME" ]; then
    echo "AWS_SECRET_NAME not set. Skipping secret fetch."
    exit 0
fi

secretsJson=$(aws secretsmanager get-secret-value \
    --secret-id "${AWS_SECRET_NAME}" \
    --query SecretString \
    --region ap-south-1 \
    --output text 2>/dev/null)

if [ -z "$secretsJson" ]; then
    echo "Error: Failed to retrieve secret or secret is empty"
    exit 1
fi

echo "$secretsJson" | jq -r 'to_entries | map("\(.key)=\(.value)") | .[]' > .env

echo "Created .env file"
