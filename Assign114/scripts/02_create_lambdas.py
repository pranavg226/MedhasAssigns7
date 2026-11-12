"""Package and create the two tool Lambdas. Needs LAMBDA_ROLE_ARN in .env."""
import io
import os
import zipfile

import boto3
from common import REGION, save_env

lam = boto3.client("lambda", region_name=REGION)
role = os.environ["LAMBDA_ROLE_ARN"]
out = {}
for name in ("lookup_customer", "send_notification"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.write(f"tools/{name}/handler.py", "handler.py")
    fn = f"agentcore-demo-{name}"
    try:
        arn = lam.create_function(FunctionName=fn, Runtime="python3.12", Role=role, Handler="handler.lambda_handler",
                                  Code={"ZipFile": buf.getvalue()})["FunctionArn"]
    except lam.exceptions.ResourceConflictException:
        arn = lam.update_function_code(FunctionName=fn, ZipFile=buf.getvalue())["FunctionArn"]
    out[f"LAMBDA_{name.upper()}_ARN"] = arn
    print(name, arn)
save_env(**out)
