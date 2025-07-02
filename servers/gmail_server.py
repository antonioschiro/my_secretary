# Built-in libraries
import os
import asyncio
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
from utils import build_query
from data_structures import (SendMailInput,
                            MailListInput,
                            ConfirmOperation,
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
    
@mcp.tool(title = "Send message with approval")
async def send_mail(sendmail_input: SendMailInput,
                        context: Context,
                        user_id = USER_ID,
                            ) -> dict|str:

    try:
        # Create message object
        message = EmailMessage()
        message.set_content(sendmail_input.mail_content)
        message["Subject"] = sendmail_input.mail_subject
        message["To"] = sendmail_input.mail_dest
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": encoded_message}

        if sendmail_input.approval_flow:
            user_response = await context.elicit(
                            message = f"""Do you want to send the mail with the following data? \n
                                    Recipient: {message["To"]}\n
                                    Subject: {message["Subject"]} \n
                                    Content: {sendmail_input.mail_content}
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
    
        else:
            with build("gmail", "v1", credentials=creds) as gmail_service:
                mail = gmail_service.users().messages().send(userId = user_id, body = body).execute()

    except HttpError as error:
        print(f"An HTTP error occurred while calling {send_mail.__name__}.")
        print(f"Details: \n {error}")
    except Exception as error:
        print(f"An exception occurred while calling {send_mail.__name__}.")
        print(f"Details: \n {error}")
    return mail

@mcp.tool(title = "Get message")
async def get_mail_details(
                            mail_id: str,
                            user_id = USER_ID,
                            ) ->dict:
    try:
        with build("gmail", "v1", credentials=creds) as gmail_service:
            mail_details = gmail_service.users().messages().get(userId = user_id, 
                                                                id = mail_id,
                                                                format = "full",
                                                            ).execute()
        # Fetch subject and date fields
        for field in mail_details["payload"]["headers"]:
            if field["name"] == "Subject":
                mail_subject = field["value"]
            elif field["name"] == "Date":
                mail_date = field["value"].split("+")[0].strip()
        
        # Fetch email body
        if "data" in (path:= mail_details["payload"]["parts"][0]["body"]):
            mail_body = path["data"]
        else:
            mail_body = mail_details["payload"]["parts"][0]["parts"][0]["body"]["data"]
        
        mail_body += "=" * (-len(mail_body) % 4) # This check is needed since Gmail could omit "=".
        mail_body = base64.urlsafe_b64decode(mail_body).decode("utf-8")
    
    except HttpError as error:
        print(f"An HTTP error occurred while calling {get_mail_details.__name__}.")
        print(f"Details: \n {error}")
    except IndexError as error:
        print(f"An error occurred while fetching datas from mail during the execution of {get_mail_details.__name__}.")
        print(f"Details: \n {error}")
    except Exception as error:
        print(f"An exception occurred while calling {get_mail_details.__name__}.")
        print(f"Details: \n {error}")
       
    return {
            "mail_id": mail_id,
            "mail_subject": mail_subject,
            "mail_body": mail_body,
            "mail_date": mail_date,
            }

@mcp.tool(title = "Mail list")
async def get_mail_list(
                            mail_list_input: MailListInput,
                            user_id: str = USER_ID,
                        )-> dict:
    
    query = build_query(
                        recipients=mail_list_input.recipients,
                        mail_subject = mail_list_input.mail_subject,
                        start_date = mail_list_input.start_date,
                        end_date = mail_list_input.end_date,
                        mail_state = mail_list_input.mail_state,
                        folder = mail_list_input.folder,
                        label = mail_list_input.label,
                        )

    with build("gmail", "v1", credentials=creds) as gmail_service:
        mail_list = gmail_service.users().messages().list(userId = user_id, 
                                                        maxResults = mail_list_input.max_result,
                                                        includeSpamTrash = mail_list_input.include_spam_trash,
                                                        q = query,
                                                        ).execute()
    
    # Get mail details for each mail_id retrieved.
    tasks = {}
    try:
        async with asyncio.TaskGroup() as tg:
            for item in mail_list["messages"]:
                msg_id = item["id"]
                tasks[msg_id] = tg.create_task(get_mail_details(mail_id = msg_id))
    except* HttpError as eg:
        for error in eg.exceptions:
            print(error)
    except* Exception as eg:
        for error in eg.exceptions:
            print(error)

    mail_dict = {key: value.result() for key, value in tasks.items()}
    return mail_dict

if __name__ == "__main__":
    transport = "stdio"
    mcp.run(transport = transport)