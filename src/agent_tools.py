from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from langgraph.prebuilt import ToolNode

# Import things that are needed generically
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from db import driver
from prompts import QUERY_CREATOR_PROMPT, PERSONALIZED_NARRATOR_PROMPT
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class FoundationConceptFetcher(BaseModel):
    """
    This tool is used to fetch the foundation concepts for a given topic or question asked by the student.
    """
    topic: str = Field(description="The question from the student for which the foundation concepts are to be fetched")

    def _run(self, topic: str):
        related_concepts = f""" Related Concepts for {topic} are:
        """
        concept_name, concept_description = find_similar_documents(topic)
        for name,concept in zip(concept_name,concept_description):
            related_concepts += f"""
            {name} - {concept}
            """
        print("related_concepts is", related_concepts)
        return related_concepts

class QuestionCreator(BaseModel):
    """
    This tool is used to create one or more questions based on the foundation concepts.
    """
    foundation_concepts: str = Field(description="The foundation concepts to create questions for")

    def _run(self, foundation_concepts: str):
        questions = create_questions(foundation_concepts)
        questions_combined = "\n".join(questions)
        return f"The question for {foundation_concepts} is {questions_combined}"   

class PersonalizedNarrator(BaseModel):
    """
    This tool is used to create a personalized narration based on the student's profile.
    """
    message: str = Field(description="The message to be narrated")
    profile: str = Field(description="The profile of the student")

    def _run(self, topic: str, profile: str):
        personalized_narration = create_personalized_narration(topic, profile)
        return f"The personalized narration for {topic} is {personalized_narration}"

# Function to generate embeddings from OpenAI
def generate_openai_embedding(text):
    # Call OpenAI API to get embedding for the given text
    response = client.embeddings.create(
        model="text-embedding-ada-002",  # You can choose another available model
        input=text
    )
    # Extract the embedding vector (a list of floats)
    return response.data[0].embedding

# Function to fetch similar documents based on a query
def find_similar_documents(query, top_n=3):
    # Generate the embedding for the query
    query_embedding = generate_openai_embedding(query)
    
    result = []
    with driver.session() as session:
        # Fetch all documents' embeddings from Neo4j
        result = session.run("""CALL db.index.vector.queryNodes('concept-embeddings', 3, $query_embedding)
                            YIELD node, score
                            RETURN node, score""",query_embedding=query_embedding)

        records = [(record['node']['concept_name'], record['node']['concept_description']) for record in result]
        return records


class Queries(BaseModel):
    questions: list[str] = Field(description="Questions to be asked to the student")

def create_questions(foundation_concepts):
    prompt = QUERY_CREATOR_PROMPT.format(foundation_concepts=foundation_concepts)
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = model.with_structured_output(Queries)
    response = structured_llm.invoke(prompt)
    return response.questions

def create_personalized_narration(topic, profile):
    prompt = PERSONALIZED_NARRATOR_PROMPT.format(topic=topic, profile=profile)
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = model.invoke(prompt)
    return response.content
