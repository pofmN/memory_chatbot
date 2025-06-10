from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
import dotenv
from dotenv import load_dotenv
import os
import getpass

load_dotenv()
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

# Debug: Print if we found the key
if os.environ.get("GOOGLE_API_KEY"):
    api_key = os.environ.get("GOOGLE_API_KEY")
    print(f"Google API key loaded successfully (starts with {api_key[:5]}...)")
else:
    print("No API key found in environment variables. Prompting for input...")
    api_key = getpass.getpass("Enter your Google AI API key: ")
    os.environ["GOOGLE_API_KEY"] = api_key
    print("API key set manually.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.2,
    max_output_tokens=None,
)

prompt = PromptTemplate.from_template(
    """Your are helpful assistant. Answer the question based on the context provided.
Question: {question}"""
)

answer_chain = prompt | llm | StrOutputParser()

answer = answer_chain.invoke(
    {"question": "What is the capital of France?",}
    )

print(answer)  # Should print "Paris" or similar response based on the model's output.