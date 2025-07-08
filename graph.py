import os
from typing import Annotated, List
from typing_extensions import TypedDict
# Langgraph libraries
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama

def create_agent_graph(tools: list) -> StateGraph:
    '''
    Creates a Langgraph agent graph equipped with the provided tools.
    Parameters:
        tools (list): the tools available for LLM from MCP servers.

    Returns:
        StateGraph: The compiled graph.
    '''

    # Defining AgentState
    class AgentState(TypedDict):
        messages: Annotated[List, add_messages]
    
    # Instanciate uncompiled graph
    graph_builder = StateGraph(AgentState)
    
    # Instanciate memory
    memory = MemorySaver()

    # Choose LLM and bind tools
    llm = ChatOllama(model = "llama3.2:latest", disable_streaming= True)
    llm_with_tools = llm.bind_tools(tools)
    
    # Definining nodes
    def llm_call(agent_state: AgentState):
        response = llm_with_tools.invoke(agent_state["messages"])
        return {"messages": [response]}

    # GRAPH BUILDING
    # Node
    graph_builder.add_node("llm_call", llm_call)
    graph_builder.add_node("tools", ToolNode(tools))
    #Edges
    graph_builder.add_edge(START, "llm_call")
    graph_builder.add_conditional_edges("llm_call",
                                        tools_condition,
                                        )
    graph_builder.add_edge("tools", "llm_call")
           
    graph = graph_builder.compile(checkpointer = memory)
    return graph
