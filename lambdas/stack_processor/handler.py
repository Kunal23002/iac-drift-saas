"""
Stack Processor Lambda

Invoked async by the Orchestrator — one invocation per affected stack per batch run.
Receives all CloudTrail write events for a single stack, fetches the current CFn
template, calls the LLM to generate an updated template, then invokes the Validator.

# INTERIM: Currently using Google Gemini API for LLM calls.
# TODO: Replace Gemini with AWS Bedrock once the model is decided.
#       Remove: google-generativeai from requirements.txt
#               GEMINI_API_KEY_SECRET_ARN env var + IAM permission in Terraform
#               get_gemini_api_key() and invoke_gemini() functions below
#               Restore: invoke_bedrock() with the chosen Bedrock model ID
"""

import json
import logging
import os
import re

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sts_client = boto3.client("sts")
lambda_client = boto3.client("lambda")
secretsmanager = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")

RECONCILIATIONS_TABLE = os.environ["DYNAMODB_RECONCILIATIONS_TABLE"]
VALIDATOR_FUNCTION_NAME = os.environ["VALIDATOR_FUNCTION_NAME"]

# INTERIM: Gemini — remove when switching to Bedrock
GEMINI_API_KEY_SECRET_ARN = os.environ.get("GEMINI_API_KEY_SECRET_ARN", "")

_gemini_api_key_cache = None  # INTERIM


def lambda_handler(event, context):
    tenant = event["tenant"]
    stack_name = event["stack_name"]
    cloudtrail_events = event["cloudtrail_events"]
    tenant_id = tenant["tenant_id"]

    logger.info(
        "Processing stack=%s tenant=%s events=%d",
        stack_name, tenant_id, len(cloudtrail_events),
    )

    creds = assume_cross_account_role(tenant["role_arn"], tenant["external_id"], stack_name)
    region = cloudtrail_events[0].get("awsRegion", "us-east-1")
    cfn_template = fetch_cfn_template(creds, stack_name, region)

    updated_template = invoke_gemini(cfn_template, cloudtrail_events)  # INTERIM: swap for invoke_bedrock()

    invoke_validator(tenant, stack_name, cloudtrail_events[0], updated_template, cfn_template)


def assume_cross_account_role(role_arn, external_id, session_name):
    resp = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=f"drift-{session_name[:32]}",
        ExternalId=external_id,
        DurationSeconds=3600,
    )
    return resp["Credentials"]


def fetch_cfn_template(creds, stack_name, region):
    cfn = boto3.client(
        "cloudformation",
        region_name=region,
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )
    resp = cfn.get_template(StackName=stack_name, TemplateStage="Original")
    return resp["TemplateBody"]


# ── INTERIM: Gemini integration ───────────────────────────────────────────────
# TODO: Delete this entire section and replace the invoke_gemini() call in
#       lambda_handler() with invoke_bedrock() once Bedrock model is decided.

def get_gemini_api_key():
    global _gemini_api_key_cache
    if _gemini_api_key_cache:
        return _gemini_api_key_cache
    resp = secretsmanager.get_secret_value(SecretId=GEMINI_API_KEY_SECRET_ARN)
    secret = json.loads(resp["SecretString"])
    _gemini_api_key_cache = secret["api_key"]
    return _gemini_api_key_cache


def invoke_gemini(cfn_template, cloudtrail_events):
    """INTERIM: Call Gemini to generate updated CFn template. Replace with invoke_bedrock()."""
    from google import genai

    client = genai.Client(api_key=get_gemini_api_key())

    template_str = (
        cfn_template if isinstance(cfn_template, str)
        else json.dumps(cfn_template, indent=2)
    )
    events_str = json.dumps(cloudtrail_events, indent=2, default=str)

    prompt = (
        "You are a CloudFormation expert. An engineer made manual changes to AWS resources "
        "outside of CloudFormation.\n\n"
        f"Here is the current CloudFormation template:\n{template_str}\n\n"
        f"Here are the CloudTrail events describing what was manually changed:\n{events_str}\n\n"
        "Return an updated CloudFormation YAML template that reflects these manual changes so "
        "the declared state matches the actual infrastructure state. "
        "Return ONLY the raw YAML — no explanation, no markdown code fences, no commentary."
    )

    logger.info("Calling Gemini for stack template update (INTERIM)")
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    raw = response.text.strip()

    # Strip markdown code fences if Gemini wraps the output anyway
    raw = re.sub(r"^```(?:yaml|json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE)
    return raw.strip()

# ── End INTERIM Gemini section ─────────────────────────────────────────────────


def invoke_validator(tenant, stack_name, cloudtrail_event, updated_template, original_template):
    payload = {
        "tenant_id": tenant["tenant_id"],
        "event_id": cloudtrail_event["eventID"],
        "stack_name": stack_name,
        "updated_template": updated_template,
        "original_template": original_template,
        "cloudtrail_event": cloudtrail_event,
        "github_repo": tenant.get("github_repo", ""),
        "retry_count": 0,
    }
    lambda_client.invoke(
        FunctionName=VALIDATOR_FUNCTION_NAME,
        InvocationType="Event",
        Payload=json.dumps(payload),
    )
