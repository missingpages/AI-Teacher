#!/usr/bin/env python
# coding: utf-8

import google.generativeai as genai
from langchain_core.output_parsers import JsonOutputParser
from openai import OpenAI
from langchain_core.pydantic_v1 import BaseModel, Field 
from typing import Optional
from langchain_openai import ChatOpenAI
import neo4j

# Model classes
class ConceptName(BaseModel):
    name:str = Field(description="concept name")

class Concept(BaseModel):
    concept_name:ConceptName = Field(description="concept name")
    concept_description:str = Field(description="Details of the concept discussed in the topic")
    prerequisite_to_understand:Optional[list[ConceptName]] = Field(description="List of concept names that are prerequisites to understand this concept.Must be List type",default=['NULL'])
        
class ConceptGraph(BaseModel):
    graph: list[Concept] = Field(description="The dict of all concepts found in the topic and its details")

def get_neo4j_credentials():
    """Read Neo4j credentials from config file"""
    credentials = {}
    with open('../neo4j.txt', 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            credentials[key] = value
    return credentials

def get_neo4j_driver():
    """Create and return Neo4j driver using credentials"""
    print("Initializing Neo4j connection...")
    try:
        credentials = get_neo4j_credentials()
        driver = neo4j.GraphDatabase.driver(
            credentials['NEO4J_URI'],
            auth=neo4j.basic_auth(credentials['NEO4J_USERNAME'], credentials['NEO4J_PASSWORD'])
        )
        print("✓ Neo4j connection established")
        return driver
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {str(e)}")
        raise

def execute_query(query):
    """Execute Neo4j query using driver"""
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(query)
        records = [record for record in result]
        return records

def get_llm():
    """Initialize and return LLM"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm

def extract_concept_graph(content):
    """Extract concept graph from content using LLM"""
    print("\nExtracting concepts using LLM...")
    try:
        prompt = f"""
                  you are a teacher good at finding the concepts discussed in the topic.
                  Find all the concepts discussed in the topic.
                  Provide concept name, concept description and prerequisites in such a way that can be used for teaching
                  
                  topic: {content}
                  """
        model = ChatOpenAI(model="gpt-4o", temperature=0)
        structured_llm = model.with_structured_output(ConceptGraph)
        response = structured_llm.invoke(prompt)
        print("✓ Concept extraction completed")
        return response
    except Exception as e:
        print(f"❌ Error during concept extraction: {str(e)}")
        raise

def process_concept(concept, section_name):
    """Process single concept and create Neo4j nodes"""
    try:
        concept_name = concept.concept_name.name.replace("'","`")
        print(f"\nProcessing concept: {concept_name}")
        
        concept_desc = concept.concept_description.replace("'","`")
        prerequisites = concept.prerequisite_to_understand
        
        if prerequisites is None:
            prerequisites = []
        
        prerequisites = [c.name.replace("'","`") for c in prerequisites]
        prerequisites_str = ','.join(prerequisites)
        print(f"Prerequisites found: {prerequisites_str if prerequisites_str else 'None'}")
        
        # Create concept node
        query = f"""
        MERGE (concept:CONCEPT{{
            concept_name:'{concept_name}',
            concept_description:'{concept_desc}',
            section_name:'{section_name}',
            prerequisites:'{prerequisites_str}'
        }})
        """
        execute_query(query)
        print("✓ Concept node created")
        
        # Create relationship
        rel_query = """
        MATCH (s:SECTION),(c:CONCEPT) 
        WHERE s.section_name=c.section_name 
        WITH s,c 
        MERGE (s)-[:INCLUDES]->(c)
        """
        execute_query(rel_query)
        print("✓ Relationship created")
        
    except Exception as e:
        print(f"❌ Error processing concept {concept_name}: {str(e)}")
        raise

def create_concept_graph_from_section():
    """Create concept graph from sections in Neo4j"""
    print("\nFetching sections from database...")
    query = "MATCH (s:SECTION) RETURN s.section_name as section_name, s.section_content as section_content"
    records = execute_query(query)
    print(f'✓ Found {len(records)} sections to process')
    
    for i, record in enumerate(records):
        print(f"\n{'='*50}")
        print(f"Processing section {i+1}/{len(records)}")
        print(f"Section name: {record['section_name']}")
        
        section_name = record['section_name']
        section_content = record['section_content']
        
        graph = extract_concept_graph(section_content)
        concept_list = graph.graph
        print(f"Found {len(concept_list)} concepts in this section")
        
        for j, concept in enumerate(concept_list):
            print(f"\nProcessing concept {j+1}/{len(concept_list)}")
            process_concept(concept, section_name)
        
        print(f"✓ Completed section {i+1}/{len(records)}")

def main():
    """Main function to orchestrate the concept graph creation"""
    print("\n=== Starting Concept Graph Creation ===\n")
    try:
        # Initialize Neo4j connection
        driver = get_neo4j_driver()
        
        # Create concept graph
        create_concept_graph_from_section()
        
        print("\n✓ Concept graph creation completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.close()
            print("\n✓ Neo4j connection closed")
    print("\n=== Process Complete ===")

if __name__ == "__main__":
    main()

