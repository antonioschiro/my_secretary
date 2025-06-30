# Built-in libraries
import os
import base64
from email.message import EmailMessage

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
SCOPES = [os.getenv("SCOPES")]
USER_ID = os.getenv("USER_ID")

from pydantic import BaseModel, Field

# Import google libraries
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# MCP libraries
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.elicitation import (
                                    AcceptedElicitation,
                                    DeclinedElicitation,
                                    CancelledElicitation,
                                    )

# Loads google credentials
creds = Credentials.from_authorized_user_file("./servers/token.json", SCOPES)

mcp = FastMCP("Google services",
              host = "0.0.0.0",
              port = 8000,
            )

# TOOLS
@mcp.tool(title = "Get user info")
async def get_profile(user_id = USER_ID) -> dict:
    try:
        with build("gmail", "v1", credentials=creds) as gmail_service:
            user_info = gmail_service.users().getProfile(userId = user_id).execute()
    except HttpError as error:
        print(f"An HTTP error occurred while calling {get_profile.__name__}.")
        print(f"Details: \n {error}")
    return user_info

@mcp.tool(title = "Create draft")
async def create_draft( mail_content: str,
                        mail_subject: str,
                        mail_dest: str|None = None,
                        user_id = USER_ID,
                        ) -> dict:
    try:
        # Create message object
        message = EmailMessage()
        message.set_content(mail_content)
        message["Subject"] = mail_subject
        if mail_dest is not None:
            message["To"] = mail_dest
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"message": {"raw": encoded_message}}
        with build("gmail", "v1", credentials=creds) as gmail_service:
            draft = gmail_service.users().drafts().create(userId = user_id, body = body).execute()
    except HttpError as error:
        print(f"An HTTP error occurred while calling {create_draft.__name__}.")
        print(f"Details: \n {error}")
    except Exception as error:
        print(f"An exception occurred while calling {create_draft.__name__}.")
        print(f"Details: \n {error}")
    return draft

@mcp.tool(title = "Send message")
async def send_mail( 
                        mail_content: str,
                        mail_subject: str,
                        mail_dest: str,
                        user_id = USER_ID,
                        ) -> dict:

    try:
        # Create message object
        message = EmailMessage()
        message.set_content(mail_content)
        message["Subject"] = mail_subject
        message["To"] = mail_dest
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": encoded_message}
        
        # Send mail
        with build("gmail", "v1", credentials=creds) as gmail_service:
            mail = gmail_service.users().messages().send(userId = user_id, body = body).execute()

    except HttpError as error:
        print(f"An HTTP error occurred while calling {send_mail.__name__}.")
        print(f"Details: \n {error}")
    except Exception as error:
        print(f"An exception occurred while calling {send_mail.__name__}.")
        print(f"Details: \n {error}")
    return mail
    

@mcp.tool(title = "Send message")
async def send_mail_with_approval( 
                        context: Context,
                        mail_content: str,
                        mail_subject: str,
                        mail_dest: str,
                        user_id = USER_ID,
                        ) -> dict|str:
    class ConfirmOperation(BaseModel):
        confirm: bool = Field(description= "True or False depending whether if you confirm the mail.")
        notes: str = Field(description = "Additional notes.")
    try:
        # Create message object
        message = EmailMessage()
        message.set_content(mail_content)
        message["Subject"] = mail_subject
        message["To"] = mail_dest
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": encoded_message}

        
        user_response = await context.elicit(
                        message = f"""Do you want to send the mail with the following data? \n
                                Recipient: {message["To"]}\n
                                Subject: {message["Subject"]} \n
                                Content: {mail_content}
                                """,
                        schema = ConfirmOperation
        )
        
        # The following commented line of code mocks the case of user approval "OK".
        #user_response = AcceptedElicitation(action = "accept", data = ConfirmOperation(confirm = True, notes = "Nothing"))
        
        match user_response:
            case AcceptedElicitation(data = data):
                if data.confirm:
                # Send mail
                    with build("gmail", "v1", credentials=creds) as gmail_service:
                        mail = gmail_service.users().messages().send(userId = user_id, body = body).execute()
                else:
                    return "Mail not sent."
            case DeclinedElicitation() | CancelledElicitation():
                return "Mail not sent."

    except HttpError as error:
        print(f"An HTTP error occurred while calling {send_mail.__name__}.")
        print(f"Details: \n {error}")
    except Exception as error:
        print(f"An exception occurred while calling {send_mail.__name__}.")
        print(f"Details: \n {error}")
    return mail


if __name__ == "__main__":
    transport = "stdio"
    mcp.run(transport = transport)