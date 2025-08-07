import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import datetime
import plotly.express as px
import os
import numpy as np

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

# Generate demo data
def generate_demo_data():
    demo_data = []
    start_date = datetime.datetime.now() - datetime.timedelta(days=29)
    for i in range(30):
        date = (start_date + datetime.timedelta(days=i)).date()
        foods = list(np.random.choice(food_tags, size=np.random.randint(1, 3), replace=False))
        acts = list(np.random.choice(activities, size=np.random.randint(1, 3), replace=False))
        mood = np.random.randint(2, 6)
        energy = np.random.randint(2, 6)
        demo_data.append({
            "Date": date,
            "Foods": ', '.join(foods),
            "Activities": ', '.join(acts),
            "Mood": mood,
            "Energy": energy
        })
    return pd.DataFrame(demo_data)

# Layout
app.layout = html.Div([
    dcc.Store(id='memory-data', data=load_data().to_dict('records')),
    dcc.Store(id='mode', data='demo'),
    dcc.Store(id='submit-count', data=0),
    html.H1("\ud83c\udf31 MindFuel: Mood & Health Predictor", style={'textAlign': 'center'}),

    html.Div([
        html.Button("View Demo Data", id='demo-btn', n_clicks=0),
        html.Button("Track My Data", id='own-btn', n_clicks=0, style={'marginLeft': '10px'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

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
        html.Button("Submit Entry", id='submit-btn', n_clicks=0, disabled=True),
    ], style={'width': '80%', 'margin': 'auto'}),

    html.H3("\ud83d\udcc8 Mood & Energy Trends"),
    dcc.Graph(id='trend-graph'),

    html.H3("\ud83d\udc40 Predictive Insight"),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px"}),

    html.Div(id='reward-penalty-output', style={'marginTop': '20px', 'fontWeight': 'bold'})
])

# Mode selection callback
@app.callback(
    Output('mode', 'data'),
    Output('submit-btn', 'disabled'),
    Input('demo-btn', 'n_clicks'),
    Input('own-btn', 'n_clicks'),
    prevent_initial_call=True
)
def switch_mode(demo_clicks, own_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'demo-btn':
        return 'demo', True
    elif button_id == 'own-btn':
        return 'own', False
    raise dash.exceptions.PreventUpdate

# Submit Entry with Limit
@app.callback(
    Output('memory-data', 'data'),
    Output('submit-count', 'data'),
    Input('submit-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value'),
    State('memory-data', 'data'),
    State('submit-count', 'data'),
    prevent_initial_call=True
)
def submit_entry(n_clicks, foods, acts, mood, energy, data_records, submit_count):
    if n_clicks > 0 and submit_count < 5:
        data = pd.DataFrame(data_records)
        today = datetime.date.today()
        new_row = {
            "Date": today,
            "Foods": ', '.join(foods) if foods else '',
            "Activities": ', '.join(acts) if acts else '',
            "Mood": mood,
            "Energy": energy
        }
        data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
        data.to_csv(DATA_FILE, index=False)
        submit_count += 1
    return data.to_dict('records'), submit_count

# Update Graph, Insights, Rewards
@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Output('reward-penalty-output', 'children'),
    Input('memory-data', 'data'),
    Input('mode', 'data')
)
def update_graph_and_insights(data_records, mode):
    data = pd.DataFrame(data_records)
    if mode == 'demo':
        data = generate_demo_data()

    if not data.empty:
        data['Date'] = pd.to_datetime(data['Date']).dt.date
        fig = px.line(data, x='Date', y=['Mood', 'Energy'], title='Mood & Energy Over Time', range_y=[1, 5] if mode=='demo' else None)

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

        # Rewards/Penalties every 5 entries
        reward_penalty = ""
        if len(data) % 5 == 0:
            score = 0
            score += all_foods.count('Healthy') * 2
            score -= all_foods.count('Junk') * 2
            score -= all_foods.count('Sugary')
            score += all_acts.count('Exercise') * 3
            reward_penalty = f"\ud83c\udf1f Reward Score: {score}" if score > 0 else f"\u26a0\ufe0f Penalty Score: {score}"
    else:
        fig = px.line(title="No data available")
        insight = ["\ud83d\udcca No data to display yet."]
        reward_penalty = ""

    return fig, html.Ul([html.Li(i) for i in insight]), reward_penalty

if __name__ == '__main__':
    app.run_server(debug=False)
