from mcp.server.fastmcp import FastMCP
from tool_utilities import execute_analysis_agent, execute_plotting_agent, execute_rag_agent
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer, CrossEncoder
from pathlib import Path
from logger.base_logger import get_logger
logger = get_logger(__name__)

mcp = FastMCP("Data and Intelligence Server", host="0.0.0.0", port=7002)

#data analysis tool to perform data analysis on a given dataset and return the results in a structured format
@mcp.tool()
def data_analysis(user_query:str, csv_filename:str, chat_session_id: str, chat_id: str)-> str:
    """Perform data analysis based on the user query and save results to shared folder.
    The user query should mandatorily contain the filename of the csv file to analyze and the type of analysis to perform. The results should be saved in the shared folder with a unique name. Pass the user query and shared folder path to the data analysis agent and return the results.
    Pass the chat session id and chat id to identify the shared folder path."""
    logger.info("Starting data analysis with query: " + user_query)
    execution_results = execute_analysis_agent(user_query, chat_session_id, chat_id, csv_filename)
    logger.info("Data analysis completed.")
    return str(execution_results)

#data visualization tool to create visualizations based on the data analysis results and save the visualizations to the shared folder
@mcp.tool()     
def data_visualization(user_query:str, csv_filename:str, chat_session_id: str, chat_id: str)-> str:
    """Perform data visualization or generate plots based on the user query and save results to shared folder.
    The user query should contain the filename of the csv file data to analyze and the type of visualization to create. The results should be saved in the shared folder with a unique name. Pass the user query and shared folder path to the data visualization agent and return the results.
    Pass the chat session id and chat id to identify the shared folder path."""
    logger.info(f"Starting data visualization with User query: {user_query}, CSV Filename: {csv_filename}, Chat Session ID: {chat_session_id}, Chat ID: {chat_id}")
    execution_results = execute_plotting_agent(user_query, chat_session_id, chat_id, csv_filename)
    logger.info("Data visualization completed.")
    return str(execution_results)

#rag tool to perform retrieval augmented generation based on a given query and return the results in a structured format
@mcp.tool()
def rag_tool(query: str, topic: str, country: str) -> str:
    """Query air pollution, health, climate or disaster related information from WHO/India documents using the RAG agent. Use this agent only when documents/repository/library is mentioned in the user query. The user query should contain the topic and country information.
    Topics can be one of the following: pollution, health, climate, disaster. Countries can be one of the following: global, india. If its related to disaster always choose india."""
    logger.info(f"Starting RAG tool with query: {query}, topic: {topic}, country: {country}")
    execution_results = execute_rag_agent(query, None, country)
    logger.info("RAG tool execution completed.")
    return str(execution_results)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
    