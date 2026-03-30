"""
AWS Bedrock provider — stub implementation.
To be fully implemented when Bedrock support is needed.
"""

from zango.ai.providers.base import BaseLLMProvider
from zango.ai.providers.registry import register_provider


@register_provider("bedrock", "AWS Bedrock", icon="aws.svg")
class BedrockProvider(BaseLLMProvider):

    supported_models = []

    config_fields = [
        {
            "name": "aws_access_key_id",
            "type": "secret",
            "required": True,
            "label": "AWS Access Key ID",
        },
        {
            "name": "aws_secret_access_key",
            "type": "secret",
            "required": True,
            "label": "AWS Secret Access Key",
        },
        {
            "name": "aws_region",
            "type": "string",
            "required": True,
            "label": "AWS Region",
            "default": "us-east-1",
        },
    ]

    def complete(self, messages, model, **kwargs):
        raise NotImplementedError("Bedrock provider coming soon.")

    def stream(self, messages, model, **kwargs):
        raise NotImplementedError("Bedrock provider coming soon.")

    def validate_config(self):
        try:
            import boto3

            client = boto3.client(
                "bedrock-runtime",
                aws_access_key_id=self.config["aws_access_key_id"],
                aws_secret_access_key=self.config["aws_secret_access_key"],
                region_name=self.config.get("aws_region", "us-east-1"),
            )
            # Minimal check — list foundation models
            bedrock_client = boto3.client(
                "bedrock",
                aws_access_key_id=self.config["aws_access_key_id"],
                aws_secret_access_key=self.config["aws_secret_access_key"],
                region_name=self.config.get("aws_region", "us-east-1"),
            )
            bedrock_client.list_foundation_models(maxResults=1)
            return (True, None)
        except Exception as e:
            return (False, str(e))

    def get_models(self):
        return self.supported_models

    def estimate_tokens(self, text):
        return max(1, len(text) // 4)
