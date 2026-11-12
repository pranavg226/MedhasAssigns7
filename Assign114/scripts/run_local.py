"""Run the whole flow offline (MOCK mode, no AWS needed):  python scripts/run_local.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
import mock_mode  # noqa: E402

SESSION = "local-demo-session"
for prompt in (
    "Look up customer C-1001 and email them that their ticket is resolved",
    "Remind that customer again about their open ticket, please notify them",
    "Look up customer C-9999",
):
    print(f"\n> {prompt}")
    print("<", mock_mode.invoke(prompt, session_id=SESSION))
