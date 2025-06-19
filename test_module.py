from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END, MessagesState
from pydantic import BaseModel, Field
from typing import List, Annotated, Literal, Optional
from langchain.chat_models import init_chat_model
import os
import json
from dotenv import load_dotenv
from database.storage import DatabaseManager
from prompt import _extract_user_information_promt


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

system_prompt = _extract_user_information_promt

llms = init_chat_model(
    "google_genai:gemini-2.0-flash",
    temperature=0.2,
    max_tokens=1000,
    api_key=GOOGLE_API_KEY
)

db = DatabaseManager()

class UserInformation(BaseModel):
    user_name: Annotated[str, Field(description="Full name of the user")]
    phone_number: Annotated[Optional[str], Field(description="User's phone number")]
    year_of_birth: Annotated[Optional[int], Field(description="User's year of birth")]
    address: Annotated[Optional[str], Field(description="User's address (city, province, or full address)")]
    major: Annotated[Optional[str], Field(description="User's field of study or academic major")]
    additional_info: Annotated[Optional[str], Field(description="Any other relevant details about the user")]

def extract_user_information(
    user_input: str
) -> Annotated[dict, Field(description="Extracted user information in JSON format")]:
    """
    Extract user information from the input string.
    
    Args:
        user_input (str): The input string containing user information.
        
    Returns:
        dict: Extracted user information as a dictionaryß
    """
    prompt = f"""{system_prompt}
    Here is the user input: {user_input}
    """
    response = llms.with_structured_output(UserInformation).invoke(prompt) # Example output for testing purposes
    try: 
        response_text = response.model_dump()
        return response_text
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return {
            "error": str(e),
            "response": response_text
        }

def validate_user_information(
    user_info: dict
) -> bool:
    """
    Validate the extracted user information.
    
    Args:
        user_info (dict): The extracted user information.
        
    Returns:
        bool: True if the information is valid, False otherwise.
    """
    if not user_info.get("user_name"):
        return False
    if user_info.get("phone_number") and not user_info["phone_number"].isdigit():
        return False
    if user_info.get("year_of_birth"):
        try:
            year = int(user_info["year_of_birth"])
            if year < 1900 or year > 2019:
                return False
        except ValueError:
            return False
    return True

def save_user_information(
    user_input: str
) -> None:
    """
    Save the extracted user information to a database or file.
    
    Args:
        user_info (dict): The extracted user information.
    """
    user_info = extract_user_information(user_input)
    if validate_user_information(user_info):
        db.add_user_info(user_info)
    else:
        print("Invalid user information:", user_info)
    print("User information saved:", json.dumps(user_info, indent=2, ensure_ascii=False))



user_input_example = "Nguyễn Văn A, sinh năm 2001, học IT tại Đại học Bách Khoa, số điện thoại 0123456789, sống tại Hà Nội."
result = extract_user_information(user_input_example)
#print(result)
print(json.dumps(result, indent=2, ensure_ascii=False))
print("User name: "+result.get("user_name"))