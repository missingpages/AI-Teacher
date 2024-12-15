from graph_builder import build_graph

def agent(message: str, context: dict={}):
    graph = build_graph()
    print("user message is",message)
    print("context is", context)
    sys_message = {"role": "system", "content": f"""
                   You are a AI teacher trying to help students learn about a topic. The Topic is given below:
                   Chapter Name - {context["chapter"]}
                   {context["topic"]}
                   Answer the student's questions and provide additional information to help them learn.
                   """}
    user_message = {"role": "user", "content": message}
    state = {"messages": [sys_message, user_message]}
    response = graph.invoke(state)
    response = response["messages"][-1].content
    print("agent response is", response)
    return response

