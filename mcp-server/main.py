from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import json
import anthropic

app = FastAPI(title="MCP Server")

INVENTORY_API_URL = "http://localhost:8000/inventory"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class NLQuery(BaseModel):
    query: str

def llm_parse(query):
    # Build a prompt to tell Claude how to convert user queries to actions
    prompt = (
        "You are an assistant that converts inventory queries into JSON actions.\n"
        "Supported items: tshirts, pants.\n"
        "Supported actions: add, sold, get inventory.\n"
        "Examples:\n"
        "User: I sold 3 t shirts\n"
        "Action: {\"item\": \"tshirts\", \"change\": -3}\n"
        "User: Add 5 pants\n"
        "Action: {\"item\": \"pants\", \"change\": 5}\n"
        "User: How many pants and shirts do I have?\n"
        "Action: GET_INVENTORY\n"
        f"User: {query}\n"
        "Action:"
    )
    # Ask Claude to generate the action for the user's query
    response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=50,
        temperature=0,
        system="You are an assistant that converts inventory queries into JSON actions.",
        messages=[{"role": "user", "content": prompt}]
    )
    # Get the action part from Claude's response
    action = response.content[0].text.strip().split("Action:")[-1].strip()
    return action

@app.post("/mcp")
def handle_nl_query(nl: NLQuery):
    # Use Claude to turn the user's query into an action
    action = llm_parse(nl.query)
    # If the action is to get inventory, call the inventory service
    if action == "GET_INVENTORY":
        return requests.get(INVENTORY_API_URL).json()
    try:
        # Try to turn the action into a Python dictionary
        payload = json.loads(action)
        # Only allow tshirts and pants
        if payload.get("item") not in ["tshirts", "pants"]:
            raise HTTPException(status_code=400, detail=f"Unsupported item: {payload.get('item')}")
    except Exception:
        # If something goes wrong, send an error
        raise HTTPException(status_code=400, detail=f"LLM could not parse query or unsupported item: {action}")
    # Send the action to the inventory service and return the result
    return requests.post(INVENTORY_API_URL, json=payload).json()
