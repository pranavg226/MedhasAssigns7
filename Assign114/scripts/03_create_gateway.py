"""Create AgentCore Gateway (JWT-protected MCP endpoint) and register both Lambda tools."""
import json
import os

import boto3
from common import REGION, save_env

ctl = boto3.client("bedrock-agentcore-control", region_name=REGION)
gw = ctl.create_gateway(
    name="agentcore-demo-gateway", roleArn=os.environ["GATEWAY_ROLE_ARN"], protocolType="MCP",
    authorizerType="CUSTOM_JWT",
    authorizerConfiguration={"customJWTAuthorizer": {
        "discoveryUrl": os.environ["COGNITO_DISCOVERY_URL"],
        "allowedClients": [os.environ["COGNITO_CLIENT_ID"]]}})
gid = gw["gatewayId"]
schemas = {s["name"]: s for s in json.load(open("infra/tool_schemas.json"))}
for name in ("lookup_customer", "send_notification"):
    ctl.create_gateway_target(
        gatewayIdentifier=gid, name=name.replace("_", "-"),
        targetConfiguration={"mcp": {"lambda": {
            "lambdaArn": os.environ[f"LAMBDA_{name.upper()}_ARN"],
            "toolSchema": {"inlinePayload": [schemas[name]]}}}},
        credentialProviderConfigurations=[{"credentialProviderType": "GATEWAY_IAM_ROLE"}])
save_env(GATEWAY_ID=gid, GATEWAY_URL=gw["gatewayUrl"])
print("Gateway:", gw["gatewayUrl"])
