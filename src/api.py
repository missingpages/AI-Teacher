from flask import Flask, jsonify, request
from flask_cors import CORS
from neo4j import GraphDatabase
from typing import List, Dict, Any
import requests
import traceback
from agent import agent  # Add this import at the top

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Add this to store chat messages (in a real app, you'd use a database)
chat_messages = []

def execute_neo4j_query(cypher_query: str, parameters: dict = None) -> List[Dict[str, Any]]:
    """
    Execute a Cypher query on Neo4j database and return the results.
    
    Args:
        cypher_query (str): The Cypher query to execute
        parameters (dict, optional): Parameters for the query. Defaults to None.
    
    Returns:
        List[Dict[str, Any]]: List of results where each result is a dictionary
    """
    # Database credentials
    URI = "neo4j+s://a83594c4.databases.neo4j.io"
    USERNAME = "neo4j"
    PASSWORD = "nXh9u6nEUPJKLVnyuzxe7NDgeCVJCYBoFX1NDJan9pw"
    
    # Initialize the results list
    results = []
    
    try:
        # Create a driver instance
        driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
        
        # Create a session
        with driver.session() as session:
            # Execute the query
            result = session.run(cypher_query, parameters or {})
            
            # Convert results to a list of dictionaries
            for record in result:
                results.append(dict(record))
                
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise
        
    finally:
        # Close the driver
        if 'driver' in locals():
            driver.close()
    
    return results

@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    query = """
    MATCH (c:CHAPTER)
    OPTIONAL MATCH (c)-[:HAS_content]->(s:SECTION)
    WITH c, collect(s) as sections
    RETURN collect({
        chapter_name: c.chapter_name,
        chapter_no: c.chapter_no,
        topics: [section IN sections | {
            section_name: section.section_name,
            title: section.section_name,
            content: toString(section.page_no)
        }]
    }) as chapters
    """
    
    try:
        results = execute_neo4j_query(query)
        print("Raw Neo4j results:", results)  # Debug print
        
        if results and len(results) > 0:
            chapters = results[0].get('chapters', [])
            # Filter out any null or empty chapters
            chapters = [chapter for chapter in chapters if chapter.get('chapter_name')]
            print("Found chapters:", chapters)  # Debug print
            return jsonify(chapters)
        
        print("No chapters found in database")  # Debug print
        return jsonify([])
        
    except Exception as e:
        print(f"Error in get_chapters: {str(e)}")  # Debug print
        traceback.print_exc()  # Print full stack trace
        return jsonify({'error': str(e)}), 500

@app.route('/api/chapters/<chapter_name>', methods=['GET'])
def get_chapter(chapter_name):
    query = """
    MATCH (c:CHAPTER {chapter_name: $chapter_name})
    OPTIONAL MATCH (c)-[:HAS_content]->(s:SECTION)
    WITH c, collect(s) as sections
    RETURN {
        chapter_name: c.chapter_name,
        chapter_no: c.chapter_no,
        topics: [section IN sections | {
            section_name: section.section_name,
            title: section.section_name,
            content: section.section_content,
            section_no: section.section_no
        }]
    } as result
    """
    
    try:
        # URL decode the chapter_name
        decoded_chapter_name = requests.utils.unquote(chapter_name)
        print(f"Looking for chapter: {decoded_chapter_name}")  # Debug print
        
        results = execute_neo4j_query(query, {"chapter_name": decoded_chapter_name})
        print("Raw Neo4j results:", results)  # Debug print
        
        if results and len(results) > 0 and results[0] is not None:
            result = results[0]
            print("API Response:", result)  # Debug print
            return jsonify(result)
            
        print("No results found for chapter:", decoded_chapter_name)  # Debug print
        return jsonify({'error': 'Chapter not found', 'chapter_name': decoded_chapter_name}), 404
        
    except Exception as e:
        print(f"Error in get_subject: {str(e)}")  # Debug print
        traceback.print_exc()  # Print full stack trace
        return jsonify({'error': str(e)}), 500

@app.route('/api/topic/<section_name>', methods=['GET'])
def get_topic(section_name):
    query = """
    MATCH (s:SECTION {section_name: $section_name})
    RETURN {
        section_name: s.section_name,
        title: s.section_name,
        content: s.section_content,
        section_no: s.section_no
    } as section
    """
    
    try:
        # URL decode the section_name
        decoded_section_name = requests.utils.unquote(section_name)
        print(f"Looking for section: {decoded_section_name}")  # Debug print
        
        results = execute_neo4j_query(query, {"section_name": decoded_section_name})
        if results and len(results) > 0:
            return jsonify(results[0])
        return jsonify({'error': 'Section not found'}), 404
    except Exception as e:
        print(f"Error in get_topic: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    try:
        # Get response from AI agent
        ai_response = agent(message)
        # print("ai response is",ai_response)
        # Store the conversation in chat history
        chat_messages.append({"user": message, "ai": ai_response})
        
        return jsonify({"response": ai_response})
        
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    return jsonify(chat_messages)

@app.route('/api/debug/chapters', methods=['GET'])
def debug_chapters():
    query = """
    MATCH (c:CHAPTER)
    RETURN collect({
        chapter_name: c.chapter_name,
        chapter_no: c.chapter_no
    }) as chapters
    """
    
    try:
        results = execute_neo4j_query(query)
        print("Debug - Raw chapter results:", results)
        return jsonify(results[0] if results else {'error': 'No chapters found'})
    except Exception as e:
        print(f"Debug - Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
