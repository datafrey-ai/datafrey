from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: EmailStr
    name: str


class StatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    user: UserInfo
    databases_count: int = Field(ge=0)
    mcp_enabled: bool
