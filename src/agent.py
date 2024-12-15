from graph_builder import build_graph

def agent(message: str):
    graph = build_graph()
    print("user message is",message)
    state = {"messages": [message]}
    response = graph.invoke(state)
    response = response["messages"][-1].content
    print("agent response is", response)
    return response

