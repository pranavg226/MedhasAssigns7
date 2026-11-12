"""Create AgentCore Memory (short-term events + long-term semantic facts)."""
import boto3
from common import REGION, save_env

ctl = boto3.client("bedrock-agentcore-control", region_name=REGION)
m = ctl.create_memory(
    name="agentcore_demo_memory", eventExpiryDuration=30,
    memoryStrategies=[{"semanticMemoryStrategy": {"name": "facts", "namespaces": ["/facts/{actorId}"]}}])
save_env(MEMORY_ID=m["memory"]["id"])
print("Memory:", m["memory"]["id"])
