#!/usr/bin/env python
# coding: utf-8

import google.generativeai as genai
import os
import fitz
import getpass
from langchain_core.output_parsers import JsonOutputParser
import neo4j

def initialize_gemini():
    """Initialize and configure Gemini API"""
    os.environ["API_KEY"] = getpass.getpass(prompt = 'Enter the Gemini API key')
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel(model_name='gemini-1.5-pro')

def extract_toc_from_pdf(model, pdf_path):
    """Extract table of contents from PDF using Gemini"""
    sample_pdf = genai.upload_file(pdf_path)
    response = model.generate_content(["""Prepare table of contents for the given file with the page numbers given at the bottom.Include sub sections as well.
Format should be json.
For eg:
```
[{
  "chapter_no" : 1,
  "chapter_name": "FIELDS",  
  "content" :
     [{ "section_no" : "1.1"
        "section_name": "Introduction",
         "page_no" : 1,
         "sub_sections" : []
         },
         { "section_no" : "1.2"
        "section_name": "Properties",
         "page_no" : 2
         "sub_sections" : [
             {
              "sub_section_no":1.2.1,
              "sub_section_name" : "Additivity"
              "sub_section_page_no" : 4
              },
              {
              "sub_section_no":1.2.2
              "sub_section_name" : "multiply"
              "sub_section_page_no" : 4
              }
              .
              .
         ]
         },
         { "section_no" : NULL
        "section_name": "Summary",
         "page_no" : 12,
         "sub_sections" : []
         }
    ]
},
 {
  "chapter_name": "MAGNETS",
  "chapter_no" : 2,
  contents: [
  ...
  ]
 }      
]
```
Do not hallucinate.
""", sample_pdf])
    return response.text

def parse_toc_json(response_text):
    """Parse TOC JSON and add subject information"""
    parser = JsonOutputParser()
    toc = parser.invoke(response_text)
    toc = {'subject':'physics', 'subject_content':toc}
    return toc

