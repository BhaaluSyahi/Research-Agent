from pydantic import BaseModel

class RawSQSMessage(BaseModel):
    """Represents the raw SQS message envelope (not the request payload)."""
    message_id: str
    receipt_handle: str
    body: str
    attributes: dict = {}
