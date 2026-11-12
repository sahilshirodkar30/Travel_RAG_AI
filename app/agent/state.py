from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing import TypedDict,Annotated

class ChatState(TypedDict,total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    question:str
    tier:str      # fast or smart model is use , set by plaaner
    cached : bool  # true if ans comes from semantic cache
    chunks : list[dict] 
    answer: str
    needs_review:bool
    blocked:bool
    degraded:bool
    