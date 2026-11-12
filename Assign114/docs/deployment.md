# Real deployment (untested - see README status)

Prereqs: an AWS account on a paid plan where Lambda, Cognito, Bedrock and Bedrock AgentCore are allowed; Claude Sonnet 4.5 enabled in Bedrock (us-east-1); Python 3.12+; AWS CLI configured via SSO or `aws configure` (never commit keys).

## 1. Roles (once)
- **Lambda role** `agentcore-demo-lambda-role`: trust `lambda.amazonaws.com`, policy `AWSLambdaBasicExecutionRole`.
- **Gateway role** `agentcore-demo-gateway-role`: trust `bedrock-agentcore.amazonaws.com`, inline policy allowing `lambda:InvokeFunction` on `arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:agentcore-demo-*`.
- The Runtime execution role is created by `agentcore launch`.

## 2. Configure and create resources (run from repo root)
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env     # set LAMBDA_ROLE_ARN and GATEWAY_ROLE_ARN with your account ID
python scripts/01_create_cognito.py   # identity: Cognito M2M client
python scripts/02_create_lambdas.py   # the two tools
python scripts/03_create_gateway.py   # Gateway + both tools as MCP targets
python scripts/04_create_memory.py    # AgentCore Memory
./scripts/05_deploy_runtime.sh        # builds + deploys to AgentCore Runtime; prints the runtime ARN
```
## 3. Invoke (shows memory)
```bash
python scripts/06_invoke.py "Look up customer C-1001 and email them that their ticket is resolved" --arn <RUNTIME_ARN>
python scripts/06_invoke.py "Notify that customer again" --arn <RUNTIME_ARN> --session <session id printed above>
```
## 4. Observability
CloudWatch -> GenAI Observability -> Bedrock AgentCore: one trace per invocation (runtime -> model -> gateway tools). Logs: `/aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT` (`invocation start/end` lines) and the Lambda log groups. Save a screenshot as `docs/trace.png`.

## 5. Cleanup
Delete: the runtime (`agentcore destroy`), Gateway targets then the Gateway, the Memory, both Lambdas, the Cognito pool, and the IAM roles/access key. Set a $5 budget alert first.
