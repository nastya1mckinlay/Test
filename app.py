import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import datetime
import plotly.express as px
import numpy as np
import os

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

app.layout = html.Div([
    dcc.Store(id='memory-data', data=load_data().to_dict('records')),
    html.H1("\ud83c\udf31 MindFuel: Mood & Health Predictor", style={'textAlign': 'center'}),
    html.Div([
        html.H3("\ud83d\udccb Log Your Day"),
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
        html.Button("Reset to Demo", id='reset-btn', n_clicks=0, style={'marginLeft': '10px'})
    ], style={'width': '80%', 'margin': 'auto'}),

    html.H3("\ud83d\udcc8 Mood & Energy Trends"),
    dcc.Graph(id='trend-graph'),

    html.H3("\ud83e\uddd0 Predictive Insight"),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px"})
])

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

@app.callback(
    Output('memory-data', 'data'),
    Input('submit-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value'),
    State('memory-data', 'data'),
    prevent_initial_call=True
)
def submit_entry(n_clicks, foods, acts, mood, energy, data_records):
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
    return data.to_dict('records')

@app.callback(
    Output('memory-data', 'data'),
    Input('reset-btn', 'n_clicks'),
    prevent_initial_call=True
)
def reset_to_demo(n_clicks):
    demo_data = []
    now = datetime.datetime.now()
    for i in range(5):
        demo_data.append({
            "Date": now - datetime.timedelta(hours=i),
            "Foods": 'Healthy, Protein',
            "Activities": 'Exercise',
            "Mood": np.random.randint(3,6),
            "Energy": np.random.randint(3,6)
        })
    df = pd.DataFrame(demo_data)
    df.to_csv(DATA_FILE, index=False)
    return df.to_dict('records')

@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Input('memory-data', 'data')
)
def update_graph_and_insights(data_records):
    data = pd.DataFrame(data_records)
    if not data.empty:
        data['Date'] = pd.to_datetime(data['Date'])
        fig = px.line(data, x='Date', y=['Mood', 'Energy'], title='Mood & Energy Over Time')

        recent = data.tail(5)
        all_foods = ','.join(recent['Foods'].dropna())
        all_acts = ','.join(recent['Activities'].dropna())

        insight = []
        if recent['Mood'].mean() > 3.5:
            insight.append("\ud83d\ude0a You're on a roll! Mood's been great lately.")
        if 'Sugary' in all_foods:
            insight.append("\ud83c\udf6d High sugar intake might be affecting energy consistency.")
        if 'Exercise' in all_acts:
            insight.append("\ud83d\udcaa Days with exercise usually show higher energy.")
        if not insight:
            insight = ["\ud83d\udcca Not enough data yet to detect trends. Keep logging!"]

    else:
        fig = px.line(title="No data available")
        insight = ["\ud83d\udcca No data to display yet."]

    return fig, html.Ul([html.Li(i) for i in insight])

if __name__ == '__main__':
    app.run_server(debug=True)
