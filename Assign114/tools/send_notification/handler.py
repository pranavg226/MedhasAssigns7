"""Gateway tool: send a notification (mock; logs to CloudWatch, optional SNS)."""
import json
import os
import uuid

import boto3

TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")  # optional; unset = log only


def lambda_handler(event, context=None):
    event = event or {}
    to = event.get("recipient_email")
    subject = event.get("subject")
    message = event.get("message")
    if not (to and subject and message):
        return {"sent": False, "error": "recipient_email, subject and message are required"}
    nid = str(uuid.uuid4())
    if TOPIC_ARN:
        boto3.client("sns").publish(TopicArn=TOPIC_ARN, Subject=subject[:100], Message=f"To: {to}\n\n{message}")
    print(json.dumps({"tool": "send_notification", "notification_id": nid, "to": to, "subject": subject}))
    return {"sent": True, "notification_id": nid}
