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

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    else:
        return pd.DataFrame(columns=['Date', 'Foods', 'Activities', 'Mood', 'Energy'])

app.layout = html.Div([
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

    html.H3("🧠 Predictive Insight"),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px"})
])

@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Input('simulate-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value')
)
def update(n, foods, acts, mood, energy):
    data = load_data()

    # Simulate entry (in-memory only)
    if n > 0:
        today = datetime.date.today()
        new_row = {
            "Date": today,
            "Foods": ', '.join(foods) if foods else '',
            "Activities": ', '.join(acts) if acts else '',
            "Mood": mood,
            "Energy": energy
        }
        data = data.append(new_row, ignore_index=True)

    # Mood & Energy Trends
    if data.empty:
        fig = px.line(title="No data available")
    else:
        fig = px.line(data, x='Date', y=['Mood', 'Energy'], title='Mood & Energy Over Time')

    # Insights
    insight = []
    if not data.empty:
        recent = data.tail(5)
        all_foods = ','.join(recent['Foods'].dropna())
        all_acts = ','.join(recent['Activities'].dropna())

        if recent['Mood'].mean() > 3.5:
            insight.append("😊 You're on a roll! Mood's been great lately.")
        if 'Sugary' in all_foods:
            insight.append("🍭 High sugar intake might be affecting energy consistency.")
        if 'Exercise' in all_acts:
            insight.append("💪 Days with exercise usually show higher energy.")

    if not insight:
        insight = ["📊 Not enough data yet to detect trends. Keep logging!"]

    return fig, html.Ul([html.Li(i) for i in insight])

if __name__ == '__main__':
    app.run_server(debug=True)
