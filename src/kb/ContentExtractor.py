#!/usr/bin/env python
# coding: utf-8

import google.generativeai as genai
import os
import fitz
from langchain_core.output_parsers import JsonOutputParser
import neo4j
import time
import argparse

def load_neo4j_config(config_file="neo4j-local.txt"):
    """Load Neo4j credentials from config file"""
    config = {}
    with open(config_file, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            config[key] = value
    return config

def initialize_gemini(api_key):
    """Initialize Gemini AI model"""
    os.environ["API_KEY"] = api_key
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel(model_name='gemini-2.0-flash-exp')

def execute_query(query, uri, username, password):
    """Execute Neo4j query"""
    driver = neo4j.GraphDatabase.driver(uri, auth=neo4j.basic_auth(username, password))
    with driver.session() as session:
        result = session.run(query)
        return result

def extract_content_from_pdf(section_name, model, pdf_path="leph102.pdf"):
    """Extract content from PDF for given section"""
    sample_pdf = genai.upload_file(pdf_path)
    prompt = """From the given pdf, extract and print the content of the section given.
    Extract the full content of the section even if it spans multiple pages.
    Extract all the content till the next section starts.
    Do not hallucinate. Do not include any prefix or suffix. Do not include ``` or markdown prefix.
    
    The output should contain entire content. section no and title can be skipped.
    Output needs to be in markdown format. 
    
    section to be extracted : {section_name}
    """
    
    prompt = prompt.format(section_name=section_name)
    response = model.generate_content([prompt, sample_pdf], request_options={"timeout": 1000})
    print(response.text)
    return response.text

def clean_property_value(value):
    """Clean property value by removing/escaping quotes"""
    if value is None:
        return ""
    return str(value).replace("'", "")

def remove_quotes_from_dict(data):
    """Remove quotes from dictionary values recursively"""
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = remove_quotes_from_dict(value)
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = remove_quotes_from_dict(data[i])
    elif isinstance(data, str):
        data = data.replace("'", "").replace('"', "")
    return data

def update_sections_with_content(model, neo4j_config, pdf_path="leph102.pdf"):
    """Updates Neo4j SECTION nodes with content extracted from PDF for all chapters"""
    # Query to get all chapters and their sections
    query = """
    MATCH (c:CHAPTER)-[:HAS_content]->(s:SECTION)
    RETURN c.chapter_name as chapter_name, s.section_name as section_name
    """
    
    with neo4j.GraphDatabase.driver(
        neo4j_config['NEO4J_URI'],
        auth=neo4j.basic_auth(neo4j_config['NEO4J_USERNAME'], neo4j_config['NEO4J_PASSWORD'])
    ) as driver:
        with driver.session() as session:
            result = session.run(query)
            chapter_sections = [(record["chapter_name"], record["section_name"]) 
                              for record in result.data()]
    
    print(f"Found {len(chapter_sections)} sections across all chapters")
    
    for chapter_name, section_name in chapter_sections:
        try:
            print(f"\nProcessing chapter: {chapter_name}, section: {section_name}")
            section_content = extract_content_from_pdf(section_name, model, pdf_path)
            time.sleep(30)
            print("Sleep completed!")
            
            cleaned_content = clean_property_value(str(section_content))
            
            update_query = f"""
            MATCH (s:SECTION {{section_name: '{section_name}', chapter_name: '{chapter_name}'}})
            SET s.section_content = '{cleaned_content}'
            """
            
            print(f"Updating content for section: {section_name}")
            execute_query(update_query, neo4j_config['NEO4J_URI'], 
                        neo4j_config['NEO4J_USERNAME'], 
                        neo4j_config['NEO4J_PASSWORD'])
            
        except Exception as e:
            print(f"Error processing section {section_name} in chapter {chapter_name}: {str(e)}")
            continue

def main(pdf_path):
    """
    Main function to extract content from PDF and update Neo4j database
    Args:
        pdf_path: Path to the PDF file
    """
    # Load Neo4j configuration
    neo4j_config = load_neo4j_config()
    
    # Get Gemini API key
    api_key = input('Enter the Gemini API key: ')
    
    # Initialize Gemini model
    model = initialize_gemini(api_key)
    
    # Update sections with content
    update_sections_with_content(
        model=model,
        neo4j_config=neo4j_config,
        pdf_path=pdf_path
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract content from PDF and update Neo4j database')
    parser.add_argument('pdf_path', type=str, help='Path to the PDF file')
    
    args = parser.parse_args()
    main(args.pdf_path)

