# Built-in libraries
import os
import asyncio
import base64
from email.message import EmailMessage

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
SCOPES = [os.getenv("GMAIL_SCOPE"), os.getenv("CALENDAR_SCOPE")]

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
                            EventListInput,
                            PostEventInput,
                            )
# Loads google credentials
creds = Credentials.from_authorized_user_file("./servers/token.json", SCOPES)

mcp = FastMCP("Google services",
              host = "0.0.0.0",
              port = 8000,
            )

user_id = "me"

# TOOLS
# MAIL TOOLS
@mcp.tool(title = "Get user info")
async def get_profile() -> dict|None:
    """
    Retrieves the Gmail account information.

    Returns:
        dict | None: The user's profile information as a dictionary or None if an error occurs.
    """
    user_info = None
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
                        ) -> dict|None:
    
    """
    Creates a draft email in the user's Gmail account.

    Parameters:
        mail_content (str): The body content of the email.
        mail_subject (str): The subject of the email.
        mail_dest (str | None, optional): The recipient's email address. If None, the draft will not have a recipient.

    Returns:
        dict | None: The created draft's details as a dictionary or None if an error occurs.
    """
    draft = None
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
                            ) -> dict|str| None:   
    """
    Sends an email message, optionally requiring user approval before sending.

    Parameters:
        sendmail_input (SendMailInput): The input data for the email (content, subject, recipient and approval flow).
        context (Context): The context for user interaction and approval.

    Returns:
        dict | str | None: The sent message's details as a dictionary, a string message if not sent or None if an error occurs.
    """    
    mail = None

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

# This is not exposed as tool, but it is called within get_mail_list()
async def get_mail_details(mail_id: str) ->dict:
    """
    Retrieves the details of a specific email message by its ID.

    Parameters:
        mail_id (str): The unique ID of the email message.

    Returns:
        dict: A dictionary containing the mail's ID, subject, body, and date.
    """

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
    except (IndexError, KeyError) as error:
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
                        )-> dict:
    """
    Retrieves email(s) matching the specified filters.

    Parameters:
        mail_list_input (MailListInput): a class containing all the filters and options for retrieving emails:
                                                recipients (str, optional): recipients email address(es) to filter.
                                                mail_subject (str, optional): email subject.
                                                mail_state (str, optional): mail state. It refers to 'is:' operator. Values accepted: "unread", "read", "starred", "important".
                                                label (str, optional): the email tag(s).
                                                folder (str, optional. Default is "inbox".): the selected mail folder. Values accepted: "inbox", "sent".
                                                start_date (str, optional): specifies the earliest date to include in the search results. Use the format: YYYY/MM/DD. (e.g. 2025/04/01)
                                                end_date (str, optional): specifies the earliest date to include in the search results. Use the format: YYYY/MM/DD. (e.g. 2025/04/02)
                                                max_result (int, default: 10): number of max results to retrieve. 
                                                include_spam_trash (bool, Default: False): whether to include spam and trash folders in search. 

    Returns:
        dict: A dictionary mapping mail IDs to their details.

    See MailListInput class for full field description.
    """

    mail_list = None
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

# CALENDAR TOOLS
@mcp.tool(title = "Get calendars list")
async def get_calendars()-> dict|None:
    """
    Retrieves the list of calendars for the authenticated user.

    Returns:
        dict | None: The list of calendars as a dictionary, or None if an error occurs.
    """
    calendars_list = None
    
    try:
        with build("calendar", "v3", credentials=creds) as calendar_service:
            calendars_list = calendar_service.calendarList().list().execute() 
    except HttpError as error:
        print(f"An HTTP error occurred while calling {get_calendars.__name__}.\nError: {error}")
    return calendars_list

