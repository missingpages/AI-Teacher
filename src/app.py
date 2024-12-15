import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import requests
import traceback

# Initialize the Dash app
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# API base URL
API_BASE_URL = 'http://localhost:5000/api'

# Create flashcard function now fetches data from API
def create_flashcard(chapter_card):
    # Add debugging print
    print("Creating flashcard for:", chapter_card)
    
    # Use chapter_name as the identifier
    chapter_name = chapter_card.get("chapter_name", "Unknown Chapter")
    topics = chapter_card.get("topics", [])
    
    return dbc.Col(
        dcc.Link(
            html.Div(
                [
                    html.Div(chapter_name, className="subject"),
                    html.Div(f"{len(topics)} Topics", className="title"),
                    html.Div("Click to explore topics", className="content"),
                ],
                className="flashcard"
            ),
            href=f'/subject/{requests.utils.quote(chapter_name)}',  # URL encode the chapter_name
            style={'text-decoration': 'none'}
        ),
        width=3,
        style={'min-width': '300px'}
    )

# Update the main layout and display_page callback
# Add this after your app initialization
main_layout = html.Div([
    html.H1("Socratix", 
            className="page-title",
            style={
                'textAlign': 'center', 
                'marginBottom': '30px',
                'fontSize': '3.5rem'
            }),
    dbc.Container([
        dbc.Row([
            dbc.Col(
                html.Button(
                    html.I(className="fas fa-chevron-left"),
                    id='scroll-left',
                    className='scroll-button left'
                ),
                width=1,
                className="d-flex align-items-center justify-content-center"
            ),
            dbc.Col(
                dbc.Row(
                    id='cards-row',
                    className="flex-nowrap",
                    style={'overflow-x': 'hidden'}
                ),
                width=10,
                className="px-0"
            ),
            dbc.Col(
                html.Button(
                    html.I(className="fas fa-chevron-right"),
                    id='scroll-right',
                    className='scroll-button right'
                ),
                width=1,
                className="d-flex align-items-center justify-content-center"
            ),
        ], className="align-items-center")
    ], fluid=True, className="cards-container", id='cards-container')
])

# Add a dcc store to hold chat context
context = dcc.Store(id='context', data={})

# Add this layout definition
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    context,
    html.Div(id='page-content')
])

# Update the display_page callback
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/':
        return main_layout
    elif pathname.startswith('/subject/'):
        return topic_layout
    return html.Div('404 - Not found')

# Add a new callback to populate the cards
@app.callback(
    Output('cards-row', 'children'),
    [Input('url', 'pathname')]
)
def update_cards(pathname):
    if pathname == '/':
        try:
            response = requests.get(f'{API_BASE_URL}/chapters')
            if response.status_code == 200:
                chapters = response.json()
                #print("Received chapters:", chapters)  # Debug print
                
                # Create flashcards from the chapters
                flashcards = []
                for chapter in chapters:
                    if isinstance(chapter, dict):
                        flashcards.append(create_flashcard(chapter))
                
                return flashcards
            else:
                print(f"API Error: Status {response.status_code}")
                return [html.Div(f"Error: Could not fetch chapters (Status: {response.status_code})")]
        except Exception as e:
            print(f"Error in update_cards: {str(e)}")
            return [html.Div(f"An unexpected error occurred: {str(e)}")]
    return []

# Make sure you have all your CSS styles
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Socratix</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Ubuntu:ital,wght@0,300;0,400;0,500;0,700;1,300;1,400;1,500;1,700&display=swap" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #9d174d, #4c1d95);
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }
            .page-title {
                font-family: 'Bebas Neue', sans-serif;
                color: white;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                letter-spacing: 2px;
            }
            .flashcard {
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease;
                min-height: 200px;
            }
            .flashcard:hover {
                transform: translateY(-5px);
            }
            .subject {
                color: #be185d;
                font-weight: bold;
                margin-bottom: 10px;
                font-family: 'Ubuntu', sans-serif;
            }
            .title {
                color: #4c1d95;
                font-size: 1.2em;
                margin-bottom: 10px;
                font-family: 'Ubuntu', sans-serif;
            }
            .content {
                color: #64748b;
                font-family: 'Ubuntu', sans-serif;
            }
            .scroll-button {
                background: none;
                border: none;
                color: white;
                font-size: 2rem;
                cursor: pointer;
                transition: transform 0.3s ease;
                padding: 10px;
            }
            .scroll-button:hover {
                transform: scale(1.2);
            }
            .scroll-button:focus {
                outline: none;
            }
            .cards-container {
                position: relative;
            }
            #cards-row {
                scroll-behavior: smooth;
            }
            /* Add all your other styles here */
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

