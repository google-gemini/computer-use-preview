"""Utility functions for AgentCore browser management."""

import json
import time
import hashlib
import termcolor


def create_recording_role(
    browser_identifier: str, recording_bucket: str, recording_prefix: str, region: str
) -> str:
    """Create IAM role scoped to recording bucket.

    Args:
        browser_identifier: Browser identifier (e.g., "aws.browser.v1")
        recording_bucket: S3 bucket name for recordings
        recording_prefix: S3 prefix for recordings
        region: AWS region

    Returns:
        ARN of the created or existing IAM role
    """
    import boto3

    # IAM is global, but STS should use the specified region
    iam = boto3.client("iam", region_name=region)
    sts = boto3.client("sts", region_name=region)
    account_id = sts.get_caller_identity()["Account"]

    # Role name uses hash of region/bucket/prefix for uniqueness
    role_hash = hashlib.md5(
        f"{region}/{recording_bucket}/{recording_prefix}".encode()
    ).hexdigest()
    role_name = f"AgentCoreBrowserRecording-{role_hash}"

    # Policy name uses same hash
    policy_name = f"S3RecordingAccess-{role_hash}"

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {"aws:SourceAccount": account_id},
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                    },
                },
            }
        ],
    }

    role_created = False
    try:
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for AgentCore browser recording",
        )
        role_created = True
        termcolor.cprint(f"Created IAM role: {role_name}", color="green")
    except iam.exceptions.EntityAlreadyExistsException:
        termcolor.cprint(f"Using existing IAM role: {role_name}", color="yellow")

    # Always ensure policy exists for this bucket/prefix
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:ListMultipartUploadParts",
                    "s3:AbortMultipartUpload",
                ],
                "Resource": f"arn:aws:s3:::{recording_bucket}/{recording_prefix}/*",
                "Condition": {"StringEquals": {"aws:ResourceAccount": account_id}},
            }
        ],
    }

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName=policy_name,
        PolicyDocument=json.dumps(permissions_policy),
    )

    if role_created:
        # Wait for IAM propagation
        termcolor.cprint("Waiting for IAM role to propagate...", color="yellow")
        time.sleep(10)

    return f"arn:aws:iam::{account_id}:role/{role_name}"


def get_or_create_browser(
    control_client,
    browser_name: str,
    execution_role_arn: str,
    region: str,
    recording_bucket: str = None,
    recording_prefix: str = "recordings",
) -> str:
    """Get existing browser or create new one with recording configured.

    Args:
        control_client: boto3 bedrock-agentcore-control client
        browser_name: Name for the browser resource
        execution_role_arn: IAM role ARN for browser execution
        region: AWS region for error messages and debugging
        recording_bucket: Optional S3 bucket for session recording
        recording_prefix: S3 prefix for recordings

    Returns:
        Browser ID (e.g., "br-xxxxx")
    """
    browser_id = None

    # Check for existing browser with same name
    try:
        next_token = None
        while True:
            list_params = {"maxResults": 100, "type": "CUSTOM"}
            if next_token:
                list_params["nextToken"] = next_token

            response = control_client.list_browsers(**list_params)
            browser_summaries = response.get("browserSummaries", [])

            for browser in browser_summaries:
                if browser.get("name") == browser_name:
                    status = browser.get("status", "")
                    browser_id = browser.get("browserId")
                    
                    if status in ["DELETING", "DELETE_FAILED"]:
                        browser_id = None
                        continue

                    termcolor.cprint(f"Found existing browser {browser_id}", color="cyan")
                    break

            if browser_id or "nextToken" not in response:
                break

            next_token = response["nextToken"]
    except Exception as e:
        termcolor.cprint(f"Error checking existing browsers: {e}", color="yellow")

    if not browser_id:
        try:
            create_params = {
                "name": browser_name,
                "networkConfiguration": {"networkMode": "PUBLIC"},
                "executionRoleArn": execution_role_arn,
                "browserSigning": {"enabled": True},
            }
            
            if recording_bucket:
                create_params["recording"] = {
                    "enabled": True,
                    "s3Location": {
                        "bucket": recording_bucket,
                        "prefix": recording_prefix.rstrip("/"),
                    },
                }
            
            response = control_client.create_browser(**create_params)
            browser_id = response["browserId"]
            termcolor.cprint(f"Created browser {browser_id}", color="green")
        except control_client.exceptions.ConflictException:
            raise ValueError(
                f"Browser '{browser_name}' already exists in region '{region}'.\n"
                f"This browser was likely created in a previous run but couldn't be found in list_browsers.\n\n"
                f"To resolve:\n"
                f"  1. Delete the existing browser via AWS Console or CLI:\n"
                f"     aws bedrock-agentcore-control delete-browser --browser-id <id> --region {region}\n"
                f"  2. Or use a different browser name by changing your recording configuration"
            )

    return browser_id


def setup_browser_recording(
    browser_name: str,
    browser_identifier: str,
    recording_bucket: str,
    recording_prefix: str,
    execution_role_arn: str | None,
    create_execution_role: bool,
    region: str,
) -> tuple[str, str]:
    """Set up browser recording configuration.

    Ensures execution role exists and browser is created with recording enabled.

    Args:
        browser_name: Name for the browser instance (must match [a-zA-Z][a-zA-Z0-9_]{0,47})
        browser_identifier: Browser identifier for sessions (e.g., "aws.browser.v1")
        recording_bucket: S3 bucket name for recordings
        recording_prefix: S3 prefix for recordings
        execution_role_arn: IAM role ARN (or None to create)
        create_execution_role: Whether to auto-create role if not provided
        region: AWS region

    Returns:
        Tuple of (execution_role_arn, browser_id) - The browser_id should be used as the identifier when starting sessions

    Raises:
        ValueError: If execution_role_arn is None and create_execution_role is False
    """
    import boto3

    if not execution_role_arn and not create_execution_role:
        raise ValueError(
            "execution_role_arn is required when using recording. "
            "Pass --execution_role_arn or use --create_execution_role to auto-create."
        )

    # Auto-create role if requested
    if create_execution_role and not execution_role_arn:
        execution_role_arn = create_recording_role(
            browser_identifier, recording_bucket, recording_prefix, region
        )

    # If browser_identifier is already a browser ID, reuse it
    if browser_identifier.startswith("br-"):
        termcolor.cprint(f"Using browser ID: {browser_identifier}", color="cyan")
        return execution_role_arn, browser_identifier
    
    control_client = boto3.client("bedrock-agentcore-control", region_name=region)
    browser_id = get_or_create_browser(
        control_client,
        browser_name,
        execution_role_arn,
        region,
        recording_bucket,
        recording_prefix,
    )

    return execution_role_arn, browser_id
