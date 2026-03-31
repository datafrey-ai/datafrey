from pydantic import BaseModel, ConfigDict, Field


class RunRequest(BaseModel):
    code: str = Field(min_length=1, max_length=16384)  # SQL / code to execute


class RunResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    output: str  # text result (rows, confirmation, etc.)
