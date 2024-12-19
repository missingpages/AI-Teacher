from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from state import State
from langgraph.prebuilt import ToolNode
from agent_tools import QuestionCreator, FoundationConceptFetcher, PersonalizedNarrator
import json
from random import choice
from prompts import AI_TEACHER_PROMPT

tools = [QuestionCreator, FoundationConceptFetcher, PersonalizedNarrator]
tool_node = ToolNode(tools)

with open("../profiles/students.json", "r") as f:
    data = json.load(f)

student = choice(data)
persona = student['persona']

def get_llm():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm

def chatbot(state: State):
    llm = get_llm()
    profile_message = {"role": "system", "content": f"""
                        The student you are talking to is {persona['name']}. Here is their profile:
                        {json.dumps(persona, indent=4)}
                          
                        Formulate your responses in a way that engages the student and aligns with their learning style, weaknesses, and strengths, current knowledge, interests, and goals.
                        you have access to the following tools:
                        1. QuestionCreator: This tool is used to create one or more questions based on the foundation concepts and the content of the topic.
                        2. FoundationConceptFetcher: This tool is used to get the related concepts and prerequisites for the topic.
                        3. PersonalizedNarrator: This tool is used to create a personalized narration based on the student's profile.
                
                        """}
    sys_message = {"role": "system", "content": f"""
                   {AI_TEACHER_PROMPT}
                   The topic currently being taught is:
                   {state["messages"][-2].content}
                   guide the student to understand the topic.
                   """}
    messages = [sys_message,profile_message] + state["messages"]
    print("messages are", messages)
    tools = [QuestionCreator, FoundationConceptFetcher, PersonalizedNarrator]
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(messages) 
    # print("response is", response)
    return {"messages": [response]} 



def router(state: State)-> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we stop (reply to the user)
    return END