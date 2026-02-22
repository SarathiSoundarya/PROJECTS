#ollama allows us to download and run llms locally
#https://ollama.com/library/gemma3
# in powershell: ollama -- version
#setx OLLAMA_MODELS "C:\Users\soundarya.sarathi\ollama_models"  After this restart the power shell
#ollama pull gemma3:1b
#ollama serve --> will open localhost at http://localhost:11434
#ollama list will list all the models
#ollama run gemma3:1b
#ollama rm gemma3:1b -> to remove the model

from langchain_ollama import ChatOllama

llama321b_ollama_llm = ChatOllama(
    model="llama3.2:1b",
    base_url="http://localhost:11434",
    temperature=0
)

# response = llama321b_ollama_llm.invoke("Explain AI in one sentence")

# print("Response:")
# print(response.content)
