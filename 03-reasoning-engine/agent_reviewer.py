import subprocess
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# This loads the OPENAI_API_KEY from your .env file into the script
load_dotenv() 
# 1. Define the AI-Native Data Structures (Pydantic)
class CodeIssue(BaseModel):
    file_name: str = Field(description="The file where the issue was found")
    line_number: str = Field(description="Approximate line number or function name")
    issue_type: str = Field(description="e.g., 'Security', 'Performance', 'Style'")
    description: str = Field(description="Description of the issue")
    suggestion: str = Field(description="Suggested code fix")

class ReviewOutput(BaseModel):
    summary: str = Field(description="A brief summary of the changes in this diff")
    issues: List[CodeIssue]

# 2. Define the Graph State
class AgentState(TypedDict):
    diff_content: str
    parsed_review: ReviewOutput
    final_markdown: str

# 3. Define the Nodes (The Agent's Actions)
def fetch_local_diff(state: AgentState) -> dict:
    """Uses local git to fetch the diff against the main branch."""
    print("🤖 Agent: Fetching local git diff...")
    try:
        # Gets the diff between the current state and the main branch
        result = subprocess.run(['git', 'diff', 'main'], capture_output=True, text=True)
        diff = result.stdout
        if not diff:
            diff = "No differences found."
    except Exception as e:
        diff = f"Error fetching diff: {e}"
    
    return {"diff_content": diff[:15000]} # Truncate for token limits if necessary

def analyze_diff(state: AgentState) -> dict:
    """Uses LLM with Structured Output to analyze the code."""
    print("🧠 Agent: Analyzing diff for bugs and security issues...")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    # FORCING the LLM to output our exact Pydantic schema (AI-Native best practice)
    structured_llm = llm.with_structured_output(ReviewOutput) 
    
    prompt = f"""
    You are an expert Senior Staff Software Engineer. 
    Review the following git diff. Focus on security, performance, and logic bugs.
    
    DIFF:
    {state['diff_content']}
    """
    
    review_data = structured_llm.invoke(prompt)
    return {"parsed_review": review_data}

def generate_report(state: AgentState) -> dict:
    """Formats the structured data into a readable CLI report."""
    print("📝 Agent: Generating final report...")
    review = state['parsed_review']
    
    md_report = f"# 🕵️‍♂️ AI Code Review \n\n**Summary:** {review.summary}\n\n"
    if not review.issues:
        md_report += "✅ No issues found! Ship it."
    else:
        for issue in review.issues:
            md_report += f"### ⚠️ {issue.issue_type} in `{issue.file_name}`\n"
            md_report += f"- **Location:** {issue.line_number}\n"
            md_report += f"- **Issue:** {issue.description}\n"
            md_report += f"- **Fix:** {issue.suggestion}\n\n"
            
    return {"final_markdown": md_report}

# 4. Compile the Graph
workflow = StateGraph(AgentState)

workflow.add_node("fetch_diff", fetch_local_diff)
workflow.add_node("analyze_diff", analyze_diff)
workflow.add_node("generate_report", generate_report)

workflow.set_entry_point("fetch_diff")
workflow.add_edge("fetch_diff", "analyze_diff")
workflow.add_edge("analyze_diff", "generate_report")
workflow.add_edge("generate_report", END)

app = workflow.compile()

# To run it:
if __name__ == "__main__":
    result = app.invoke({"diff_content": "", "parsed_review": None, "final_markdown": ""})
    print("\n\n" + result["final_markdown"])