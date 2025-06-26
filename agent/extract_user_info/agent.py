from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
import os
import json
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from agent.extract_user_info.services import update_user_profile
from core.utils.get_current_profile import get_user_profile
from core.base.schema import UserInformation
from agent.extract_user_info.prompt import EXTRACT_USER_INFORMATION_PROMPT

class UserInfoState(TypedDict):
    """State for user information extraction"""
    user_input: str
    current_profile: dict
    extracted_info: dict
    validated_info: dict
    save_result: str
    error: Optional[str]

class UserInfoExtractionAgent:
    """User information extraction agent"""
    
    def __init__(self, llm: ChatOpenAI = None):
        """Initialize the user info extraction agent"""
        if llm is None:
            # Load environment variables
            load_dotenv()
            openai_api = os.environ.get("OPENAI_API_KEY")
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1000,
                base_url="https://warranty-api-dev.picontechnology.com:8443",
                openai_api_key=openai_api,
            )
        else:
            self.llm = llm
            
        # Initialize database
        
        # Create the agent graph
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Create the user info extraction graph"""
        graph = StateGraph(UserInfoState)
        
        # Add nodes
        graph.add_node("extract", self._extract_node)
        graph.add_node("validate", self._validate_node)
        graph.add_node("save", self._save_node)
        
        # Add edges
        graph.add_edge(START, "extract")
        graph.add_conditional_edges("extract", self._should_continue, {
            "validate": "validate",
            "end": END
        })
        graph.add_conditional_edges("validate", self._should_save, {
            "save": "save",
            "end": END
        })
        graph.add_edge("save", END)
        
        return graph.compile()
    
    def _extract_node(self, state: UserInfoState) -> dict:
        """Extract user information from the input using the LLM"""
        print("🔍 Extracting user information...")
        try:
            user_input = state.get("user_input", "")
            current_profile = state.get("current_profile", {})
            
            # Format current profile for context
            profile_context = self._format_user_profile(current_profile)
            
            # Build the extraction prompt
            prompt = f"""{EXTRACT_USER_INFORMATION_PROMPT}
            
CURRENT USER PROFILE:
{profile_context}

EXTRACTION RULES:
- Only extract information that is explicitly mentioned in the user input
- If a field is not mentioned, do not include it in the response
- You can combine with current user information when user provides updates
- For additional_info field, combine existing info with new information
- Exception: If user explicitly requests to update/change information

