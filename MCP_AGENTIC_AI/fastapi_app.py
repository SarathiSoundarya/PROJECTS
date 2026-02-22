import os
import asyncio
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
import json
from models import azure_chatopenai_model, google_model
from db import SessionDB
from logger.base_logger import get_logger
from pathlib import Path
from utilities import format_response
from pydantic import BaseModel, Field
from typing import Literal
load_dotenv()

logger = get_logger(__name__)

app = FastAPI(title="MCP Agent API")


class ChatRequest(BaseModel):
    user_id: int
    chat_session_id: int
    user_query: str

class NewSessionRequest(BaseModel):
    user_id: int

class FollowupIntent(BaseModel):
    """To detect if the user query is a follow-up and to detect the intent in the user query."""
    is_followup: str = Field(description="Indicates if the user query is a follow-up, return 'yes' or 'no'", default="no")
    intent_detected: str = Field(description="The intent detected in the user query,'yes' or 'no', return empty string if not found", default="")
    response_if_intent_not_found: str = Field(description="The response to return if the intent is not found, return empty string if intent is found", default="")


#chat endpoint
@app.post("/chat")
async def chat(req: ChatRequest):
    try:

        logger.info(f"Received chat request: {req}")
        db = SessionDB()

        #create a chat id 
        user_id = req.user_id
        chat_session_id = req.chat_session_id
        user_query = req.user_query

        chat_id = db.create_chat_id(
            user_id,
            chat_session_id,
            user_query
        )
        PROJECT_ROOT = Path(__file__).parent.resolve()  # MCP_AGENTIC_AI folder

        shared_folder = PROJECT_ROOT / f"static/{user_id}/{chat_session_id}/{chat_id}"

        logger.info(f"Chat ID {chat_id} created for user {user_id} in session {chat_session_id}. Shared folder: {shared_folder}")

        shared_folder.mkdir(parents=True, exist_ok=True)

        #load last 2 chats for context
        rows = db.get_last_chats(chat_session_id, chat_id, limit=2)

        history = []
        for q, a in rows:
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": a})
        logger.info("Chat history loaded for context: {}".format(history))
        agent, tool_info = await build_agent()
        
        followup_result = is_followup(history, user_query, tool_info)
        if followup_result.intent_detected == "no":
            response= [{
                "type":"markdown",
                "content": followup_result.response_if_intent_not_found
            }]
            return {
                "response": response,
                "followup": followup_result.is_followup,
                "shared_folder": str(shared_folder),
                "chat_id": chat_id
            }
        
        messages = []
        if followup_result.is_followup == "yes":
            messages.extend(history)
        

        messages.append({
            "role": "user",
            "content": user_query + "Please save any files to the shared folder and include the file path in your response. Shared folder path: " + str(shared_folder)
        })
    
        response = await agent.ainvoke({
            "messages": messages
        })
        logger.info(f"Agent response received: {response}")

        texts = []

        for msg in response["messages"]:

            if isinstance(msg, AIMessage) and msg.content:
                texts.append(msg.content)

            # Tool messages
            elif isinstance(msg, ToolMessage):

                if isinstance(msg.content, list):
                    for item in msg.content:
                        texts.append(item.get("text", ""))

                else:
                    texts.append(str(msg.content))

        answer="\n".join(t for t in texts if t)       
        logger.info(f"Response before formatting: {answer}")

        answer = format_response(user_query, answer)
        answer = attach_filepaths(answer, shared_folder)
        if not isinstance(answer, str):
            answer = json.dumps(answer, ensure_ascii=False)

        safe_answer = answer.encode("utf-8", "ignore").decode()

        print(f"Final response: {safe_answer}")

        db.update_chat_answer(
            user_id,
            chat_session_id,
            chat_id,
            safe_answer
        )

        return {
            "response": answer,
            "followup": followup_result.is_followup,
            "shared_folder": str(shared_folder),
            "chat_id": chat_id
        }

    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))
       


#new session
@app.post("/new_session")
async def new_session(req: NewSessionRequest):

    db = SessionDB()
    logger.info("Initialized SessionDB for new session request")
    chat_session_id=db.create_chat_session(
        req.user_id
    )
    logger.info(f"New chat session created: {chat_session_id} for user {req.user_id}")
    return {
        "chat_session_id": chat_session_id
    }


