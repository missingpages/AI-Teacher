from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from state import State

def get_llm():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm

def chatbot(state: State):
    llm = get_llm()
    return {"messages": [llm.invoke(state["messages"])]} 