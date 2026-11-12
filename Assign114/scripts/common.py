import os
import re

from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ENV_PATH)
REGION = os.environ.get("AWS_REGION", "us-east-1")


def save_env(**kv):
    """Upsert KEY=VALUE pairs into the gitignored .env file."""
    text = open(ENV_PATH).read() if os.path.exists(ENV_PATH) else ""
    for k, v in kv.items():
        if re.search(rf"^{k}=.*$", text, re.M):
            text = re.sub(rf"^{k}=.*$", f"{k}={v}", text, flags=re.M)
        else:
            text += f"\n{k}={v}"
        os.environ[k] = v
    open(ENV_PATH, "w").write(text.strip() + "\n")
