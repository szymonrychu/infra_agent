from typing import Callable, List

from pydantic import BaseModel, Field

from infra_agent.models.generic import InfraAgentBaseModel


class OpenAIToolParameterPropertyItems(InfraAgentBaseModel):
    type: str = "string"


class OpenAIToolParameterProperty(InfraAgentBaseModel):
    type: str = "string"
    enum: List[str] | None = None
    description: str | None = None
    items: OpenAIToolParameterPropertyItems | None = None
    additional_properties: dict[str, str] | None = Field(default=None, alias="additionalProperties")
    min_properties: int | None = Field(default=None, alias="minProperties")


class OpenAIToolParameter(InfraAgentBaseModel):
    type: str = "object"
    properties: dict[str, OpenAIToolParameterProperty] = {}
    required: List[str] = []


class OpenAIFunction(InfraAgentBaseModel):
    name: str
    description: str
    parameters: OpenAIToolParameter | None = None


class OpenAITool(InfraAgentBaseModel):
    type: str = "function"
    function: OpenAIFunction
    handler: Callable | None = Field(default=None, exclude=True)


class OpenAIToolGroup(InfraAgentBaseModel):
    name: str
    description_template: str
    tools: List[OpenAITool]

    def description(self):
        return self.description_template.format(tool_list=f"[{','.join([tool.function.name for tool in self.tools])}]")


class OpenAIFunctionCall(InfraAgentBaseModel):
    arguments: str
    name: str
    type: str = "function"


class OpenAIToolCall(InfraAgentBaseModel):
    type: str = "function"
    id: str
    function: OpenAIFunctionCall
    result: BaseModel | None = Field(default=None, exclude=True)


class OpenAIMessage(InfraAgentBaseModel):
    role: str
    name: str | None = None
    content: str | None = None
    tool_calls: List[OpenAIToolCall] | None = None
    tool_call_id: str | None = None
    tool_call_arguments: str | None = Field(default=None, exclude=True)


class OpenAICaseSummary(InfraAgentBaseModel):
    type: str = "case_summary"
    solved: bool
    explanation: str
    missing_tools: List[str] | None = None


class OpenAIPromptSummary(InfraAgentBaseModel):
    data: OpenAICaseSummary | None = None
    messages: List[OpenAIMessage]
    resolved: bool
