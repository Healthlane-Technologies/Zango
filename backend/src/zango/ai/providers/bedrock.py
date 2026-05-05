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

    @classmethod
    def fetch_models(cls, config: dict) -> list[dict]:
        """
        Fetch ON_DEMAND text-generation models from AWS Bedrock using the
        supplied credentials. Raises a descriptive error on auth failure.
        """
        try:
            import boto3

            from botocore.exceptions import ClientError, NoCredentialsError
        except ImportError as e:
            raise ValueError("boto3 is not installed. Run: pip install boto3") from e

        try:
            bedrock_client = boto3.client(
                "bedrock",
                aws_access_key_id=config["aws_access_key_id"],
                aws_secret_access_key=config["aws_secret_access_key"],
                region_name=config.get("aws_region", "us-east-1"),
            )
            response = bedrock_client.list_foundation_models(
                byOutputModality="TEXT",
                byInferenceType="ON_DEMAND",
            )
        except NoCredentialsError as e:
            raise ValueError(
                "Invalid AWS credentials. Check your Access Key ID and Secret Access Key."
            ) from e
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in (
                "UnauthorizedException",
                "AccessDeniedException",
                "InvalidClientTokenId",
                "UnrecognizedClientException",
                "InvalidSignatureException",
                "AuthFailure",
            ):
                raise ValueError(
                    f"Invalid AWS credentials or permissions denied ({code}). "
                    "Check your Access Key ID, Secret Access Key, and IAM permissions for Bedrock."
                ) from e
            raise ValueError(f"AWS Bedrock error: {e}") from e
        except Exception as e:
            raise ValueError(f"Could not connect to AWS Bedrock: {e}") from e

        models = []
        for m in response.get("modelSummaries", []):
            models.append(
                {
                    "id": m["modelId"],
                    "name": m.get("modelName", m["modelId"]),
                    "context_window": 200000,
                    "max_output_tokens": 8192,
                    "input_cost_per_mtok": None,
                    "output_cost_per_mtok": None,
                    "supports_tools": "TEXT" in m.get("outputModalities", []),
                    "supports_vision": "IMAGE" in m.get("inputModalities", []),
                    "supports_streaming": m.get("responseStreamingSupported", False),
                }
            )
        return models

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
