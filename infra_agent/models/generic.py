from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class InfraAgentBaseModel(BaseModel):
    """Base model with common configuration"""

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda dt: dt.isoformat() if dt else None},
    )


class SuccessPromptSummary(InfraAgentBaseModel):
    type: str = "success"


class PromptToolErrorModel(InfraAgentBaseModel):
    tool_name: str
    error: str
    inputs: dict[str, Any]
    exception: str | None = None


class PromptToolError(Exception):
    def __init__(
        self, message: str, tool_name: str, inputs: dict[str, Any], exception: Exception | None = None
    ) -> None:
        super().__init__(message)
        self.tool_name = tool_name
        self.inputs = inputs
        self.exception = exception

    def model(self) -> PromptToolErrorModel:
        return PromptToolErrorModel(
            tool_name=self.tool_name,
            error=str(self),
            inputs=self.inputs,
            exception=str(self.exception) if self.exception else None,
        )