@app.callback(
    [Output('subject-title', 'children'),
     Output('topics-nav', 'children'),
     Output('topic-content', 'children'), 
     Output('context', 'data')],
    [Input('url', 'pathname')]
)
def update_page_content(pathname):
    if pathname.startswith('/subject/'):
        try:
            # Extract chapter name from URL
            chapter_name = pathname.split('/')[2]
            chapter_name = requests.utils.unquote(chapter_name)
            print(f"Fetching topics for chapter: {chapter_name}")  # Debug print
            
            # Fetch chapter data from API - Updated endpoint
            response = requests.get(f'{API_BASE_URL}/chapters/{chapter_name}')  # Changed from /subject/
            data = response.json()['result']
            #print("Received chapter data:", data)  # Debug print
            
            if data and 'error' not in data:
                # Create navigation links for topics
                nav_links = [
                    dbc.NavLink(
                        topic['title'],  # Using title for display
                        href=f"/subject/{requests.utils.quote(chapter_name)}/topic/{requests.utils.quote(topic['section_name'])}",
                        id=f"topic-link-{topic['section_name']}",
                        style={
                            'color': 'white',
                            'fontFamily': "'Ubuntu', sans-serif"
                        }
                    ) for topic in data.get('topics', [])
                ]
                
                # Get section_name from URL or use first topic
                parts = pathname.split('/')
                topics = data.get('topics', [])
                
                if len(parts) >= 5:
                    section_name = requests.utils.unquote(parts[4])
                    
                    # Find the current topic in the topics list
                    current_topic = next(
                        (t for t in topics if t['section_name'] == section_name),  # Changed from title to section_name
                        topics[0] if topics else {'title': 'No topics available', 'content': ''}
                    )
                elif topics:
                    current_topic = topics[0]
                else:
                    current_topic = {'title': 'No topics available', 'content': ''}
                
                # Find current topic index
                current_index = next(
                    (i for i, t in enumerate(topics) if t['section_name'] == current_topic['section_name']), 
                    0
                )
                prev_topic = topics[current_index - 1] if current_index > 0 else None
                next_topic = topics[current_index + 1] if current_index < len(topics) - 1 else None
                
                topic_content = create_topic_content(chapter_name, current_topic, prev_topic, next_topic)
                
                return chapter_name, nav_links, topic_content, {'chapter': chapter_name, 'topic': current_topic.get('content')}
                
        except Exception as e:
            print(f"Error in update_page_content: {str(e)}")  # Debug print
            traceback.print_exc()  # Add this for better error tracking
            return f"Error: {chapter_name}", [], f"Error loading content: {str(e)}", {}
            
    return "Topics", [], "Select a topic", {}

def create_topic_content(chapter_name, current_topic, prev_topic, next_topic):
    content = current_topic.get('content', 'No content available')
    
    # Ensure headers have proper spacing
    formatted_content = content.replace('###', '### ')
    
    # Process the content line by line
    lines = formatted_content.splitlines()
    processed_lines = []
    current_paragraph = []
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            if current_paragraph:
                # Join the current paragraph and add it to processed lines
                processed_lines.append(' '.join(current_paragraph))
                current_paragraph = []
            continue
            
        # Remove extra spaces
        line = line.strip()
        
        # If it's a header, add the current paragraph and then the header
        if line.startswith('#'):
            if current_paragraph:
                processed_lines.append(' '.join(current_paragraph))
                current_paragraph = []
            if processed_lines:  # Add extra line before header except for first one
                processed_lines.append('')
            processed_lines.append(line)
        else:
            # Add line to current paragraph
            current_paragraph.append(line)
    
    # Add any remaining paragraph
    if current_paragraph:
        processed_lines.append(' '.join(current_paragraph))
    
    # Join all lines with newlines
    formatted_content = '\n'.join(processed_lines)

    return html.Div([
        dbc.Row([
            dbc.Col(
                dcc.Link(
                    html.I(className="fas fa-chevron-left fa-2x"),
                    href=f"/subject/{chapter_name}/topic/{prev_topic['section_name']}" if prev_topic else "#",
                    style={
                        'color': '#4c1d95' if prev_topic else '#ccc',
                        'pointerEvents': 'auto' if prev_topic else 'none'
                    }
                ),
                width=1,
                style={'textAlign': 'center', 'alignSelf': 'center'}
            ),
            dbc.Col(
                html.H2(
                    current_topic.get('title', 'No Title'),
                    className="mb-4",
                    style={
                        'color': 'white',
                        'fontFamily': "'Bebas Neue', sans-serif",
                        'letterSpacing': '2px'
                    }
                ),
                width=10,
                style={'textAlign': 'center'}
            ),
            dbc.Col(
                dcc.Link(
                    html.I(className="fas fa-chevron-right fa-2x"),
                    href=f"/subject/{chapter_name}/topic/{next_topic['section_name']}" if next_topic else "#",
                    style={
                        'color': '#4c1d95' if next_topic else '#ccc',
                        'pointerEvents': 'auto' if next_topic else 'none'
                    }
                ),
                width=1,
                style={'textAlign': 'center', 'alignSelf': 'center'}
            ),
        ], className="mb-4", align="center"),
        html.Div(
            dcc.Markdown(
                formatted_content,
                dangerously_allow_html=True,
                style={
                    'fontSize': '1.2rem',
                    'lineHeight': '1.6',
                    'whiteSpace': 'pre-wrap',
                    'fontFamily': "'Ubuntu', sans-serif",
                    'textAlign': 'justify',
                    'padding': '0 1rem'
                }
            ),
            className="topic-card",
            style={
                'padding': '2rem',
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'minHeight': '200px',
                'textAlign': 'left',
                'overflow': 'auto'
            }
        )
    ])

