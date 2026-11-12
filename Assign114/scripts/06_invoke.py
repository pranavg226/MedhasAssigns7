"""Invoke the deployed runtime. Reuse --session to demonstrate memory."""
import argparse
import json
import uuid

import boto3
from common import REGION

p = argparse.ArgumentParser()
p.add_argument("prompt")
p.add_argument("--session", default=str(uuid.uuid4()) + "-" + "x" * 8)  # session ids must be >=33 chars
p.add_argument("--actor", default="user-demo")
p.add_argument("--arn", required=True, help="Agent runtime ARN printed by `agentcore launch`")
a = p.parse_args()
r = boto3.client("bedrock-agentcore", region_name=REGION).invoke_agent_runtime(
    agentRuntimeArn=a.arn, runtimeSessionId=a.session,
    payload=json.dumps({"prompt": a.prompt, "actor_id": a.actor}).encode())
print("session:", a.session)
print(r["response"].read().decode())
