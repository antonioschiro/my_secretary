# My secretary [WORK IN PROGRESS 🛠️]

"My secretary" is a Python project that provides programmatic access to Gmail features using Google APIs, LangChain, and MCP. It enables you to interact with your Gmail account, automate email tasks, and integrate with language models.

## Features

- Authenticate and connect to Gmail using OAuth2.
- Retrieve user profile information.
- Create email drafts.
- Send emails programmatically.
- Integrate with language models via LangChain and Ollama.
- Modular server-client architecture using MCP.

## Project Structure

```
main.py                      # Entry point for the assistant agent
servers/
  gmail_server.py            # MCP server exposing Gmail tools
  gmail_quickstart.py        # Script to generate/update Google credentials
  credentials.json           # Google OAuth2 credentials
  token.json                 # User access/refresh tokens
pyproject.toml               # Project dependencies and metadata
.env                         # Environment variables (not committed)
```

## Setup

1. **Clone the repository** and navigate to the project directory.

2. **Install dependencies** (Python 3.12.9 recommended):

   ```sh
   uv pip install -r requirements.txt
   ```

3. **Set up environment variables**  
   Create a `.env` file with the following variables:

   ```
   SCOPES=https://mail.google.com/
   USER_ID=me
   ```

4. **Google API Credentials**  
   - Place your `credentials.json` in the `servers/` directory.
   - Run the quickstart script to generate `token.json`:

     ```sh
     uv run servers/gmail_quickstart.py
     ```

## Usage

- **Start the Gmail MCP server:**

  ```sh
  uv run servers/gmail_server.py
  ```

- **Start the Gmail MCP server in DEV MODE:**

  ```sh
  mcp dev servers/gmail_server.py
  ```

- **Run the main assistant agent:**

  ```sh
  uv run main.py
  ```

## Notes

- The project uses [LangChain](https://github.com/langchain-ai/langchain), [Ollama](https://github.com/ollama/ollama), and [MCP](https://github.com/microsoft/mcp).
- Make sure your Google Cloud project has Gmail API enabled.
- Do not commit your `.env`, `token.json`, or other sensitive files.

## License

MIT License

---

*This project is for educational and prototyping purposes. Use responsibly and comply with Google API terms of service.*