"""LLM 对话与工具调用的请求/响应模型。"""
from typing import Any, Literal

from pydantic import BaseModel, Field


PlanStepKind = Literal["knowledge", "code", "html", "synthesize"]


class PlanStep(BaseModel):
    id: str = Field(..., description="步骤标识，如 1、2")
    kind: str = Field(..., description="knowledge | code | html | synthesize")
    goal: str = Field(..., description="该步要达成的自然语言目标")


class PlannerPlan(BaseModel):
    reasoning_summary: str = ""
    steps: list[PlanStep] = Field(default_factory=list)


ExecutionStepStatus = Literal["pending", "running", "done", "failed", "skipped"]


class ExecutionStepTrace(BaseModel):
    step_id: str
    kind: str
    status: ExecutionStepStatus
    summary: str = ""


class ChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant | system")
    content: str = ""


class ChatRequest(BaseModel):
    kb_id: int = Field(..., description="知识库 ID，用于工具检索")
    messages: list[ChatMessage] = Field(..., min_length=1)
    stream: bool = False


class PlannerDebugRequest(BaseModel):
    """仅调试 Planner：与完整 chat 解耦，不执行编排。"""

    messages: list[ChatMessage] = Field(..., min_length=1)
    include_fallback_preview: bool = Field(
        True, description="解析失败时是否再调意图路由，返回与线上一致的回退计划预览"
    )
    daytona_available: bool | None = Field(
        None, description="覆盖是否视为沙箱可用；默认与 DAYTONA_API_KEY 一致"
    )


class PlannerDebugResponse(BaseModel):
    model: str
    raw_content: str
    prompt_tokens: int
    completion_tokens: int
    used_json_object_mode: bool
    parse_ok: bool
    plan: PlannerPlan | None = None
    fallback_plan: PlannerPlan | None = None
    system_prompt_preview: str = ""
    invoke_error: str | None = None


class CitationChunk(BaseModel):
    """Agent 检索工具返回的片段，用于左侧预览高亮。"""
    chunk_text: str = ""
    source_id: str | None = None
    source_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    message: ChatMessage
    tool_calls: list[dict[str, Any]] | None = None
    citation_chunks: list[CitationChunk] | None = None
    intent: str | None = None  # "kb" | "code" | "html" | "multi"
    code_result: dict[str, Any] | None = None  # {code, language, exit_code, result}
    html_content: str | None = None
    plan_summary: str | None = None
    execution_trace: list[ExecutionStepTrace] | None = None


class UsageSegmentOut(BaseModel):
    """单次模型调用用量（编排调试）。"""

    request_type: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int = 0


class OrchestrateDebugResponse(BaseModel):
    """Planner + 完整编排调试：与线上一致，可选是否记账。"""

    plan: PlannerPlan
    chat_response: ChatResponse
    planner_prompt_tokens: int
    planner_completion_tokens: int
    orchestration_segments: list[UsageSegmentOut] = Field(default_factory=list)
