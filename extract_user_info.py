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
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from database.storage import DatabaseManager
from prompt import _extract_user_information_promt


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
openai_api = os.environ.get("OPENAI_API_KEY")

system_prompt = _extract_user_information_promt

llm = ChatOpenAI(
        model_name="gpt-4o", # gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, ada-2, 3-small
        temperature=0.1 ,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",  # Ensure /v1 path if OpenAI-compatible
        openai_api_key=openai_api,
    )

db = DatabaseManager()

class UserInformation(BaseModel):
    user_name: Annotated[Optional[str], Field(description="Personal name of the user")]
    phone_number: Annotated[Optional[str], Field(description="User's phone number")]
    year_of_birth: Annotated[Optional[int], Field(description="User's year of birth")]
    address: Annotated[Optional[str], Field(description="User's address (city, province, or full address)")]
    major: Annotated[Optional[str], Field(description="User's field of study or academic major")]
    additional_info: Annotated[Optional[str], Field(description="Any other relevant details about the user")]

def extract_user_information(
    user_input: str
) -> dict:
    """Extract user information using the provided LLM instance."""
    prompt = f"""{system_prompt}
    IMPORTANT: Only extract information that is explicitly mentioned in the user input. 
    If a field is not mentioned, do not include it in the response at all.
    Here is the user input: {user_input}
    """
    
    # ✅ Use the passed LLM instance
    response = llm.with_structured_output(UserInformation).invoke(prompt)
    
    try: 
        response_data = response.model_dump()
        
        # ✅ Filter out None/empty values to only update mentioned fields
        filtered_data = {}
        for key, value in response_data.items():
            if value is not None and value != "":
                # For strings, also check if it's not just whitespace
                if isinstance(value, str) and value.strip():
                    filtered_data[key] = value.strip()
                elif not isinstance(value, str):
                    filtered_data[key] = value
        
        print(f"🔍 Extracted fields: {list(filtered_data.keys())}")
        return filtered_data
    except Exception as e:
        print(f"❌ Error extracting user information: {e}")
        return {"error": "Failed to extract user information: " + str(e)}

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
    user_input: str,
) -> str:
    """
    Save the extracted user information to a database or file.
    
    Args:
        user_info (dict): The extracted user information.
    """
    user_info = extract_user_information(user_input)
    if validate_user_information(user_info):
        db.update_user_profile(user_info)
    else:
        print("Invalid user information:", user_info)
    #print("User information saved:", json.dumps(user_info, indent=2, ensure_ascii=False))
    return user_info


# user_input_example = "my name is Pham Van Nam, i was born in 2003, now i student in DaNang and intern in HBG company"
# result = save_user_information(user_input_example)
# #print(result)
# print(json.dumps(result, indent=2, ensure_ascii=False))
# print("User name: "+result.get("user_name"))