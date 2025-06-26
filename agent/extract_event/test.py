from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

openai_api = os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.2,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",
        openai_api_key=openai_api,
    )

test_prompt = "What is the capital of France?"
response = llm.invoke(test_prompt)
print(f"Response: {response}")