# Add this before your callbacks
topic_layout = html.Div([
    dbc.Container([
        dbc.Row([
            # Left sidebar with topics
            dbc.Col([
                # Home button and subject title in a row
                dbc.Row([
                    dbc.Col(
                        dcc.Link(
                            html.I(className="fas fa-home fa-2x"),
                            href="/",
                            style={
                                'color': 'white',
                                'textDecoration': 'none',
                                'marginRight': '15px'
                            }
                        ),
                        width="auto"
                    ),
                    dbc.Col(
                        html.H3(id="subject-title", 
                               className="mb-4",
                               style={
                                   'color': 'white',
                                   'fontFamily': "'Bebas Neue', sans-serif",
                                   'letterSpacing': '2px'
                               }),
                        width="auto"
                    )
                ], className="mb-4", align="center"),
                
                # Topics nav with updated styles
                dbc.Nav(
                    id="topics-nav",
                    vertical=True,
                    pills=True,
                    className="flex-column",
                    style={
                        'color': 'white'
                    }
                )
            ], width=3, className="topic-sidebar"),
            
            # Center content
            dbc.Col([
                html.Div(id="topic-content", className="topic-content")
            ], width=6),
            
            # Updated right chat section
            dbc.Col([
                html.Div([
                    html.H3("Chat with AI Tutor", 
                           style={
                               'color': 'white',
                               'fontFamily': "'Bebas Neue', sans-serif",
                               'letterSpacing': '2px',
                               'marginBottom': '20px'
                           }),
                    html.Div(
                        id="chat-messages",
                        className="chat-messages",
                        style={
                            'height': 'calc(100vh - 250px)',
                            'overflowY': 'auto',
                            'padding': '10px',
                            'backgroundColor': 'rgba(255, 255, 255, 0.1)',
                            'borderRadius': '10px',
                            'marginBottom': '20px'
                        }
                    ),
                    dbc.Input(
                        id="chat-input",
                        placeholder="Type your question...",
                        type="text",
                        style={
                            'marginBottom': '10px',
                            'backgroundColor': 'rgba(255, 255, 255, 0.9)'
                        }
                    ),
                    dbc.Button(
                        "Send",
                        id="send-button",
                        color="light",
                        className="w-100"
                    )
                ], className="chat-section")
            ], width=3)
        ])
    ], fluid=True)
])

# Add these callbacks for chat functionality
@app.callback(
    [Output('chat-messages', 'children'),
     Output('chat-input', 'value')],
    [Input('send-button', 'n_clicks')],
    [State('chat-input', 'value'), State('context', 'data')]
)
def update_chat(n_clicks, message, data):
    if n_clicks is None or not message:
        return [], ''
    
    print("Data in the store:", data)

    try:
        # Send message to API
        response = requests.post(f'{API_BASE_URL}/chat', 
                               json={'message': message, 'context': data})
        
        if response.status_code == 200:
            # Get updated chat history
            history_response = requests.get(f'{API_BASE_URL}/chat/history')
            if history_response.status_code == 200:
                chat_history = history_response.json()
                
                # Create message elements
                messages = []
                for chat in chat_history:
                    messages.extend([
                        html.Div(
                            chat['user'],
                            className='user-message',
                            style={
                                'textAlign': 'right',
                                'margin': '10px',
                                'padding': '10px',
                                'backgroundColor': '#be185d',
                                'color': 'white',
                                'borderRadius': '10px',
                                'maxWidth': '80%',
                                'marginLeft': 'auto'
                            }
                        ),
                        html.Div(
                            dcc.Markdown(chat['ai']),
                            className='ai-message',
                            style={
                                'textAlign': 'left',
                                'margin': '10px',
                                'padding': '10px',
                                'backgroundColor': '#4c1d95',
                                'color': 'white',
                                'borderRadius': '10px',
                                'maxWidth': '80%'
                            }
                        )
                    ])
                
                return messages, ''
    
    except requests.RequestException as e:
        print(f"Chat API Error: {e}")
    
    return [], message

# Add these styles to your app.index_string
'''
    <style>
        /* ... existing styles ... */
        .chat-messages::-webkit-scrollbar {
            width: 8px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5);
        }
        
        .user-message, .ai-message {
            word-wrap: break-word;
            margin-bottom: 10px;
        }
    </style>
'''

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
