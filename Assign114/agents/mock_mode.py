"""Offline mock of the orchestrator -> specialist -> Gateway-tools flow.

No AWS, no model calls: a tiny rule-based "model" decides which tool to call. It runs the real tool
handlers from tools/, keeps session memory in-process, and emits trace-style JSON log lines, so the
flow (and the memory/observability behaviour) can be demonstrated without a deployed account.
It is NOT the production path - the real agent is agents/orchestrator.py.
"""
import json
import os
import re
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools.lookup_customer.handler import lambda_handler as lookup_customer  # noqa: E402
from tools.send_notification.handler import lambda_handler as send_notification  # noqa: E402

TOOLS = {"lookup_customer": lookup_customer, "send_notification": send_notification}


class InMemoryMemory:
    """Stands in for AgentCore Memory: events per (actor, session) + last-customer fact per actor."""

    def __init__(self):
        self.events, self.facts = {}, {}

    def list_events(self, actor, session):
        return self.events.get((actor, session), [])

    def add_turn(self, actor, session, prompt, answer):
        self.events.setdefault((actor, session), []).append({"user": prompt, "assistant": answer})

    def remember_customer(self, actor, customer):
        self.facts[actor] = customer


MEMORY = InMemoryMemory()


class Trace:
    """Emits one JSON line per span, sharing a trace_id (mimics what OTel shows in CloudWatch)."""

    def __init__(self, out=sys.stdout):
        self.trace_id, self.out = uuid.uuid4().hex, out

    def span(self, name, **attrs):
        self.out.write(json.dumps({"trace_id": self.trace_id, "span": name, "ts": round(time.time(), 3), **attrs}) + "\n")


def _call_tool(trace, name, args):
    start = time.time()
    result = TOOLS[name](args)  # same event shape the Gateway sends to Lambda
    trace.span(f"gateway.tool.{name}", args=args, ms=round((time.time() - start) * 1000, 2))
    return result


def specialist(trace, request, memory_customer):
    """Support specialist: picks tools by simple rules, like the LLM would pick by reasoning."""
    m = re.search(r"\bC-\d+\b", request, re.I)
    customer = None
    if m or memory_customer:
        cid = m.group(0) if m else memory_customer["id"]
        r = _call_tool(trace, "lookup_customer", {"customer_id": cid})
        if not r["found"]:
            return f"I couldn't find a customer with id {cid.upper()}."
        customer = r["customer"]
    if not customer:
        return "Please give me a customer id such as C-1001."
    answer = (f"{customer['name']} ({customer['id']}) is a {customer['tier']} customer "
              f"with {customer['open_tickets']} open ticket(s).")
    if re.search(r"\b(email|notify|message|tell)\b", request, re.I):
        n = _call_tool(trace, "send_notification", {
            "recipient_email": customer["email"], "subject": "Update from support",
            "message": f"Hi {customer['name'].split()[0]}, {request.strip()}"})
        answer += f" Notification sent (id {n['notification_id'][:8]})." if n["sent"] else " Notification failed."
    MEMORY.remember_customer(request_actor.get(), customer)
    return answer


class _Actor:  # tiny holder so specialist() can store the fact for the current actor
    _v = "anonymous"

    def set(self, v):
        self._v = v

    def get(self):
        return self._v


request_actor = _Actor()


def invoke(prompt, actor_id="user-demo", session_id="local-session", out=sys.stdout):
    trace = Trace(out)
    request_actor.set(actor_id)
    trace.span("runtime.invoke", actor=actor_id, session=session_id, mode="MOCK")
    history = MEMORY.list_events(actor_id, session_id)
    trace.span("memory.recall", turns=len(history))
    remembered = MEMORY.facts.get(actor_id)
    use_memory = bool(history) and bool(re.search(r"\b(that|same|him|her|they|just asked)\b", prompt, re.I))
    trace.span("orchestrator.delegate", to="support_specialist", used_memory=use_memory)
    answer = specialist(trace, prompt, remembered if use_memory else None)
    MEMORY.add_turn(actor_id, session_id, prompt, answer)
    trace.span("runtime.done", chars=len(answer))
    return answer
