from langgraph.graph import StateGraph, START, END
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
import os
import json
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from core.base.schema import UserInformation
from agent.extract_user_info_agent.services import update_user_profile, get_user_profile
from agent.extract_user_info_agent.prompt import _extract_user_information_promt


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
openai_api = os.environ.get("OPENAI_API_KEY")

system_prompt = _extract_user_information_promt

llm = ChatOpenAI(
        model_name="gpt-4o-mini", # gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, ada-2, 3-small
        temperature=0.1 ,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",  # Ensure /v1 path if OpenAI-compatible
        openai_api_key=openai_api,
    )


# class UserInformation(BaseModel):
#     user_name: Annotated[Optional[str], Field(description="Personal name of the user")]
#     phone_number: Annotated[Optional[str], Field(description="User's phone number")]
#     year_of_birth: Annotated[Optional[int], Field(description="User's year of birth")]
#     address: Annotated[Optional[str], Field(description="User's address (city, province, or full address)")]
#     major: Annotated[Optional[str], Field(description="User's field of study or academic major")]
#     additional_info: Annotated[Optional[str], Field(description="Any other relevant details about the user")]

class UserInfoState(TypedDict):
    user_input: str
    current_profile: dict
    extracted_info: dict
    validated_info: dict
    save_result: str
    error: Optional[str]

def extract_node(state: UserInfoState) -> dict:
    """Extract user information from the input using the LLM."""
    print("🔍 Extracting user information...")
    try:
        user_input = state.get("user_input", "")
        current_profile = format_user_profile(state.get("current_profile", {}))
        prompt = f"""{system_prompt}
        IMPORTANT: Only extract information that is explicitly mentioned in the user input.
        If a field is not mentioned, do not include it in the response at all.
        Consider with the current user information, you can update the fields that are mentioned in the user input. 
        Here is the current user information:{current_profile},
        If needed, you can use the current user information to combine with user input to have fully information, 
        additional_info field should be combined when user provide more information.
        Except case that user require to update their information.
        Here is the user input: {user_input}
        """
        response = llm.with_structured_output(UserInformation).invoke(prompt)
        response_data = response.model_dump()

        # Filter out None/empty values to only update mentioned fields
        filtered_data = {}
        for key, value in response_data.items():
            if value is not None and value != "":
                # For strings, also check if it's not just whitespace
                if isinstance(value, str) and value.strip():
                    filtered_data[key] = value.strip()
                elif not isinstance(value, str):
                    filtered_data[key] = value
        print(f"🔍 Extracted fields: {list(filtered_data.keys())}")
        return {"extracted_info": filtered_data}

    except Exception as e:
        print(f"❌ Error extracting user input: {e}")
        return {"error": "Failed to extract user input: " + str(e)}


# def extract_user_information(
#     user_input: str
# ) -> dict:
#     """Extract user information using the provided LLM instance."""
#     current_user_profile = format_user_profile()
#     prompt = f"""{system_prompt}
#     IMPORTANT: Only extract information that is explicitly mentioned in the user input. 
#     If a field is not mentioned, do not include it in the response at all.
#     Consider with the current user information, you can update the fields that are mentioned in the user input. 
#     Here is the current user information:{current_user_profile},
#     If needed, you can use the current user information to combine with user input to have fully information, 
#     additional_infor field may suppose to combine when user provide information.
#     Here is the user input: {user_input}
#     """
    
#     # ✅ Use the passed LLM instance
#     response = llm.with_structured_output(UserInformation).invoke(prompt)
    
#     try: 
#         response_data = response.model_dump()
        
#         # ✅ Filter out None/empty values to only update mentioned fields
#         filtered_data = {}
#         for key, value in response_data.items():
#             if value is not None and value != "":
#                 # For strings, also check if it's not just whitespace
#                 if isinstance(value, str) and value.strip():
#                     filtered_data[key] = value.strip()
#                 elif not isinstance(value, str):
#                     filtered_data[key] = value
        
#         print(f"🔍 Extracted fields: {list(filtered_data.keys())}")
#         return filtered_data
#     except Exception as e:
#         print(f"❌ Error extracting user information: {e}")
#         return {"error": "Failed to extract user information: " + str(e)}

def validate_node(state: UserInfoState) -> dict:
    """Validate the extracted user information."""
    print("🔍 Validating user information...")
    try:
        extracted_info = state.get("extracted_info", {})
        
        if not extracted_info:
            return {"error": "No user information extracted."}
        
        if extracted_info.get("phone_number"):
            phone = extracted_info["phone_number"]
            if not isinstance(phone, str) or len(phone) < 10 or len(phone) > 13 or not phone.isdigit():
                return {"error": "Phone number must be a string of digits between 10 and 15 characters."}
        
        if extracted_info.get("year_of_birth"):
            current_year = 2025
            if not isinstance(extracted_info["year_of_birth"], int) or \
               extracted_info["year_of_birth"] < 1900 or \
               extracted_info["year_of_birth"] > current_year:
                return {"error": "Year of birth must be a valid year between 1900 and the current year."}   
        
        print("✅ User information is valid.")
        return {"validated_info": extracted_info}
    except Exception as e:
        print(f"❌ Error validating user information: {e}")
        return {"error": "Failed to validate user information: " + str(e)}
    
