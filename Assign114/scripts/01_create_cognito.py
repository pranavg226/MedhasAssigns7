"""Create a Cognito user pool + M2M client = the scoped identity that may call the Gateway."""
import boto3
from common import REGION, save_env

c = boto3.client("cognito-idp", region_name=REGION)
pool = c.create_user_pool(PoolName="agentcore-demo-pool")["UserPool"]["Id"]
domain = f"agentcore-demo-{pool.split('_')[1].lower()}"
c.create_user_pool_domain(Domain=domain, UserPoolId=pool)
c.create_resource_server(UserPoolId=pool, Identifier="agentcore-demo", Name="demo",
                         Scopes=[{"ScopeName": "invoke", "ScopeDescription": "Invoke gateway tools"}])
cl = c.create_user_pool_client(
    UserPoolId=pool, ClientName="agent-m2m", GenerateSecret=True,
    AllowedOAuthFlows=["client_credentials"], AllowedOAuthScopes=["agentcore-demo/invoke"],
    AllowedOAuthFlowsUserPoolClient=True)["UserPoolClient"]
save_env(COGNITO_POOL_ID=pool, COGNITO_CLIENT_ID=cl["ClientId"], COGNITO_CLIENT_SECRET=cl["ClientSecret"],
         COGNITO_DOMAIN=f"https://{domain}.auth.{REGION}.amazoncognito.com",
         COGNITO_DISCOVERY_URL=f"https://cognito-idp.{REGION}.amazonaws.com/{pool}/.well-known/openid-configuration")
print("Cognito ready:", pool)