def remove_quotes_from_dict(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = remove_quotes_from_dict(value)
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = remove_quotes_from_dict(data[i])
    elif isinstance(data, str):
        data = data.replace("'", "").replace('"', "")
    return data

def clean_property_value(value):
    if value is None:
        return ""
    cleaned_value = str(value).replace("'", "")
    return cleaned_value

def get_neo4j_credentials():
    """Read Neo4j credentials from config file"""
    credentials = {}
    with open('neo4j-local.txt', 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            credentials[key] = value
    return credentials

def execute_query(query):
    """Execute a Neo4j query using credentials from config file"""
    credentials = get_neo4j_credentials()
    uri = credentials['NEO4J_URI']
    username = credentials['NEO4J_USERNAME']
    password = credentials['NEO4J_PASSWORD']
    
    driver = neo4j.GraphDatabase.driver(uri, auth=neo4j.basic_auth(username, password))
    with driver.session() as session:
        result = session.run(query)
        return result

def insert_nested_dict_to_neo4j(data, key_to_insert, node_label, primary_key, parent_label=None, parent_primary_key=None, parent_node=None, parent_props=None):
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                insert_nested_dict_to_neo4j(
                    item, key_to_insert, node_label, primary_key,
                    parent_label, parent_primary_key, parent_node, parent_props
                )
        return

    if isinstance(data, dict):
        current_props = {k: clean_property_value(v) for k, v in data.items() 
                       if not isinstance(v, (dict, list))}
        all_props = {**(parent_props or {}), **current_props}

        for key, value in data.items():
            if key == key_to_insert:
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            filtered_item = {k: clean_property_value(v) for k, v in item.items() 
                                          if not isinstance(v, list)}
                            
                            node_props = {**all_props, **filtered_item}
                            props_dict = {k: v for k, v in node_props.items() 
                                        if k != primary_key}
                            props_str = ", ".join([f"{k}: '{v}'" for k, v in props_dict.items()])
                            
                            if parent_label and parent_primary_key:
                                parent_key_value = all_props.get(parent_primary_key)
                                if parent_key_value:
                                    query = f"""
                                    MATCH (parent:{parent_label} {{{parent_primary_key}: '{parent_key_value}'}})
                                    MERGE (n:{node_label} {{{primary_key}: '{filtered_item[primary_key]}'}})
                                    ON CREATE SET n += {{{props_str}}}
                                    ON MATCH SET n += {{{props_str}}}
                                    MERGE (parent)-[:HAS_{key}]->(n)
                                    """
                                else:
                                    print(f"Warning: Parent primary key {parent_primary_key} not found in properties")
                                    continue
                            else:
                                query = f"""
                                MERGE (n:{node_label} {{{primary_key}: '{filtered_item[primary_key]}'}})
                                ON CREATE SET n += {{{props_str}}}
                                ON MATCH SET n += {{{props_str}}}
                                """
                            execute_query(query)
            
            elif isinstance(value, (dict, list)):
                insert_nested_dict_to_neo4j(
                    value, key_to_insert, node_label, primary_key,
                    parent_label, parent_primary_key, key, all_props
                )

def find_nested_list(data, list_key):
    found_lists = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            if key == list_key and isinstance(value, list):
                found_lists.append(value)
            if isinstance(value, (dict, list)):
                found_lists.extend(find_nested_list(value, list_key))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                found_lists.extend(find_nested_list(item, list_key))
                
    return found_lists

def create_sequential_relationships(data, list_key, node_label, primary_key):
    all_lists = find_nested_list(data, list_key)
    if not all_lists:
        return
    
    for items in all_lists:
        for i in range(len(items) - 1):
            current_item = items[i]
            next_item = items[i + 1]
            
            query = f"""
            MATCH (current:{node_label}), (next:{node_label})
            WHERE current.{primary_key} = '{current_item[primary_key]}' 
            AND next.{primary_key} = '{next_item[primary_key]}'
            MERGE (current)-[:NEXT]->(next)"""
            
            execute_query(query)

def main(pdf_path):
    """
    Extract TOC from PDF and create knowledge graph
    Args:
        pdf_path: Path to the PDF file
    """
    print(f"\n[1/6] Initializing Gemini API...")
    model = initialize_gemini()
    
    print(f"[2/6] Extracting table of contents from {pdf_path}...")
    toc_text = extract_toc_from_pdf(model, pdf_path)
    
    print("[3/6] Parsing TOC JSON and processing data...")
    toc = parse_toc_json(toc_text)
    toc = remove_quotes_from_dict(toc)
    print(toc)
    
    print("[4/6] Creating chapter nodes in Neo4j...")
    insert_nested_dict_to_neo4j(
        data=toc,
        key_to_insert="subject_content",
        node_label="CHAPTER",
        primary_key="chapter_name"
    )
    
    print("[5/6] Creating section nodes and relationships...")
    insert_nested_dict_to_neo4j(
        data=toc,
        key_to_insert="content",
        node_label="SECTION",
        primary_key="section_name",
        parent_label="CHAPTER",
        parent_primary_key="chapter_name"
    )
    
    print("[5/6] Creating subsection nodes and relationships...")
    insert_nested_dict_to_neo4j(
        data=toc,
        key_to_insert="sub_sections",
        node_label="SUBSECTION",
        primary_key="sub_section_name",
        parent_label="SECTION",
        parent_primary_key="section_name"
    )
    
    print("[6/6] Creating sequential relationships...")
    print("  - Creating section sequences...")
    create_sequential_relationships(
        data=toc,
        list_key='content',
        node_label='SECTION',
        primary_key='section_name'
    )
    
    print("  - Creating subsection sequences...")
    create_sequential_relationships(
        data=toc,
        list_key='sub_sections',
        node_label='SUBSECTION',
        primary_key='sub_section_name'
    )
    
    print("\n✅ TOC extraction and knowledge graph creation completed successfully!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python TOCExtractor.py <pdf_path>")
        sys.exit(1)
    main(sys.argv[1])


