"""
Input Validation Schemas
========================
Pydantic schemas for validating API inputs
"""

from pydantic import BaseModel, field_validator, EmailStr, Field
from typing import Optional, Annotated
from datetime import datetime, timezone


class TeamCreate(BaseModel):
    """Schema for creating a new team"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Team name cannot be empty or whitespace")
        return v.strip()


class TeamUpdate(BaseModel):
    """Schema for updating a team"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("Team name cannot be empty or whitespace")
        return v.strip() if v else v


class MemberCreate(BaseModel):
    """Schema for creating a new team member"""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    team_id: Annotated[int, Field(gt=0)]
    role: Optional[str] = Field(None, max_length=50)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Member name cannot be empty or whitespace")
        return v.strip()


class CommunicationCreate(BaseModel):
    """Schema for creating a communication record"""

    sender_id: Annotated[int, Field(gt=0)]
    receiver_id: Optional[Annotated[int, Field(gt=0)]] = None
    team_id: Annotated[int, Field(gt=0)]
    communication_type: str
    duration_minutes: Optional[Annotated[float, Field(ge=0, le=480)]] = None  # Max 8 hours
    is_group: bool = False
    is_cross_team: bool = False
    message_content: Optional[str] = Field(None, max_length=5000)
    context: Optional[str] = Field(None, max_length=50)
    external_team_id: Optional[Annotated[int, Field(gt=0)]] = None

    @field_validator("communication_type")
    @classmethod
    def validate_type(cls, v):
        valid_types = ["face-to-face", "email", "chat", "meeting", "video-call", "phone", "other"]
        if v not in valid_types:
            raise ValueError(
                f'Invalid communication type. Must be one of: {", ".join(valid_types)}'
            )
        return v

    @field_validator("receiver_id")
    @classmethod
    def validate_sender_receiver_different(cls, v, info):
        if v and "sender_id" in info.data and v == info.data["sender_id"]:
            raise ValueError("Sender and receiver must be different people")
        return v

    @field_validator("is_group")
    @classmethod
    def validate_group_consistency(cls, v, info):
        if v and "receiver_id" in info.data and info.data["receiver_id"]:
            raise ValueError("Group communication cannot have a specific receiver")
        return v

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        if v:
            valid_contexts = [
                "standup",
                "1:1",
                "planning",
                "review",
                "brainstorm",
                "feedback",
                "social",
                "training",
                "other",
            ]
            if v not in valid_contexts:
                raise ValueError(f'Invalid context. Must be one of: {", ".join(valid_contexts)}')
        return v


class CommunicationBulkCreate(BaseModel):
    """Schema for bulk creating communications"""

    communications: Annotated[list[CommunicationCreate], Field(min_length=1, max_length=1000)]


class MetricsCalculate(BaseModel):
    """Schema for calculating metrics"""

    days: Optional[Annotated[int, Field(ge=1, le=365)]] = 30
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("start_date")
    @classmethod
    def start_not_future(cls, v):
        if v and v > datetime.now(timezone.utc):
            raise ValueError("start_date cannot be in the future")
        return v

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if v and v > datetime.now(timezone.utc):
            raise ValueError("end_date cannot be in the future")
        if v and "start_date" in info.data and info.data["start_date"]:
            if v < info.data["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v


class NetworkAnalysisParams(BaseModel):
    """Schema for network analysis parameters"""

    days: Optional[Annotated[int, Field(ge=1, le=365)]] = 30


# Export validation function
def validate_request(schema_class, data: dict):
    """
    Validate request data against a schema

    Returns:
        Tuple of (validated_data, error_dict)
        If valid: (data, None)
        If invalid: (None, errors)
    """
    try:
        validated = schema_class(**data)
        return validated, None
    except Exception as e:
        if hasattr(e, "errors"):
            return None, e.errors()
        return None, [{"msg": str(e)}]
