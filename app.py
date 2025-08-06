import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import datetime
import plotly.express as px
import os

app = dash.Dash(__name__)
server = app.server

DATA_FILE = "data.csv"
food_tags = ['Healthy', 'Sugary', 'Junk', 'Protein', 'Carbs']
activities = ['Exercise', 'Socializing', 'Gaming', 'Studying', 'Outdoors', 'None']

# Load data function
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    else:
        return pd.DataFrame(columns=['Date', 'Foods', 'Activities', 'Mood', 'Energy'])

# Layout
app.layout = html.Div([
    dcc.Store(id='memory-data', data=load_data().to_dict('records')),
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
        html.Button("Simulate Entry", id='simulate-btn', n_clicks=0),
    ], style={'width': '80%', 'margin': 'auto'}),

    html.H3("📈 Mood & Energy Trends"),
    dcc.Graph(id='trend-graph'),

    html.H3("🧐 Predictive Insight"),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px"})
])

# Callback to simulate entry and update in-memory data
@app.callback(
    Output('memory-data', 'data'),
    Input('simulate-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value'),
    State('memory-data', 'data')
)
def simulate_entry(n_clicks, foods, acts, mood, energy, data_records):
    if n_clicks > 0:
        data = pd.DataFrame(data_records)
        today = datetime.date.today()
        new_row = {
            "Date": today,
            "Foods": ', '.join(foods) if foods else '',
            "Activities": ', '.join(acts) if acts else '',
            "Mood": mood,
            "Energy": energy
        }
        new_entry_df = pd.DataFrame([new_row])
        data = pd.concat([data, new_entry_df], ignore_index=True)
        return data.to_dict('records')
    else:
        return data_records

# Callback to update graph and insights
@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Input('memory-data', 'data')
)
def update_graph_and_insights(data_records):
    data = pd.DataFrame(data_records)
    if not data.empty:
        data['Date'] = pd.to_datetime(data['Date']).dt.date
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
