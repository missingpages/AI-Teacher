# Socratix : Socratic AI-Teacher
Socratic Teacher is one who fosters critical thinking in students through engaging with students in thought provoking dialogue, Understand the students’ beliefs ,opinions and misconceptions with probing questions and help them find answers on their own. The teacher helps students discover truths and refine their understanding, making learning more personal and profound.

With the rise of online education platforms , we see more people pursuing their learning goals through MOOC. Online courses democratize education by providing access to high-quality content from world-renowned institutions and experts and offers flexibility. However the downside is the lack of one-one engagement we used to have with teachers in class rooms. The future of education lie in middle ground between the two, offering both flexibility and personalized engagement.

Our attempt here, as part of LLM Agents hackathon by Berkeley RDI, is to impart human elements of traditional teaching to online learning process with a virtual teacher aka socratic AI teacher. The socratic AI teacher is an agentic framework to augment the online learning with socratic teaching methods and personalized engagement.

### Pre-requisites
Requires access to
- Neo4j
- LLM APIs (by default requires openAI gpt-4o-mini for agents, Gemini for Data extraction)

## Instructions
- create conda env or python venv
- Run 'requirements.txt'
- ensure neo4j credentials are entered in 'neo4j-local.txt'
- set proper LLM key set in python env.
  - For eg. to access openAI LLM gpt-40-mini ,set OPENAI_API_KEY

- OPTIONAL : Change user persona details in profile/student.json
  One persona will be randomly picked & assumed for the student
    
- To create Knowledge base with learning materials(pdfs):
    - Run "python kb/data_pipeline.py <pdf_path>"
      This will extract all the contents from pdf, discover concepts, create concept hierarchy and then load to Neo4j. Also creates vector embedding for concept.

- To start backend api server
  - Run "python api.py"
 
- To start GUI
  - Run "python app.py"
    - This will brigng up the UI to access the learning content
