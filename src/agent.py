from graph_builder import build_graph

import json
from random import choice

with open("..\profiles\students.json", "r") as f:
    data = json.load(f)

student = choice(data)
persona = student['persona']


def agent(message: str, context: dict={}):
    graph = build_graph()
    print("user message is",message)
    print("context is", context)
    profile_message = {"role": "system", "content": f"""
The student you are talking to is {persona['name']}. Here is their profile:
{json.dumps(persona, indent=4)}

Formulate your responses in a way that engages the student and aligns with their learning style, weaknesses, and strengths, current knowledge, interests, and goals.
"""}
    sys_message = {"role": "system", "content": f"""
                   You are a AI teacher trying to help students learn about a topic. The Topic is given below:
                   Chapter Name - {context["chapter"]}
                   {context["topic"]}
                   Answer the student's questions and provide additional information to help them learn.
                   """}
    user_message = {"role": "user", "content": message}
    state = {"messages": [sys_message,profile_message, user_message]}
    response = graph.invoke(state)
    response = response["messages"][-1].content
    print("agent response is", response)
    return response

