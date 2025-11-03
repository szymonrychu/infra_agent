from typing import Any, List

from pydantic import BaseModel

from infra_agent.models.ai import OpenAIMessage


class PromptSummary(BaseModel):
    data: dict[str, Any]
    messages: List[OpenAIMessage]
    resolved: bool


class CaseSummary(BaseModel):
    type: str = "case_summary"
    solved: bool
    explanation: str
    missing_tools: List[str] | None = None


class SuccessPromptSummary(BaseModel):
    type: str = "success"


class PromptToolErrorModel(BaseModel):
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

    def model_dump(self, *args, **kwargs) -> Any:
        return PromptToolErrorModel(
            tool_name=self.tool_name,
            error=str(self),
            inputs=self.inputs,
            exception=str(self.exception) if self.exception else None,
        ).model_dump(*args, **kwargs)
