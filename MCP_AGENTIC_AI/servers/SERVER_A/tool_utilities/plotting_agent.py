from langchain.agents import create_agent
from models import azure_chatopenai_model, google_model
from .code_execution_tool import python_code_exec_tool
from pathlib import Path
from logger.base_logger import get_logger
from dotenv import load_dotenv
load_dotenv()
logger = get_logger(__name__)
AGENT_NAME = "plotting_agent"

def extract_ai_message(result: dict) -> str:
    """
    Extract AI message content from langchain agent result
    """
    messages = result.get("messages", [])

    for msg in reversed(messages):  # search from latest
        if msg.__class__.__name__ == "AIMessage":
            return msg.content

    return ""

def execute_plotting_agent(user_query, shared_folder,csv_filename):
    try:
        # Set your API key
        
        logger.info(f"Invoking {AGENT_NAME} with query: {user_query} and shared folder: {shared_folder} and csv filename: {csv_filename}")
        tools = [python_code_exec_tool]
        csv_path = str(Path(shared_folder) / csv_filename)  # construct full csv path
    
        
        #check if the csv file path is present in the csv_path else search in the whole shared folder a level up and if found then update the csv_path with the correct path
        if not Path(csv_path).is_file():
            #go a level up in the shared folder and search for the csv file
            shared_folder_parent = Path(shared_folder).parent
            #search for the file in the shared folder
            csv_path = None
            for file in shared_folder_parent.glob("**/*.csv"):
                if file.name == csv_filename:
                    csv_path = str(file)
                    logger.info(f"CSV file found at path: {csv_path}")
                    break
            if csv_path is None:
                logger.error(f"CSV file {csv_filename} not found in shared folder or its parent directory.")
                return f"Error: CSV file {csv_filename} not found in shared folder or its parent directory."

        if csv_path is None:
            #check any of the files in the shared folder has the csv filename and if found then update the csv_path with the correct path
            for file in Path(shared_folder).glob("**/*.csv"):
                if file.name == csv_filename:
                    csv_path = str(file)
                    logger.info(f"CSV file found at path: {csv_path}")
                    break
            if csv_path is None:
                logger.error(f"CSV file {csv_filename} not found in shared folder or its parent directory.")
                return f"Error: CSV file {csv_filename} not found in shared folder or its parent directory."
        
        user_query =f"User Query: {user_query}\nShared Folder: {shared_folder}\nCSV FILE Path: {csv_path}, use this CSV file for plotting the graphs as per the user query and save the results to shared folder ."
          
        system_instructions =system_instructions = """
        You are an expert in Python data plotting using plotly express utilizing the data from a given csv path.

        Task:
        - Extract the CSV file path from the user query.
        - If no CSV path is mentioned, do NOT perform any plotting.
        - Generate the relevant plots requested in the user query using plotly express.
        - Save the plots to the shared folder as JSON.
        - The filename MUST include a unique uuid and MUST end with the suffix: plotly_json.json
        - ALWAYS save results into a .json file in the shared folder.
        - Return ONLY the filename of the JSON file created (no extra text).

        Path Handling Rules:
        - For accessing csv path and shared folder path, use the Path library:
        from pathlib import Path
        - Always encode paths using Path("path_string") and then use the encoded path.
        - When writing Windows file paths, ALWAYS use raw string literals:
        Example: Path(r"C:\\Users\\name\\file.csv")
        - Never construct paths using string concatenation.

        Code Generation Rules (VERY IMPORTANT):
        1. Generate valid executable Python code exactly as it should appear in a .py file.
        2. DO NOT include escaped newline characters like \\n in the code.
        3. DO NOT add stray backslashes (\\) outside string literals.
        4. NEVER prepend a backslash before variable names.
        5. Use raw strings (r"...") for all Windows paths.
        6. Ensure imports are included when needed.
        7. The final code must run without syntax errors.
        8. print the column names of the dataframe csv before plotting to ensure that correct column names are used for plotting.
        Validation Step:
        - Before returning the code, mentally simulate running it and ensure there are no syntax errors.

        Plot Saving Rules:
        - Use plotly express for plotting.
        - Save the figure using fig.write_json(output_path).
        - The output path must be inside the shared folder.
        - Filename format example:
        <uuid>_plotly_json.json

        - Return output saying that the plotting is successful and include the filename of the saved plot in the response.
        Failure Handling:
        - If the CSV path cannot be extracted → do NOT generate code.
        """

        tools = [python_code_exec_tool]
        agent = create_agent(
            model=google_model,#azure_chatopenai_model,
            tools=tools,
            system_prompt=system_instructions
        )
        logger.info(f"{AGENT_NAME} initialized! Starting execution...")
       
        response = agent.invoke({"messages": [("user", user_query)]})
        response = extract_ai_message(response)
        logger.info(f"{AGENT_NAME} execution completed. Results: {response}")
        return str(response)
              
    except Exception as e:
        logger.error(f"Error in {AGENT_NAME} invoke method: {e}")
        return "Error executing plotting agent: " + str(e)
            
