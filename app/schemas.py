from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str


class LLMOutput(BaseModel):
    summary: str
    top_findings: list[str] = Field(default_factory=list)
    recommendation: list[str] = Field(default_factory=list)
    data_confidence: str = "low"
    rag_sources: list[str] = Field(default_factory=list)


class AskResponse(BaseModel):
    question: str
    mapped_analysis: str
    status: str
    message: str
    agent_trace: list[str] = Field(default_factory=list)
    rows: list[dict] = Field(default_factory=list)
    llm_output: LLMOutput | None = None


class BriefingSection(BaseModel):
    analysis_type: str
    label: str
    status: str
    summary: str
    top_findings: list[str] = Field(default_factory=list)
    recommendation: list[str] = Field(default_factory=list)
    row_count: int = 0
    data_confidence: str | None = None
    rag_sources: list[str] = Field(default_factory=list)


class BriefingResponse(BaseModel):
    status: str
    message: str
    executive_summary: str = ""
    sections: list[BriefingSection] = Field(default_factory=list)
    agent_trace: list[str] = Field(default_factory=list)


class DailyReportEntry(BaseModel):
    generated_at: str
    date: str
    executive_summary: str
    sections: list[BriefingSection] = Field(default_factory=list)


class DailyReportResponse(BaseModel):
    status: str
    message: str
    latest: DailyReportEntry | None = None
    history: list[DailyReportEntry] = Field(default_factory=list)


class IngestResponse(BaseModel):
    status: str
    message: str
    ingested_chunks: int = 0
    docs: list[str] = Field(default_factory=list)


class UploadPreviewResponse(BaseModel):
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[str] = Field(default_factory=list)
    sample: list[dict] = Field(default_factory=list)


class UploadResponse(BaseModel):
    status: str
    message: str
    table: str
    total_rows: int
    valid_rows: int = 0
    invalid_rows: int = 0
    inserted_rows: int = 0
    errors: list[str] = Field(default_factory=list)
