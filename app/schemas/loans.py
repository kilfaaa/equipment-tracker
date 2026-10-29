from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class LoanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: int = Field(strict=True, gt=0, le=2147483647)
    equipment_id: int = Field(strict=True, gt=0, le=2147483647)


class LoanRead(BaseModel):
    id: int
    employee_id: int
    equipment_id: int
    issued_at: datetime
    returned_at: datetime | None