# Get Files in Folder
@app.get("/files")
async def list_files(user_id: int, session_id: int, chat_id: int):
    PROJECT_ROOT = Path(__file__).parent.resolve()  # MCP_AGENTIC_AI folder
    folder = PROJECT_ROOT / f"static/{user_id}/{session_id}/{chat_id}"

    if not folder.exists():
        return []

    return [f.name for f in folder.iterdir() if f.is_file()]



# List Sessions
@app.get("/sessions/{user_id}")
async def list_sessions(user_id: str):
    db = SessionDB()

    sessions = db.get_sessions(user_id)

    return sessions



def is_followup(chat_history: List[dict], user_query: str,tool_info: str) -> bool:
    #intent detection and followup logic here
    
    logger.info("Detecting if the query is a follow-up and intent detection. User query: {}, Chat history: {}".format(user_query, chat_history))
    structured_llm = google_model.with_structured_output(FollowupIntent)
    prompt=f"""Given the following conversation history and user query, determine if the user query is a follow-up question.
    A follow-up question is a question that is related to the previous conversation and requires the context of the previous conversation to answer. If it is a follow-up question, return 'yes' for is_followup else 'no' for is_followup.

    You also have to detect the intent of the user query.
    The intent of the user query is yes if it can be answered one of the following tools: {tool_info}.
    If the user query can be answered by any of the above tools, then return 'yes' for intent_detected else return a 'no' for intent_detected. If the intent is not found, return a response that they can pose a query that is related to for better assistance as response_if_intent_not_found.
    You should return 'no' ONLY if the user query is not related to any of the tools and cannot be answered by the agent. If the user query is related to any of the tools, then it is a valid query and you should return 'yes' for intent_detected even if it is a follow-up question.
    User's query: {user_query}
    Conversation history: {chat_history}
    """

    result = structured_llm.invoke(prompt)
    logger.info("Follow-up detection result: {}".format(result))
    return result


async def build_agent():

    with open("servers.json","r") as f:
        servers = json.load(f)
    client = MultiServerMCPClient(servers)
    tools = await client.get_tools()
    tools_info = {tool.name: tool.description for tool in tools}
    prompt = f"""
    You are an assistant.

    You have access to the following tools:

    {tools_info}

    If asked for plotting or analysis:
    1. Fetch CSV data using the best tool if not already provided in the query.
    2. Perform plotting/analysis for the csv data. MANDATORY to pass the CORRECT csv filename returned from the previous tool to the analysis/plotting tool. Do NOT pass any imaginary filename, only use the filename returned from the file retrieval tool.
    3. Save results to shared folder
    4. MANDATORILY to USE the correct filename returned from the tool for saving the results and include the file name in the response.This instruction is of utmost importance,
    5.Mandatory to Include all the filenames in the response and do not include any file paths.
    6. You can even use the csv file paths in the previous response, in case the query seems like a follow-up and the user is asking for analysis or plotting after the csv file has been provided in the previous response. Just make sure to use the correct csv filename from the previous response and pass only the filename instead of the whole file path to the agent.
    """
    agent = create_agent(google_model, tools, system_prompt=prompt)

    return agent, tools_info



def attach_filepaths(response_blocks, shared_folder: Path):

    if isinstance(response_blocks, str):
        try:
            response_blocks = json.loads(response_blocks)
        except Exception:
            return response_blocks

    if not isinstance(response_blocks, list):
        return response_blocks

    for block in response_blocks:
        block_type = block.get("type")
        filename = block.get("filename")

        if filename:
            if block_type == "document":
                doc_folder = Path("C:/Users/soundarya.sarathi/OneDrive - Accenture/study_materials/PROJECTS/MCP_AGENTIC_AI/servers/SERVER_A/tool_utilities/RAG/knowledge_docs")
                filepath = doc_folder / filename
                block["filepath"] = str(filepath)
            else:
                filepath = shared_folder / filename  
                block["filepath"] = str(filepath)     

    return response_blocks

#run the fast api on port 6000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)