# Architecture note

**Pattern:** agents-as-tools. An orchestrator agent owns the conversation and delegates customer work to a specialist agent; only the specialist holds enterprise tools. This limits tool exposure and keeps orchestration logic separate from tool use.

**Model:** Claude Sonnet 4.5 via Bedrock (`us-east-1` cross-region inference profile), swappable by `MODEL_ID`.

**Runtime:** `BedrockAgentCoreApp` entrypoint, deployed to AgentCore Runtime; each `runtimeSessionId` gets an isolated microVM session.

**Tools:** Two Lambdas (customer lookup, notification) registered as Gateway targets, exposed as MCP tools. Data is mocked; swap handlers for DynamoDB/CRM/SES.

**Identity:** Gateway uses a custom JWT authorizer (Cognito). The agent authenticates with an M2M client restricted to the `agentcore-demo/invoke` scope, and the Gateway reaches Lambdas with its own IAM role. No long-lived AWS keys in code.

**Memory:** Each turn is written as an event keyed by `actor_id` + `session_id`; a semantic strategy extracts long-term facts per actor. Memory failures degrade gracefully.

**Observability:** OTel traces to CloudWatch GenAI Observability/X-Ray, plus JSON start/end logs per invocation.

**Trade-offs:** Mock data and one environment; client-credentials identity is per-agent, not per-end-user (use 3LO/user JWT passthrough for that).

**Testing status:** The AWS path is written but was not deployed (account restrictions). `agents/mock_mode.py` runs the same flow offline with the real tool handlers, an in-memory stand-in for AgentCore Memory and trace-style JSON logs, so behaviour can be checked without AWS.
