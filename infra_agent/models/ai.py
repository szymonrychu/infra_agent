from typing import Callable, List

from pydantic import BaseModel


class OpenAIToolParameterProperty(BaseModel):
    type: str = "string"
    enum: List[str] | None = None
    description: str | None = None


class OpenAIToolParameter(BaseModel):
    type: str = "object"
    properties: dict[str, OpenAIToolParameterProperty] = {}
    required: List[str] = []


class OpenAIFunction(BaseModel):
    name: str
    description: str
    parameters: OpenAIToolParameter | None = None


class OpenAITool(BaseModel):
    type: str = "function"
    function: OpenAIFunction
    handler: Callable | None = None


class OpenAIFunctionCall(BaseModel):
    arguments: str
    name: str
    type: str = "function"


class OpenAIToolCall(BaseModel):
    type: str = "function"
    id: str
    function: OpenAIFunctionCall


class OpenAIMessage(BaseModel):
    role: str
    name: str | None = None
    content: str | None = None
    tool_calls: List[OpenAIToolCall] | None = None
    tool_call_id: str | None = None