@mcp.tool(title = "Get calendar info")
async def get_my_calendar(calendar_id: str = "primary")-> dict|None:
    """
    Retrieves details of a specific calendar.

    Parameters:
        calendar_id (str, optional): The calendar's ID. Defaults to "primary".

    Returns:
        dict | None: The calendar's details as a dictionary, or None if an error occurs.
    """
    my_calendar = None
    
    try:
        with build("calendar", "v3", credentials=creds) as calendar_service:
            my_calendar = calendar_service.calendarList().get(calendarId = calendar_id).execute() 
    except HttpError as error:
        print(f"An HTTP error occurred while calling {get_my_calendar.__name__}.\nError: {error}")
    return my_calendar

@mcp.tool(title = "Get events")
async def get_events(event_list: EventListInput, calendar_id: str = "primary")-> dict|None:

    """
    Retrieves event(s) filtered by the provided criteria from the calendar.

    Parameters:
        event_list (EventListInput):  a class containing all the filters and options for retrieving events:
                                            eventTypes (str. Default = "default"): the type of event(s) you want to search. 
                                                        Values accepted: "birthday", 
                                                                        "default", 
                                                                        "focusTime", 
                                                                        "fromGmail", 
                                                                        "outOfOffice", 
                                                                        "workingLocation".
                                            maxResults (int. Default = 10): the maximum number of events to retrieve from the search.
                                            timeMin (str, optional. Default = None): specifies the earliest date/time to include in the search results. Use the format: %Y-%m-%dT%H:%M:%SZ (e.g., 2025-07-07T14:30:00Z).
                                            timeMax (str, optional. Default = None): specifies the latest date/time to include in the search results. Use the format: %Y-%m-%dT%H:%M:%SZ (e.g., 2025-07-08T14:30:00Z).
        calendar_id (str, optional): The calendar's ID. Defaults to "primary".

    Returns:
        dict | None: The list of events as a dictionary, or None if an error occurs.
    """
    events = None
    # Filter out null attributes
    attrs_values = {key: value for key, value in event_list.__dict__.items() if value is not None}
    
    try:
        with build("calendar", "v3", credentials=creds) as calendar_service:
            events = calendar_service.events().list(calendarId = calendar_id,
                                                    **attrs_values,
                                                    ).execute()
    except HttpError as error:
        print(f"An HTTP error occurred while calling {get_events.__name__}.\nError: {error}")
    return events

@mcp.tool(title = "Create event")
async def post_event(post_event_input: PostEventInput, calendar_id: str = "primary") -> dict|None:
    """
    Create an event on the calendar with the provided start time and end date.

    Parameters:
    - post_event_input (PostEventInput): a class containing the start time and end date to be set for the event:
                                        start_time (str): the start date of the event. Use the format: %Y-%m-%dT%H:%M:%SZ (e.g., 2025-07-07T14:30:00Z).
                                        end_time (str): the end date of the event. Use the format: %Y-%m-%dT%H:%M:%SZ (e.g., 2025-07-07T15:30:00Z).
                                        attendees (list(str), optional. Default = None): the email(s) list of the attendees.
                                        summary (str, optional. Default = None): The title of the event. It is the event's name displayed on the calendar.

    Returns:
        dict | None:                                    

    """
    # Initialize body with mandatory fields.
    body = {
        "start": {
            "dateTime": post_event_input.start_time,
            },
        "end": {
            "dateTime": post_event_input.end_time,
            }
    }

    # Adding optional fields if they are provided.
    if post_event_input.attendees is not None: 
        attendees = [{"email": email} for email in post_event_input.attendees]
        body["attendees"] = attendees
    if (summary :=post_event_input.summary) is not None:
        body["summary"] = summary
    
    try:
        with build("calendar", "v3", credentials=creds) as calendar_service:
            event = calendar_service.events().insert(calendarId = calendar_id,
                                                    body = body,
                                                    ).execute()
    except HttpError as error:
            print(f"An HTTP error occurred while calling {post_event.__name__}.\nError: {error}")

    return event

if __name__ == "__main__":
    transport = "stdio"
    mcp.run(transport = transport)