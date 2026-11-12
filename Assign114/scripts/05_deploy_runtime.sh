#!/usr/bin/env bash
# Deploy the agent to AgentCore Runtime with the starter toolkit (builds container via CodeBuild).
set -euo pipefail
set -a; source .env; set +a
agentcore configure -e agents/orchestrator.py -n support_orchestrator -r "$AWS_REGION" \
  -rf requirements.txt --non-interactive
agentcore launch \
  --env AWS_REGION="$AWS_REGION" --env MODEL_ID="$MODEL_ID" --env GATEWAY_URL="$GATEWAY_URL" \
  --env MEMORY_ID="$MEMORY_ID" --env COGNITO_CLIENT_ID="$COGNITO_CLIENT_ID" \
  --env COGNITO_CLIENT_SECRET="$COGNITO_CLIENT_SECRET" --env COGNITO_DOMAIN="$COGNITO_DOMAIN"
