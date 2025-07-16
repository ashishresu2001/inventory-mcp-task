from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import requests
import os
import json
import anthropic

app = FastAPI(
    title="MCP Server",
    description="GenAI-powered interface for inventory management. Converts natural language queries into inventory actions using Claude Opus 4.",
    version="1.0.0"
)

INVENTORY_API_URL = "http://localhost:8000/inventory"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class NLQuery(BaseModel):
    query: str = Field(..., example="I sold 3 t shirts", description="Natural language inventory query")

def llm_parse(query: str) -> str:
    
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
    response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=50,
        temperature=0,
        system="You are an assistant that converts inventory queries into JSON actions.",
        messages=[{"role": "user", "content": prompt}]
    )
    # Extract the action from Claude's response
    action = response.content[0].text.strip().split("Action:")[-1].strip()
    return action

@app.post(
    "/mcp",
    summary="Process natural language inventory query",
    response_description="Inventory state after action"
)
def handle_nl_query(nl: NLQuery):
    action = llm_parse(nl.query)
    if action == "GET_INVENTORY":
        return requests.get(INVENTORY_API_URL).json()
    try:
        payload = json.loads(action)
        # Only allow supported items
        if payload.get("item") not in ["tshirts", "pants"]:
            raise HTTPException(status_code=400, detail=f"Unsupported item: {payload.get('item')}")
    except Exception:
        raise HTTPException(status_code=400, detail=f"LLM could not parse query or unsupported item: {action}")
    return requests.post(INVENTORY_API_URL, json=payload).json()
