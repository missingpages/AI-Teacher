#!/usr/bin/env python
# coding: utf-8

import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
from openai import OpenAI
import os
import configparser

def load_neo4j_config(config_file):
    """Load Neo4j configuration from file"""
    print("Loading Neo4j configuration...")
    with open(config_file, 'r') as f:
        config = {}
        for line in f:
            key, value = line.strip().split('=')
            config[key] = value
    return config

def init_neo4j_driver(uri, username, password):
    """Initialize Neo4j driver"""
    print(f"Initializing Neo4j connection to {uri}...")
    return GraphDatabase.driver(uri, auth=(username, password))

def init_openai_client():
    """Initialize OpenAI client"""
    print("Initializing OpenAI client...")
    return OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def generate_openai_embedding(client, text):
    """Generate embeddings using OpenAI API"""
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

def store_embeddings_in_neo4j(driver, openai_client):
    """Store embeddings for all concepts in Neo4j"""
    print("Starting to store embeddings in Neo4j...")
    with driver.session() as session:
        result = session.run("MATCH (c:CONCEPT) RETURN c.concept_name AS name, c.concept_description AS description")
        
        for i, record in enumerate(result):
            name = record["name"]
            content = record["description"]
            print(f"Processing concept {i+1}: {name}")

            embedding = generate_openai_embedding(openai_client, content)

            session.run("""
                MATCH (c:CONCEPT {concept_name: $name})
                CALL db.create.setNodeVectorProperty(c, 'embedding', $embedding)
                """, name=name, embedding=embedding)
            
    print("Successfully stored all embeddings in Neo4j!")

def find_similar_documents(driver, openai_client, query, top_n=3):
    """Find similar documents based on query"""
    print(f"Searching for documents similar to query: {query}")
    query_embedding = generate_openai_embedding(openai_client, query)
    
    with driver.session() as session:
        result = session.run("""
            CALL db.index.vector.queryNodes('concept-embeddings', $top_n, $query_embedding)
            YIELD node, score
            RETURN node, score
            """, 
            top_n=top_n,
            query_embedding=query_embedding
        )
        records = [(record['node']['concept_name'], record['node']['concept_description']) 
                  for record in result]
        print(f"Found {len(records)} similar documents")
        return records

def generate_answer_with_rag(query, top_n=3):
    """Generate answer using RAG approach"""
    print(f"Generating RAG answer for query: {query}")
    similar_docs = find_similar_documents(query, top_n)
    context = "\n".join([f"Document {doc_id}: {content}" for doc_id, _ in similar_docs])

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Question: {query}\nContext: {context}\nAnswer:",
        max_tokens=150
    )
    return response.choices[0].text.strip()

def create_vector_index(driver, index_name, label, property_name, dimensions=1536):
    """
    Create a vector index in Neo4j
    
    Parameters:
    - driver: Neo4j driver instance
    - index_name: Name of the index to create
    - label: Node label to index
    - property_name: Property that contains the vector
    - dimensions: Dimension of the vectors (default 1536 for OpenAI ada-002)
    """
    print(f"Creating vector index '{index_name}' for {label}.{property_name}...")
    
    with driver.session() as session:
        try:
            # Check if index already exists
            result = session.run("""
                SHOW INDEXES
                YIELD name, type
                WHERE name = $index_name
                RETURN count(*) as count
                """, 
                index_name=index_name
            )
            
            if result.single()['count'] > 0:
                print(f"Index '{index_name}' already exists")
                return
            
            # Create the vector index
            query = f"""
                CREATE VECTOR INDEX `{index_name}`
                FOR (n: {label}) ON (n.{property_name})
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {dimensions},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
            """
            session.run(query)
            print(f"Successfully created vector index '{index_name}'")
            
        except Exception as e:
            print(f"Error creating vector index: {str(e)}")

def main():
    # Initialize configurations and clients
    config = load_neo4j_config('neo4j-local.txt')
    driver = init_neo4j_driver(
        config['NEO4J_URI'],
        config['NEO4J_USERNAME'],
        config['NEO4J_PASSWORD']
    )
    openai_client = init_openai_client()

    try:
        # Create vector index if it doesn't exist
        create_vector_index(
            driver,
            index_name='concept-embeddings',
            label='CONCEPT',
            property_name='embedding'
        )
        
        # Store embeddings
        store_embeddings_in_neo4j(driver, openai_client)

        # Example query
        # query = "can you explain about Electric Flux"
        # similar_docs = find_similar_documents(driver, openai_client, query)
        # print("\nSimilar documents found:")
        # for name, description in similar_docs:
        #     print(f"\nConcept: {name}")
        #     print(f"Description: {description[:200]}...")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        driver.close()
        print("Neo4j connection closed")

if __name__ == "__main__":
    main()


# In[ ]:




