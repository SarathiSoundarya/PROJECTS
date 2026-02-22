import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()

# Set your API key
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE-API-KEY")

google_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")