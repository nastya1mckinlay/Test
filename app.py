import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import datetime
import plotly.express as px
import numpy as np
import os
import time

app = dash.Dash(__name__)
server = app.server

DATA_FILE = "data.csv"
food_tags = ['Healthy', 'Sugary', 'Junk', 'Protein', 'Carbs']
activities = ['Exercise', 'Socializing', 'Gaming', 'Studying', 'Outdoors', 'None']

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        return pd.DataFrame(columns=['Date', 'Foods', 'Activities', 'Mood', 'Energy'])

# Store the timestamp of the last submit
last_submit_time = 0

app.layout = html.Div([
    dcc.Store(id='memory-data', data=load_data().to_dict('records')),
    dcc.Store(id='last-submit', data=0),  # Store last submit timestamp in client memory
    html.H1("🌱 MindFuel: Mood & Health Predictor", style={'textAlign': 'center'}),
    html.Div([
        html.H3("📋 Log Your Day"),
        html.Label("Food Tags:"),
        dcc.Dropdown(food_tags, multi=True, id='food-input'),
        html.Label("Activities:"),
        dcc.Dropdown(activities, multi=True, id='activity-input'),
        html.Label("Mood (1-5):"),
        dcc.Slider(1, 5, 1, value=3, id='mood-input'),
        html.Label("Energy (1-5):"),
        dcc.Slider(1, 5, 1, value=3, id='energy-input'),
        html.Button("Submit Entry", id='submit-btn', n_clicks=0),
        html.Button("Simulate Entry", id='simulate-btn', n_clicks=0, style={'marginLeft': '10px'}),
        html.Div(id='submit-message', style={'color': 'red', 'marginTop': '10px'})
    ], style={'width': '80%', 'margin': 'auto'}),

    html.H3("📈 Mood & Energy Trends"),
    dcc.Graph(id='trend-graph'),

    html.H3("🧐 Predictive Insight"),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px"})
])

# Submit Entry callback with 1-minute cooldown
@app.callback(
    Output('memory-data', 'data'),
    Output('submit-message', 'children'),
    Output('last-submit', 'data'),
    Input('submit-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value'),
    State('memory-data', 'data'),
    State('last-submit', 'data'),
    prevent_initial_call=True
)
def submit_entry(n_clicks, foods, acts, mood, energy, data_records, last_submit_timestamp):
    now_ts = time.time()
    # Check cooldown: only allow if >60 seconds since last submit
    if now_ts - last_submit_timestamp < 60:
        return data_records, "⏳ Please wait before submitting again (1 min cooldown).", last_submit_timestamp

    data = pd.DataFrame(data_records)
    now = datetime.datetime.now()

    new_row = {
        "Date": now,
        "Foods": ', '.join(foods) if foods else '',
        "Activities": ', '.join(acts) if acts else '',
        "Mood": mood,
        "Energy": energy
    }
    data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
    data.to_csv(DATA_FILE, index=False)
    return data.to_dict('records'), "", now_ts

# Simulate Entry callback (demo)
@app.callback(
    Output('memory-data', 'data'),
    Input('simulate-btn', 'n_clicks'),
    State('memory-data', 'data'),
    prevent_initial_call=True
)
def simulate_entry(n_clicks, data_records):
    data = pd.DataFrame(data_records)
    now = datetime.datetime.now()

    demo_foods = list(np.random.choice(food_tags, size=np.random.randint(1, 3), replace=False))
    demo_acts = list(np.random.choice(activities, size=np.random.randint(1, 3), replace=False))
    demo_mood = np.random.randint(2, 6)
    demo_energy = np.random.randint(2, 6)

    new_row = {
        "Date": now,
        "Foods": ', '.join(demo_foods),
        "Activities": ', '.join(demo_acts),
        "Mood": demo_mood,
        "Energy": demo_energy
    }
    data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
    data.to_csv(DATA_FILE, index=False)
    return data.to_dict('records')

# Update graph and insights
@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Input('memory-data', 'data')
)
def update_graph_and_insights(data_records):
    data = pd.DataFrame(data_records)
    if not data.empty:
        fig = px.line(data, x='Date', y=['Mood', 'Energy'], title='Mood & Energy Over Time')

        recent = data.tail(5)
        all_foods = ','.join(recent['Foods'].dropna())
        all_acts = ','.join(recent['Activities'].dropna())

        insight = []
        if recent['Mood'].mean() > 3.5:
            insight.append("😊 You're on a roll! Mood's been great lately.")
        if 'Sugary' in all_foods:
            insight.append("🍭 High sugar intake might be affecting energy consistency.")
        if 'Exercise' in all_acts:
            insight.append("💪 Days with exercise usually show higher energy.")
        if not insight:
            insight = ["📊 Not enough data yet to detect trends. Keep logging!"]

    else:
        fig = px.line(title="No data available")
        insight = ["📊 No data to display yet."]

    return fig, html.Ul([html.Li(i) for i in insight])

if __name__ == '__main__':
    app.run_server(debug=True)
