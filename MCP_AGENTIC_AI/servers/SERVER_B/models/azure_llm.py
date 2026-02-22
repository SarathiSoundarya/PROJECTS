from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()
import os

azure_chatopenai_model = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"), 
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

# response = azure_chatopenai_model.invoke([HumanMessage(content="Explain AI in one sentence")])

# print("Response:")
# print(response.content)