from langchain.agents import create_agent
from models import azure_chatopenai_model, google_model
from .code_execution_tool import python_code_exec_tool
from pathlib import Path
from logger.base_logger import get_logger
logger = get_logger(__name__)
AGENT_NAME = "data_analysis_agent"

def extract_ai_message(result: dict) -> str:
    """
    Extract AI message content from langchain agent result
    """
    messages = result.get("messages", [])

    for msg in reversed(messages):  # search from latest
        if msg.__class__.__name__ == "AIMessage":
            return msg.content

    return ""

def execute_analysis_agent(user_query, shared_folder, csv_filename):
    try:
        logger.info(f"Invoking {AGENT_NAME} with query: {user_query} and shared folder: {shared_folder} and csv filename: {csv_filename}")
        tools = [python_code_exec_tool]
        
        shared_folder = Path(shared_folder)
        shared_folder_parent = shared_folder.parent

        csv_path = shared_folder / csv_filename


        # Direct path check
        if not csv_path.is_file():

            csv_path = None

            #  Search in parent recursively
            for file in shared_folder_parent.glob("**/*.csv"):
                if file.name == csv_filename:
                    csv_path = file
                    logger.info(f"CSV file found at path: {csv_path}")
                    break

            # Fallback → latest csv in parent
            if csv_path is None:
                latest_csv = max(
                    shared_folder_parent.glob("*.csv"),
                    key=lambda x: x.stat().st_mtime,
                    default=None
                )

                if latest_csv:
                    csv_path = latest_csv
                    logger.info(f"Latest CSV file found at path: {csv_path}")


        # 4 Final validation
        if csv_path is None:
            logger.error(
                f"CSV file {csv_filename} not found in shared folder or parent directory."
            )
            return (
                f"Error: CSV file {csv_filename} not found "
                f"in shared folder or parent directory."
            )

        csv_path = str(csv_path)  # convert Path object to string for agent input
        user_query =f"User Query: {user_query}\nShared Folder: {shared_folder}\nCSV FILE Path: {csv_path}, use this CSV file for doing the analysis as per the user query and save the results to shared folder ."
        
        system_instructions = """
        You are an expert in Python data analysis for a csv file given in the csv file path.
        Perform relevant analysis as per the user query using the data from the given csv path.
        Extract the CSV file path from the query.
        If no CSV is mentioned, do NOT do analysis.
        Perform relevant time-series analysis.
        Do NOT plot any graphs
        Save results into a .txt or .csv file in the shared folder. Suffix the result file name with analysis and add a unique uuid to the filename and save it under the shared folder.
        For accessing csv path and shared folder path, use the Path library imported as "from pathlib import Path", encode the path as Path("path_string") and then use the encoded path for reading the csv and saving the analysis results. 
        Return only the filename of the file created.
        Return output saying that the analysis is successful and include the filename of the saved analysis in the response.
        """

        tools = [python_code_exec_tool]
        agent = create_agent(
            model=google_model,#azure_chatopenai_model,
            tools=tools,
            system_prompt=system_instructions
        )

        results=agent.invoke({"messages": [("user", user_query)]})
        response = extract_ai_message(results)
        logger.info(f"{AGENT_NAME} execution completed. Results: {response}")
        return str(response)
              
    except Exception as e:
        logger.error(f"Error in {AGENT_NAME} invoke method: {e}")
        return "Error executing data analysis agent: " + str(e)
            

