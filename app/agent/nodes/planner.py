from app.agent.state import ChatState
from app.gateway.router import pick_tier

def plan_node(state:ChatState) -> dict:
    return {"tier":pick_tier(state["question"])}