USER INPUT TO ANALYZE:
{user_input}
"""
            
            # Extract using structured output
            response = self.llm.with_structured_output(UserInformation).invoke(prompt)
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
            print(f"❌ Error extracting user information: {e}")
            return {"error": f"Failed to extract user information: {str(e)}"}
    
    def _validate_node(self, state: UserInfoState) -> dict:
        """Validate the extracted user information"""
        print("🔍 Validating user information...")
        try:
            extracted_info = state.get("extracted_info", {})
            
            if not extracted_info:
                return {"error": "No user information extracted"}
            
            validation_errors = []
            
            # Validate phone number
            if extracted_info.get("phone_number"):
                phone = extracted_info["phone_number"]
                if not self._validate_phone_number(phone):
                    validation_errors.append("Phone number must be 10-15 digits")
            
            # Validate year of birth
            if extracted_info.get("year_of_birth"):
                year = extracted_info["year_of_birth"]
                if not self._validate_birth_year(year):
                    validation_errors.append("Year of birth must be between 1900 and current year")
            
            # Validate user name
            if extracted_info.get("user_name"):
                name = extracted_info["user_name"]
                if not self._validate_user_name(name):
                    validation_errors.append("User name must be at least 2 characters")
            
            if validation_errors:
                return {"error": "; ".join(validation_errors)}
            
            print("✅ User information is valid")
            return {"validated_info": extracted_info}
            
        except Exception as e:
            print(f"❌ Error validating user information: {e}")
            return {"error": f"Failed to validate user information: {str(e)}"}
    
    def _save_node(self, state: UserInfoState) -> dict:
        """Save the validated user information to the database"""
        print("💾 Saving user information...")
        try:
            validated_info = state.get("validated_info", {})
            #current_profile = state.get("current_profile", {})
            
            if not validated_info:
                return {"save_result": "❌ No valid user information to save"}
            
            # Save to database
            success = update_user_profile(validated_info)
            
            if success:
                saved_fields = list(validated_info.keys())
                result_msg = f"✅ User information saved successfully!\nUpdated fields: {', '.join(saved_fields)}\nData: {json.dumps(validated_info, indent=2, ensure_ascii=False)}"
                print(f"✅ Successfully saved user info: {saved_fields}")
                return {"save_result": result_msg}
            else:
                return {"save_result": "❌ Failed to save user information to database"}
                
        except Exception as e:
            print(f"❌ Error saving user information: {e}")
            return {"error": f"Failed to save user information: {str(e)}"}
    
    def _should_continue(self, state: UserInfoState) -> Literal["validate", "end"]:
        """Determine if the state should continue to validation"""
        if state.get("error"):
            print(f"❌ Stopping due to error: {state['error']}")
            return "end"
        
        if not state.get("extracted_info"):
            print("❌ No extracted info, ending process")
            return "end"
        
        return "validate"
    
    def _should_save(self, state: UserInfoState) -> Literal["save", "end"]:
        """Determine if the state should save the information"""
        if state.get("error"):
            print(f"❌ Stopping due to error: {state['error']}")
            return "end"
        
        if not state.get("validated_info"):
            print("❌ No validated info, ending process")
            return "end"
        
        return "save"
    
    def _format_user_profile(self, current_profile: dict) -> str:
        """Format user profile for LLM context"""
        try:
            if not current_profile:
                return "No personal information available"
            
            # Build context parts
            context_parts = []
            
            if current_profile.get('user_name'):
                context_parts.append(f"Name: {current_profile['user_name']}")
            
            if current_profile.get('year_of_birth'):
                age = 2025 - current_profile['year_of_birth']
                context_parts.append(f"Age: {age} (born {current_profile['year_of_birth']})")
            
            if current_profile.get('phone_number'):
                context_parts.append(f"Phone: {current_profile['phone_number']}")
            
            if current_profile.get('address'):
                context_parts.append(f"Location: {current_profile['address']}")
            
            if current_profile.get('major'):
                context_parts.append(f"Studies/Field: {current_profile['major']}")
            
            if current_profile.get('additional_info'):
                context_parts.append(f"Additional: {current_profile['additional_info']}")
            
            return " | ".join(context_parts) if context_parts else "No personal information available"
            
        except Exception as e:
            print(f"Error formatting profile: {e}")
            return "Error retrieving profile information"
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        if not isinstance(phone, str):
            return False
        
        # Remove common separators
        clean_phone = phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "").replace("+", "")
        
        return clean_phone.isdigit() and 10 <= len(clean_phone) <= 15
    
    def _validate_birth_year(self, year: int) -> bool:
        """Validate birth year"""
        current_year = 2025
        return isinstance(year, int) and 1900 <= year <= current_year
    
    def _validate_user_name(self, name: str) -> bool:
        """Validate user name"""
        return isinstance(name, str) and len(name.strip()) >= 2
    
    def process(self, user_input: str) -> dict:
        """Process user input and extract user information"""
        try:
            # Get current profile
            current_profile = get_user_profile() or {}
            
            print(f"🚀 Processing user info extraction for: {user_input[:50]}...")
            
            # Run the agent
            result = self.graph.invoke({
                "user_input": user_input,
                "current_profile": current_profile,
                "extracted_info": {},
                "validated_info": {},
                "save_result": "",
                "error": None
            })
            
            if result.get("error"):
                error_msg = f"❌ Error: {result['error']}"
                print(error_msg)
                return {"error": result["error"], "success": False}
            
            if result.get("save_result"):
                print(f"✅ Process completed: {result['save_result']}")
                return {
                    "success": True,
                    "message": result["save_result"],
                    "extracted_data": result.get("validated_info", {}),
                    "updated_fields": list(result.get("validated_info", {}).keys())
                }
            
            return {"error": "No result generated", "success": False}
            
        except Exception as e:
            error_msg = f"❌ Processing failed: {str(e)}"
            print(error_msg)
            return {"error": str(e), "success": False}
    
    def get_current_profile(self) -> dict:
        """Get current user profile"""
        try:
            return get_user_profile() or {}
        except Exception as e:
            print(f"❌ Error getting profile: {e}")
            return {}
    
    def get_formatted_profile(self) -> str:
        """Get formatted current user profile"""
        current_profile = self.get_current_profile()
        return self._format_user_profile(current_profile)

def create_user_info_extraction_agent(llm: ChatOpenAI = None) -> UserInfoExtractionAgent:
    """Factory function to create user info extraction agent"""
    return UserInfoExtractionAgent(llm)

# Convenience function for backwards compatibility
def save_user_information(user_input: str) -> dict:
    """Process user input and save user information (backwards compatibility)"""
    agent = create_user_info_extraction_agent()
    result = agent.process(user_input)
    
    if result.get("success"):
        return result.get("extracted_data", {})
    else:
        return {"error": result.get("error", "Unknown error")}
