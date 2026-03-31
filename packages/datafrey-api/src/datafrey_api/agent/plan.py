from pydantic import BaseModel, ConfigDict, Field


class PlanRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4096)


class PlanResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    plan: str  # natural-language query plan
