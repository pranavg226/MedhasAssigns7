import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools.lookup_customer.handler import lambda_handler as lookup
from tools.send_notification.handler import lambda_handler as notify


def test_lookup_found():
    r = lookup({"customer_id": "c-1001"})
    assert r["found"] and r["customer"]["name"] == "Asha Rao"


def test_lookup_missing():
    assert not lookup({"customer_id": "nope"})["found"]


def test_notify_ok():
    r = notify({"recipient_email": "a@b.com", "subject": "Hi", "message": "x"})
    assert r["sent"] and r["notification_id"]


def test_notify_validation():
    assert not notify({"recipient_email": "a@b.com"})["sent"]


def test_mock_flow_uses_both_tools_and_memory():
    import io

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
    import mock_mode

    out = io.StringIO()
    a1 = mock_mode.invoke("Look up C-1001 and email them", actor_id="t", session_id="s1", out=out)
    assert "Asha Rao" in a1 and "Notification sent" in a1
    a2 = mock_mode.invoke("notify that customer again", actor_id="t", session_id="s1", out=out)
    assert "Asha Rao" in a2  # recalled from memory, no id given
    spans = out.getvalue()
    assert "gateway.tool.lookup_customer" in spans and "gateway.tool.send_notification" in spans
