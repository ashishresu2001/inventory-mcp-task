from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Inventory Service")

class InventoryChange(BaseModel):
    item: str
    change: int

class InventoryManager:
    def __init__(self):
        self.inventory = {"tshirts": 20, "pants": 15}

    def get_inventory(self):
        return self.inventory

    def modify_inventory(self, item, change):
        item = item.lower()
        if item not in self.inventory:
            raise ValueError("Invalid item")
        self.inventory[item] += change
        return self.inventory

manager = InventoryManager()

@app.get("/inventory")
def get_inventory():
    return manager.get_inventory()

@app.post("/inventory")
def modify_inventory(change: InventoryChange):
    try:
        return manager.modify_inventory(change.item, change.change)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
