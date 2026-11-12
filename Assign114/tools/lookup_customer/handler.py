"""Gateway tool: look up a customer record (mock enterprise CRM)."""
import json

CUSTOMERS = {
    "C-1001": {"id": "C-1001", "name": "Asha Rao", "email": "asha.rao@example.com", "tier": "gold", "open_tickets": 1},
    "C-1002": {"id": "C-1002", "name": "Liam Chen", "email": "liam.chen@example.com", "tier": "silver", "open_tickets": 0},
    "C-1003": {"id": "C-1003", "name": "Maria Lopez", "email": "maria.lopez@example.com", "tier": "bronze", "open_tickets": 3},
}


def lambda_handler(event, context=None):
    # AgentCore Gateway passes tool arguments directly as the event.
    cid = (event or {}).get("customer_id", "").strip().upper()
    record = CUSTOMERS.get(cid)
    if not record:
        return {"found": False, "error": f"No customer with id '{cid}'"}
    print(json.dumps({"tool": "lookup_customer", "customer_id": cid, "found": True}))
    return {"found": True, "customer": record}
