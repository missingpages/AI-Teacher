# Socratix - Socratic AI Teacher
Socratic Teacher is one who fosters critical thinking in students through engaging with students in thought provoking dialogue, Understand the students’ beliefs ,opinions and misconceptions with probing questions and help them find answers on their own. The teacher helps students discover truths and refine their understanding, making learning more personal and profound.

With the rise of online education platforms , we see more people pursuing their learning goals through MOOC. Online courses democratize education by providing access to high-quality content from world-renowned institutions and experts and offers flexibility. However the downside is the lack of one-one engagement we used to have with teachers in class rooms. The future of education lie in middle ground between the two, offering both flexibility and personalized engagement.

Our attempt here, as part of LLM Agents hackathon by Berkeley RDI, is to impart human elements of traditional teaching to online learning process with a virtual teacher aka socratic AI teacher. The socratic AI teacher is an agentic framework to augment the online learning with socratic teaching methods and personalized engagement.
## Features
### 1. Personalized teaching
![Personalization](images/PersonalizedTeaching-eg.png)

### 2. Socratic Teaching 
<img src="images/foundationConcepts-eg.png" alt="Socratic" width="250" height="500">


For eg. To know the concept of **'electric flux'**, understanding of **'electric field'** is important!

Ofcourse, the response is personalized to students likings towards **poetry**!
    
## Pre-requisites
Requires access to
- Neo4j
- LLM APIs (by default requires openAI gpt-4o-mini for agents, Gemini for Data extraction)

## Instructions
- create conda env or python venv
- Run 'requirements.txt'
- ensure neo4j credentials are entered in 'neo4j-local.txt'
- set OpenAI API key as an environment variable OPENAI_API_KEY.
- set Google API key as an environment variable GEMINI_API_KEY.
  
- OPTIONAL : Change user persona details in profile/student.json
  One persona will be randomly picked & assumed for the student
    
- To create Knowledge base with learning materials(pdfs):
    - cd into src/kb
    - Run "python data_pipeline.py <pdf_path>"
      This will extract all the contents from pdf, discover concepts, create concept hierarchy and then load to Neo4j. Also creates vector embedding for concept.
    - Sample pdf files used in demo are available in **sample-data** folder

- To start backend api server
  - cd into src
  - Run "python api.py"
    The backend api service will be available at http://127.0.0.1:5000
 
- To start GUI
  - cd into src
  - Run "python app.py"
    - This will bring up the UI to access the learning content
    - The UI can be accessed through the url - http://127.0.0.1:8050
