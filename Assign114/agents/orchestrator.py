"""Multi-agent support system running on AgentCore Runtime.

Orchestrator agent -> delegates customer questions to a Support specialist agent,
which calls enterprise tools (lookup_customer, send_notification) via AgentCore Gateway.
Memory: AgentCore Memory stores each turn per (actor_id, session_id) and recalls facts.
Identity: tools are called with a Cognito M2M JWT (scoped principal).
"""
import logging
import os

import requests
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}')
log = logging.getLogger("orchestrator")

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
GATEWAY_URL = os.environ["GATEWAY_URL"]
MEMORY_ID = os.environ["MEMORY_ID"]

app = BedrockAgentCoreApp()
memory = MemoryClient(region_name=REGION)
model = BedrockModel(model_id=MODEL_ID, region_name=REGION)


def gateway_token() -> str:
    """Identity: OAuth client-credentials token for the scoped gateway principal."""
    r = requests.post(
        f"{os.environ['COGNITO_DOMAIN']}/oauth2/token",
        data={"grant_type": "client_credentials", "scope": "agentcore-demo/invoke"},
        auth=(os.environ["COGNITO_CLIENT_ID"], os.environ["COGNITO_CLIENT_SECRET"]), timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def gateway_client() -> MCPClient:
    token = gateway_token()
    return MCPClient(lambda: streamablehttp_client(GATEWAY_URL, headers={"Authorization": f"Bearer {token}"}))


def recall(actor_id: str, session_id: str, query: str) -> str:
    """Short-term (this session's turns) + long-term (semantic facts) context."""
    lines = []
    try:
        for ev in memory.list_events(memory_id=MEMORY_ID, actor_id=actor_id, session_id=session_id, max_results=10):
            for m in ev.get("payload", []):
                c = m.get("conversational", {})
                lines.append(f"{c.get('role')}: {c.get('content', {}).get('text')}")
        facts = memory.retrieve_memories(memory_id=MEMORY_ID, namespace=f"/facts/{actor_id}", query=query, top_k=3)
        lines += [f"fact: {f['content']['text']}" for f in facts]
    except Exception as e:  # memory must never break the invocation
        log.warning("memory recall failed: %s", e)
    return "\n".join(lines)


@app.entrypoint
def invoke(payload, context):
    prompt = payload.get("prompt", "")
    actor_id = payload.get("actor_id", "anonymous")
    session_id = getattr(context, "session_id", None) or "default-session"
    log.info("invocation start actor=%s session=%s", actor_id, session_id)

    history = recall(actor_id, session_id, prompt)
    with gateway_client() as gw:
        tools = gw.list_tools_sync()
        specialist = Agent(
            model=model, tools=tools, callback_handler=None,
            system_prompt="You are a customer-support specialist. Use lookup_customer to find records "
                          "and send_notification to message customers. Never invent customer data.")

        @tool
        def support_specialist(request: str) -> str:
            """Handle a customer-support request that needs customer data or notifications."""
            return str(specialist(request))

        orchestrator = Agent(
            model=model, tools=[support_specialist], callback_handler=None,
            system_prompt="You are an orchestrator. Delegate anything about customers to support_specialist, "
                          "then give the user a concise final answer. Prior context:\n" + history)
        answer = str(orchestrator(prompt))

    try:
        memory.create_event(memory_id=MEMORY_ID, actor_id=actor_id, session_id=session_id,
                            messages=[(prompt, "USER"), (answer, "ASSISTANT")])
    except Exception as e:
        log.warning("memory write failed: %s", e)
    log.info("invocation end actor=%s session=%s chars=%d", actor_id, session_id, len(answer))
    return {"result": answer}


if __name__ == "__main__":
    app.run()
