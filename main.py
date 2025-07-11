import os
import asyncio
import json
# Importing Langchain/Langgraph packages
from langchain_mcp_adapters.client import MultiServerMCPClient
from graph import create_agent_graph
from langchain.prompts import ChatPromptTemplate
# FastAPI/Backend imports
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketException
from fastapi.responses import HTMLResponse
import uvicorn

from prompts import google_assistant_prompt

# Defining prompt template
prompt_template = ChatPromptTemplate(
            [
                ("system", google_assistant_prompt),
                ("user", "{query}"),
           ]
        )

# Defining lifespan.
@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # Getting tools from MCP server.
    with open("./servers/mcp_config.json", "r") as config:
        mcp_config = json.load(config)
    client = MultiServerMCPClient(mcp_config)
    tools = await client.get_tools()

    # Initialize agent.
    memory_config = {"configurable": {"thread_id": "1"}}
    agent = create_agent_graph(tools = tools)
    agent_chain = (prompt_template | agent)

    async def run_agent(query: str) -> str:
        async for event in agent_chain.astream(
                                        {"tools": tools,
                                        "query": query},
                                        stream_mode="updates",
                                        config = memory_config,
                                        ):
            if event.get("llm_call") is not None and (response := event["llm_call"]["messages"][0].content):
                answer = response
        return answer
    
    # Make agent accessible to websocket.   
    app.state.run_agent = run_agent

    yield


app = FastAPI(lifespan = lifespan)

# Example of html. Should be changed.
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Alfred</title>
    </head>
    <body>
        <h1>Alfred</h1>
        <h2>Your Google assistant</h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        while True:
            user_input = await websocket.receive_text()
            response = await app.state.run_agent(query = user_input)
            await websocket.send_text(response)
    except WebSocketException as error:
        return f"An error encountered while connecting to websocket.\nDetails: {error}"

if __name__ == "__main__":
    uvicorn.run("main:app", host = "localhost", port = 8000, reload = True)