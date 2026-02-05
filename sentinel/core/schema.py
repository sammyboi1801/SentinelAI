from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, Optional

class AgentAction(BaseModel):
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "ignore"