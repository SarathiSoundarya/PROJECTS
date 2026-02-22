from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
from models import azure_chatopenai_model
from logger.base_logger import get_logger
logger = get_logger(__name__)

async def main():
    client = MultiServerMCPClient({
        "Data and Intelligence Server": {
            "command": "python",
            "args":["servers/SERVER_A/data_and_intelligence_server.py"],
            "transport":"stdio"
        },
        "External Services Server": {
            "url":"http://127.0.0.1:8000/mcp",
            "transport":"streamable-http"
    }})

    tools = await client.get_tools()

    print(f"Loaded tools: {tools}")

    agent = create_agent(azure_chatopenai_model, tools)

    math_response = await agent.ainvoke({"messages": [{"role": "user", "content": "What is the weather at New York City and what is 2+3?"}]})
    print("Math Response:", math_response)

asyncio.run(main())





