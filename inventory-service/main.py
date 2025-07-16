from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Inventory Service")

# In-memory inventory store
inventory = {
    "tshirts": 20,
    "pants": 15
}

class InventoryChange(BaseModel):
    item: str
    change: int

@app.get("/inventory")
def get_inventory():
    return inventory

@app.post("/inventory")
def modify_inventory(change: InventoryChange):
    item = change.item.lower()
    if item not in inventory:
        raise HTTPException(status_code=400, detail="Invalid item")
    inventory[item] += change.change
    return inventory
