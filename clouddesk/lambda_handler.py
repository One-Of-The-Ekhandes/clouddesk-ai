"""AWS Lambda entry point: wraps the FastAPI app with Mangum.

The LLM API key is read once per cold start from SSM Parameter Store (SecureString),
so it never sits in plain text in the Lambda configuration.
"""
import os

from mangum import Mangum


def _load_secret_from_ssm() -> None:
    param = os.getenv("LLM_KEY_PARAM")
    provider = os.getenv("LLM_PROVIDER", "groq").upper()
    env_var = f"{provider}_API_KEY"
    if param and not os.getenv(env_var):
        import boto3
        value = boto3.client("ssm").get_parameter(Name=param, WithDecryption=True)["Parameter"]["Value"]
        os.environ[env_var] = value


_load_secret_from_ssm()

from clouddesk.api import app  # noqa: E402  (import after the key is in the environment)

handler = Mangum(app, lifespan="off")
