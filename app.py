import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import datetime
import plotly.express as px
import os
import time
import numpy as np
from dash.exceptions import PreventUpdate

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

# Load base data once at startup for reset
BASE_DATA = load_data()

app.layout = html.Div([
    dcc.Store(id='memory-data', data=BASE_DATA.to_dict('records')),
    dcc.Store(id='last-submit-time', data=None),

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

        html.Button("Submit Entry", id='submit-btn', n_clicks=0, style={'marginRight': '10px'}),
        html.Button("Demo Entry", id='demo-btn', n_clicks=0, style={'marginRight': '10px'}),
        html.Button("Reset Data", id='reset-btn', n_clicks=0, style={'marginRight': '10px'}),
        html.Button("Export CSV", id='export-btn', n_clicks=0),

        html.Div(id='submit-timer', style={'color': 'red', 'marginTop': '10px'})
    ], style={'width': '80%', 'margin': 'auto'}),

    html.H3("📈 Mood & Energy Trends"),
    dcc.Graph(id='trend-graph'),

    html.H3("🧐 Predictive Insight"),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px"})
])


@app.callback(
    Output('memory-data', 'data'),
    Output('last-submit-time', 'data'),
    Input('submit-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value'),
    State('memory-data', 'data'),
    State('last-submit-time', 'data'),
    prevent_initial_call=True
)
def submit_entry(n_clicks, foods, acts, mood, energy, data_records, last_submit):
    now = time.time()
    # Cooldown: 20 minutes = 1200 seconds
    if last_submit and (now - last_submit) < 1200:
        raise PreventUpdate

    if not foods or not acts:
        # Require at least some input to submit
        raise PreventUpdate

    data_df = pd.DataFrame(data_records)
    today = datetime.date.today()

    new_row = {
        "Date": today,
        "Foods": ', '.join(foods),
        "Activities": ', '.join(acts),
        "Mood": mood,
        "Energy": energy
    }

    # Append new row to data
    data_df = pd.concat([data_df, pd.DataFrame([new_row])], ignore_index=True)

    # Save updated data to CSV
    data_df.to_csv(DATA_FILE, index=False)

    return data_df.to_dict('records'), now


@app.callback(
    Output('memory-data', 'data'),
    Input('demo-btn', 'n_clicks'),
    prevent_initial_call=True
)
def demo_entry(n_clicks):
    # Generate random demo entry values
    demo_foods = list(np.random.choice(food_tags, size=np.random.randint(1, 3), replace=False))
    demo_acts = list(np.random.choice(activities, size=np.random.randint(1, 3), replace=False))
    demo_mood = np.random.randint(2, 6)
    demo_energy = np.random.randint(2, 6)

    data_df = pd.DataFrame(load_data().to_dict('records'))  # start fresh from disk

    new_row = {
        "Date": datetime.date.today(),
        "Foods": ', '.join(demo_foods),
        "Activities": ', '.join(demo_acts),
        "Mood": demo_mood,
        "Energy": demo_energy
    }

    data_df = pd.concat([data_df, pd.DataFrame([new_row])], ignore_index=True)
    data_df.to_csv(DATA_FILE, index=False)

    return data_df.to_dict('records')


@app.callback(
    Output('memory-data', 'data'),
    Input('reset-btn', 'n_clicks'),
    prevent_initial_call=True
)
def reset_data(n_clicks):
    BASE_DATA.to_csv(DATA_FILE, index=False)
    return BASE_DATA.to_dict('records')


@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Input('memory-data', 'data')
)
def update_graph_insights(data_records):
    data_df = pd.DataFrame(data_records)
    if not data_df.empty:
        data_df['Date'] = pd.to_datetime(data_df['Date']).dt.date

        fig = px.line(data_df, x='Date', y=['Mood', 'Energy'], title='Mood & Energy Over Time')

        recent = data_df.tail(5)
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


@app.callback(
    Output('submit-timer', 'children'),
    Input('submit-btn', 'n_clicks'),
    State('last-submit-time', 'data'),
    prevent_initial_call=True
)
def update_submit_timer(n_clicks, last_submit):
    if not last_submit:
        return ""

    remaining = 1200 - (time.time() - last_submit)
    if remaining <= 0:
        return "✅ You can submit now."
    else:
        minutes, seconds = divmod(int(remaining), 60)
        return f"⏳ Next submission allowed in {minutes:02}:{seconds:02} min"


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("export-btn", "n_clicks"),
    State('memory-data', 'data'),
    prevent_initial_call=True
)
def export_csv(n_clicks, data_records):
    df = pd.DataFrame(data_records)
    return dcc.send_data_frame(df.to_csv, "mindfuel_data.csv", index=False)


if __name__ == '__main__':
    app.run_server(debug=True)
