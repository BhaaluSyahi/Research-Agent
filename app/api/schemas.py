"""Pydantic models for the API layer."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
