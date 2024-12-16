import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
from openai import OpenAI
import os

# Neo4j connection setup
from dotenv import load_dotenv
load_dotenv('neo4j.txt')

# Set credentials from environment variables
uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USERNAME') 
password = os.getenv('NEO4J_PASSWORD')

driver = GraphDatabase.driver(uri, auth=(user, password))