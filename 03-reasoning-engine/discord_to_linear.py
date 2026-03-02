from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import os
from dotenv import load_dotenv

# This loads the OPENAI_API_KEY from your .env file into the script
load_dotenv() 
# 1. Define the target schema (What Jira/Linear needs)
class LinearTicket(BaseModel):
    title: str = Field(description="A concise, technical title for the bug")
    priority: str = Field(description="Must be one of: 'Low', 'Medium', 'High', 'Urgent'")
    tags: List[str] = Field(description="e.g., 'frontend', 'database', 'auth'")
    steps_to_reproduce: Optional[List[str]] = Field(description="Guessed steps based on user text")
    user_sentiment: str = Field(description="e.g., 'Frustrated', 'Neutral', 'Confused'")

def process_discord_message(raw_message: str):
    print(f"📥 Received Discord Message: '{raw_message}'\n")
    
    # 2. Initialize LLM with strict JSON output
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    parser = llm.with_structured_output(LinearTicket)
    
    system_prompt = """
    You are an automated triage agent. Convert the incoming unstructured user complaint 
    into a structured Linear ticket payload. Infer priority based on their tone and the issue.
    """
    
    # 3. Extract the data
    print("🧠 Extracting structured data...")
    ticket: LinearTicket = parser.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_message}
    ])
    
    # 4. Simulate sending to Linear API
    print("✅ Successfully generated Ticket Payload:")
    print(json.dumps(ticket.model_dump(), indent=2))
    
    return ticket

if __name__ == "__main__":
    # Simulate a chaotic, non-technical user message from Discord
    messy_discord_msg = """
    Bro seriously?? I just tried to log in to the dashboard and it gave me a 500 error 
    saying 'Connection Refused'. I'm trying to export my tax report and it's due TOMORROW. 
    Fix this ASAP, I clicked the blue button on the sidebar and it just spun forever.
    """
    
    process_discord_message(messy_discord_msg)