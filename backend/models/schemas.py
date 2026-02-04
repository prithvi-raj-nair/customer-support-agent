from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime


class User(BaseModel):
    user_id: str
    email: str
    name: str


class Order(BaseModel):
    order_id: str
    user_id: str
    product_name: str
    status: Literal["processing", "shipped", "out_for_delivery", "delivered", "cancelled"]
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[str] = None
    order_date: str
    total_amount: float


class EmailInput(BaseModel):
    sender_email: str = Field(..., description="Email address of the sender")
    subject: str = Field(..., description="Subject line of the email")
    body: str = Field(..., description="Body content of the email")


class EmailResponse(BaseModel):
    to_email: str
    subject: str
    body: str
    timestamp: str


class HumanQueueItem(BaseModel):
    id: str
    email_input: EmailInput
    reason: str
    timestamp: str
    resolved: bool = False


class GuardrailResult(BaseModel):
    passed: bool
    query_type: Literal["order_status", "other", "prompt_injection", "out_of_scope"]
    reason: str
    confidence: float = 0.0


class TraceStep(BaseModel):
    node: str
    timestamp: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    duration_ms: Optional[float] = None


class ProcessEmailRequest(BaseModel):
    sender_email: str
    subject: str
    body: str


class ProcessEmailResponse(BaseModel):
    success: bool
    response_email: Optional[EmailResponse] = None
    routed_to: str
    escalation_reason: Optional[str] = None
    trace: list[TraceStep]
    error: Optional[str] = None
