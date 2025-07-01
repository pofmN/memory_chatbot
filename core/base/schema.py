from typing import Annotated, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from typing import Optional



class State(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str

class UserInformation(BaseModel):
    user_name: Annotated[Optional[str], Field(description="Personal name of the user")]
    phone_number: Annotated[Optional[str], Field(description="User's phone number")]
    year_of_birth: Annotated[Optional[int], Field(description="User's year of birth")]
    address: Annotated[Optional[str], Field(description="User's address (city, province, or full address)")]
    major: Annotated[Optional[str], Field(description="User's field of study or academic major")]
    additional_info: Annotated[Optional[str], Field(description="Any other relevant details about the user")]

class EventInformation(BaseModel):
    event_name: Annotated[Optional[str], Field(description="Name of the event")]
    start_time: Annotated[Optional[str], Field(description="Start time of the event in ISO format")]
    end_time: Annotated[Optional[str], Field(description="End time of the event in ISO format")]
    location: Annotated[Optional[str], Field(description="Location of the event")]
    priority: Annotated[Optional[str], Field(description="Priority level of the event (e.g., high, medium, low)")]
    description: Annotated[Optional[str], Field(description="Description of the event")]

class ActivitiesInformation(BaseModel):
    activity_name: Annotated[Optional[str], Field(description="Name of the activity")]
    start_at: Annotated[Optional[str], Field(description="Start time of the activity in ISO format")]
    end_at: Annotated[Optional[str], Field(description="End time of the activity in ISO format")]
    description: Annotated[Optional[str], Field(description="Description of the activity")]
    tags: Annotated[Optional[list[str]], Field(description="Tags associated with the activity")]

class AlertInformation(BaseModel):
    alert_type: Annotated[Optional[str], Field(description="Type of the alert (e.g., reminder, notification)")]
    title: Annotated[Optional[str], Field(description="Title of the alert")]
    message: Annotated[Optional[str], Field(description="Message content of the alert")]
    trigger_time: Annotated[Optional[str], Field(description="Time when the alert should be triggered in ISO format")]
    recurrence: Annotated[Optional[str], Field(description="Recurrence pattern of the alert (e.g., daily, weekly)")]
    priority: Annotated[Optional[str], Field(description="Priority level of the alert (e.g., high, medium, low)")]
    status: Annotated[Optional[str], Field(description="Status of the alert (e.g., active, resolved)")] 
    source: Annotated[Optional[str], Field(description="Source of the alert (e.g., user input, system generated, event, activity)")]