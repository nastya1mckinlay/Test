import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import datetime
import plotly.express as px
import os
import time

app = dash.Dash(__name__)
server = app.server

DATA_FILE = "data.csv"
food_tags = ['Healthy', 'Sugary', 'Junk', 'Protein', 'Carbs']
activities = ['Exercise', 'Socializing', 'Gaming', 'Studying', 'Outdoors', 'None']

# Load data
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    else:
        return pd.DataFrame(columns=['Date', 'Foods', 'Activities', 'Mood', 'Energy'])

# Submission tracker
submission_times = []
user_mode = {'demo': True}  # True means demo mode is active
user_score = {'score': 0, 'counter': 0}
demo_data = load_data()
user_data = pd.DataFrame(columns=['Date', 'Foods', 'Activities', 'Mood', 'Energy'])

# Layout
app.layout = html.Div([
    dcc.Store(id='memory-data', data=demo_data.to_dict('records')),
    html.Div([
        html.Div([
            html.H1("🌱 MindFuel", style={'textAlign': 'left', 'display': 'inline-block'}),
            html.Div(id='score-display', style={'fontSize': '18px', 'marginTop': '10px'})
        ], style={'width': '100%', 'display': 'flex', 'justifyContent': 'space-between'})
    ]),

    html.Div([
        html.Button("🌐 Demo Mode", id='demo-btn', n_clicks=0, style={'marginRight': '10px'}),
        html.Button("📊 Track My Data", id='track-btn', n_clicks=0, style={'marginRight': '10px'}),
        html.Button("✅ Submit Entry", id='submit-btn', n_clicks=0, disabled=True)
    ], style={'marginBottom': '10px'}),

    html.Div([
        html.Label("Food Tags:"),
        dcc.Dropdown(food_tags, multi=True, id='food-input', style={'marginBottom': '5px'}),
        html.Label("Activities:"),
        dcc.Dropdown(activities, multi=True, id='activity-input', style={'marginBottom': '5px'}),
        html.Label("Mood (1-5):"),
        dcc.Slider(1, 5, 1, value=3, id='mood-input', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
        html.Label("Energy (1-5):"),
        dcc.Slider(1, 5, 1, value=3, id='energy-input', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
    ], style={'width': '100%', 'maxWidth': '500px'}),

    dcc.Graph(id='trend-graph', style={'height': '250px'}),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px", 'fontSize': '14px'})
])

# Mode toggle
@app.callback(
    Output('submit-btn', 'disabled'),
    Output('memory-data', 'data'),
    Input('demo-btn', 'n_clicks'),
    Input('track-btn', 'n_clicks')
)
def toggle_mode(demo_clicks, track_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return True, demo_data.to_dict('records')
    triggered = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered == 'track-btn':
        user_mode['demo'] = False
        return False, user_data.to_dict('records')
    else:
        user_mode['demo'] = True
        return True, demo_data.to_dict('records')

# Handle submit entry
@app.callback(
    Output('memory-data', 'data'),
    Input('submit-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value'),
    State('memory-data', 'data')
)
def handle_entry(submit_clicks, foods, acts, mood, energy, data_records):
    if submit_clicks == 0:
        return data_records

    now = time.time()
    submission_times[:] = [t for t in submission_times if now - t < 3600]
    if len(submission_times) >= 5:
        return data_records  # limit reached
    submission_times.append(now)

    today = datetime.date.today()
    new_row = {
        "Date": today,
        "Foods": ', '.join(foods) if foods else '',
        "Activities": ', '.join(acts) if acts else '',
        "Mood": mood,
        "Energy": energy
    }
    data = pd.DataFrame(data_records)
    new_entry_df = pd.DataFrame([new_row])
    data = pd.concat([data, new_entry_df], ignore_index=True)

    user_data[:] = data

    if 'Healthy' in new_row['Foods'] or 'Exercise' in new_row['Activities']:
        user_score['score'] += 2
    if 'Sugary' in new_row['Foods'] or 'Junk' in new_row['Foods']:
        user_score['score'] -= 1
    user_score['counter'] += 1

    return data.to_dict('records')

# Update graph, insights, score
@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Output('score-display', 'children'),
    Input('memory-data', 'data')
)
def update_outputs(data_records):
    data = pd.DataFrame(data_records)
    score_text = f"⭐ Score: {user_score['score']}"

    if not data.empty:
        data['Date'] = pd.to_datetime(data['Date']).dt.date
        fig = px.line(data, x='Date', y=['Mood', 'Energy'], title='')

        recent = data.tail(5)
        all_foods = ','.join(recent['Foods'].dropna())
        all_acts = ','.join(recent['Activities'].dropna())

        insight = []
        if recent['Mood'].mean() > 3.5:
            insight.append("😊 Great mood lately!")
        if 'Sugary' in all_foods:
            insight.append("🍭 Watch sugar intake.")
        if 'Exercise' in all_acts:
            insight.append("💪 Exercise helps energy!")
        if not insight:
            insight = ["📊 Keep logging to see insights."]
    else:
        fig = px.line(title="No data yet")
        insight = ["📊 No data to show."]

    return fig, html.Ul([html.Li(i) for i in insight]), score_text

if __name__ == '__main__':
    app.run_server(debug=True)
