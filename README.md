# My Secretary [WORK IN PROGRESS 🛠️]

"My Secretary" is a Python project that provides a conversational assistant for Gmail and Google Calendar, powered by Google APIs, LangChain, LangGraph and MCP. It enables you to automate email and calendar tasks, interact with language models and use a web frontend for chat-based interaction.

## Features

- Authenticate and connect to Gmail and Google Calendar using OAuth2.
- Retrieve user profile information.
- Create email drafts and send emails programmatically.
- List, read and filter emails with advanced queries.
- List calendars and retrieve events with filters.
- Create calendar events with custom details.
- Integrate with Gemini LLM via LangChain and LangGraph.
- Modular MCP server exposing tools for LLM agents.
- Web frontend for chat-based interaction.

## Project Structure

```
main.py                      # FastAPI backend and websocket/chat frontend
servers/
  gmail_server.py            # MCP server exposing Gmail and Calendar tools
  gmail_quickstart.py        # Script to generate/update Google credentials
  credentials.json           # Google OAuth2 credentials
  token.json                 # User access/refresh tokens
  mcp_config.json            # MCP server configuration
  data_structures.py         # Pydantic models for tool inputs
  utils.py                   # Utility functions (e.g., query builder)
frontend/
  static/
    style.css                # Web chat CSS styles
    assistant.js             # Web chat JS logic
  templates/
    main_page.html           # Jinja2 template for chat UI
graph.py                     # LangGraph agent graph definition
prompts.py                   # Prompt templates for LLM agent
.env                         # Environment variables (not committed)
pyproject.toml               # Project dependencies and metadata
README.md                    # Project documentation
```

## Setup

1. **Clone the repository** and navigate to the project directory.

2. **Install dependencies** (Python 3.12 recommended):

   ```sh
   uv pip install -r requirements.txt
   ```

3. **Set up environment variables**  
   Create a `.env` file with the following variables:

   ```
   SCOPES=https://mail.google.com/
   CALENDAR_SCOPE=https://www.googleapis.com/auth/calendar
   USER_ID=me
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Google API Credentials**  
   - Place your `credentials.json` in the `servers/` directory.
   - Run the quickstart script to generate `token.json`:

     ```sh
     uv run servers/gmail_quickstart.py
     ```

5. **Configure MCP**  
   - Edit `servers/mcp_config.json` with your MCP server details if needed.

## Usage

- **Start the Gmail MCP server:**

  ```sh
  uv run servers/gmail_server.py
  ```

- **Start the assistant agent (FastAPI backend + frontend):**

  ```sh
  uv run main.py
  ```

- **Access the web chat UI:**  
  Open [http://localhost:8000](http://localhost:8000) in your browser.

## Notes

- The project uses [LangChain](https://github.com/langchain-ai/langchain), [LangGraph](https://github.com/langchain-ai/langgraph) and [MCP](https://github.com/microsoft/mcp).
- Make sure your Google Cloud project has Gmail and Calendar APIs enabled.
- Do not commit your `.env`, `token.json`, or other sensitive files.
- For Gemini LLM, ensure your API key is valid and set in `.env`.

## License

MIT License

---

*This project is for educational and prototyping purposes. Use responsibly and comply with Google API terms of service.*