aws --region ap-south-1 secretsmanager get-secret-value --secret-id zango-test-secret --query SecretString --output text > /mnt/config/.env