def save_node(state: UserInfoState) -> dict:
    """Save the validated user information to the database."""
    print("💾 Saving user information...")
    try:
        validated_info = state.get("validated_info", {})
        
        if state.get("error") or not validated_info:
            return {"save_result": "❌No valid user information to save."}
        
        success = update_user_profile(validated_info)
        if success:
            result_msg = f"User information saved successfully: {json.dumps(validated_info, indent=2, ensure_ascii=False)}"
            return {"save_result": result_msg}
        else:
            return {"save_result": "❌Failed to save user information."}
    except Exception as e:
        print(f"❌ Error saving user information: {e}")
        return {"error": "Failed to save user information: " + str(e)}
    
def should_continue(state: UserInfoState) -> Literal["end", "validate"]:
    """Determine if the state should continue to the next step."""
    # If there's an error, we stop the process
    if state.get("error"):
        print(f"❌ Stopping due to error: {state['error']}")
        return "end"
    if not state.get("extracted_info"):
        return "end"
    return "validate"

def should_save(state: UserInfoState) -> Literal["end", "save"]:
    """Determine if the state should save the information."""
    # If there's an error, we stop the process
    if state.get("error"):
        print(f"❌ Stopping due to error: {state['error']}")
        return "end"
    if not state.get("validated_info"):
        return "end"
    return "save"

def format_user_profile(current_profile: dict) -> str:
    """Get user profile formatted for LLM prompt injection"""
    try:        
        if not current_profile:
            return "USER PROFILE: No personal information available."
        
        # Build context parts
        context_parts = []
        
        if current_profile.get('user_name'):
            context_parts.append(f"Name: {current_profile['user_name']}")
        
        if current_profile.get('year_of_birth'):
            age = 2025 - current_profile['year_of_birth']
            context_parts.append(f"Age: {age} ({current_profile['year_of_birth']})")
        
        if current_profile.get('phone_number'):
            context_parts.append(f"Phone: {current_profile['phone_number']}")
        
        if current_profile.get('address'):
            context_parts.append(f"Location: {current_profile['address']}")
        
        if current_profile.get('major'):
            context_parts.append(f"Studies: {current_profile['major']}")
        
        if current_profile.get('additional_info'):
            context_parts.append(f"Other: {current_profile['additional_info']}")
        
        if context_parts:
            return "USER PROFILE: " + " | ".join(context_parts)
        else:
            return "USER PROFILE: No personal information available."
            
    except Exception as e:
        print(f"Error getting profile: {e}")
        return "USER PROFILE: Error retrieving information."



def create_user_info_agent():
    graph = StateGraph(UserInfoState)
    graph.add_node("extract", extract_node)
    graph.add_node("validate", validate_node)
    graph.add_node("save", save_node)
    
    #add edges
    graph.add_edge(START, "extract")
    graph.add_conditional_edges("extract", should_continue,
                   {
                       "validate": "validate",
                       "end": END
                   })
    graph.add_conditional_edges("validate", should_save,
                   {
                       "save": "save",
                       "end": END
                   })
    graph.add_edge("save", END)
    return graph.compile()

user_info_agent = create_user_info_agent()

def save_user_information(user_input: str) -> str:
    try:
        current_profile = get_user_profile() or {}
        
        # Run the agent
        result = user_info_agent.invoke({
            "user_input": user_input,
            "current_profile": current_profile,
            "extracted_info": {},
            "validated_info": {},
            "save_result": "",
            "error": None
        })
        if result.get("error"):
            print(f"❌ Error in user information agent: {result['error']}")
            return {"error": result["error"]}
        if result.get("save_result"):
            print(f"✅ User information saved successfully: {result['save_result']}")
            return result["validated_info"]
    except Exception as e:
        print(f"❌ Error in user information agent: {e}")
        return {"error": "Failed to process user information: " + str(e)}

# if __name__ == "__main__":
#     print("🚀 Testing User Information Agent")
#     print("=" * 50)
    
#     # Test input
#     user_input_example = "my name is Pham Van Nam, i was born in 2003, now i'm a student in DaNang and intern at HBG company"
    
#     print(f"Input: {user_input_example}")
#     print("-" * 50)
    
#     # Test the agent
#     result = save_user_information(user_input_example)
#     print("Agent Result:")
#     print(result)
    
#     print("-" * 50)
#     print("Current Profile:")
#     print(format_user_profile())