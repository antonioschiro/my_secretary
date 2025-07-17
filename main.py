import os
import asyncio
import json
# Importing Langchain/Langgraph packages
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import ChatPromptTemplate
# FastAPI/Backend imports
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from graph import create_agent_graph
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
        answer = None
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
app.mount("/frontend/static", StaticFiles(directory= "./frontend/static"), name= "static")
templates = Jinja2Templates(directory="frontend")

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse(name = "main_page.html", context= {"request": request})

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