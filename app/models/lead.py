from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LeadCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    email: str
    phone: str | None = None
    company: str | None = None
    role: str | None = None
    source: str | None = None


class LeadBase(LeadCreate):
    score: int | None = None
    priority: str | None = None


class Lead(LeadBase):
    id: int
    created_at: datetime


class LeadProcessedData(LeadCreate):
    score: int
    priority: str


class LeadProcessResponse(BaseModel):
    message: str
    data: LeadProcessedData
