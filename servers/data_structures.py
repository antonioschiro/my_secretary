from pydantic import (BaseModel, 
                      Field,
                      EmailStr,
                      field_validator,
                      ValidationError,
                    )
from enum import Enum
from typing import (Optional,
                    List,
                    Union,
                    )

# INPUT DATA CLASSES
class MailState(str, Enum):
    unread = "unread"
    read = "read"
    starred = "starred"
    important = "important"

class SendMailInput(BaseModel):
    mail_content: str = Field(..., description= "The email body.")
    mail_subject: str = Field(..., description = "Email subject.")
    mail_dest: EmailStr = Field(..., description = "The recipient email address.")
    approval_flow: bool = Field(default = False, description = "Whether to request approval or not.")

class MailListInput(BaseModel):
    recipients: Optional[Union[str, List[str]]] = Field(default = None, description = "The recipients email address to filter.")
    mail_subject: Optional[str] = Field(default = None, description = "Email subject.")
    mail_state: Optional[MailState] = Field(default = None, description = "Mail state. It refers to 'is:' operator.")
    label: Optional[str] = Field(default = None, description= "The email tag(s).")
    folder: Optional[str] = Field(default="inbox", description= "The selected mail folder.")
    start_date: Optional[str] = Field(default = None, description = "The start date filter in YYYY/MM/DD.")
    end_date: Optional[str] = Field(default = None, description = "The end date filter in YYYY/MM/DD.")
    max_result: int = Field(default = 10, description = "Number of max results to retrieve.")
    include_spam_trash: bool = Field(default = False, description = "Whether to search in spam and trash folder or not.")
    
    class Config:
        use_enum_values = True

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            splitted_date = v.split("/")
            if len(splitted_date) == 3:
                for item, expected_len in zip(splitted_date, [4,2,2]):
                    if len(item) != expected_len:
                        raise ValidationError(f"""An error occurred while parsing {v}:\n
                                              Length of {item} should be equal to {expected_len}.
                                              Length found: {len(item)}""")
                return v
            raise ValidationError(f"{v} should be in YYYY/MM/DD format.")
        raise ValidationError(f"{v} should be a {str.__name__}. Found {type(v).__name__}")

# OTHER CLASSES
class ConfirmOperation(BaseModel):
    confirm: bool = Field(description= "True or False depending whether if you confirm the mail.")
    notes: str = Field(description = "Additional notes.")