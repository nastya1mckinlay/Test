import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import datetime
import plotly.express as px
import numpy as np
import os
import time
from dash.exceptions import PreventUpdate

app = dash.Dash(__name__)
server = app.server

DATA_FILE = "data.csv"
food_tags = ['Healthy', 'Sugary', 'Junk', 'Protein', 'Carbs']
activities = ['Exercise', 'Socializing', 'Gaming', 'Studying', 'Outdoors', 'None']

# Initialize empty dataframe
if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE)
    data['Date'] = pd.to_datetime(data['Date']).dt.date
else:
    data = pd.DataFrame(columns=['Date', 'Foods', 'Activities', 'Mood', 'Energy'])

BASE_DATA = data.copy()

def generate_demo_data(days=30, case='balanced'):
    demo_data = []
    start_date = datetime.datetime.now() - datetime.timedelta(days=days-1)

    for i in range(days):
        date = (start_date + datetime.timedelta(days=i)).date()
        foods = list(np.random.choice(food_tags, np.random.randint(1, 3), replace=False))
        acts = list(np.random.choice(activities, np.random.randint(1, 3), replace=False))

        if case == 'high-energy':
            mood = np.random.randint(4, 6)
            energy = np.random.randint(4, 6)
        elif case == 'low-energy':
            mood = np.random.randint(2, 4)
            energy = np.random.randint(1, 3)
        elif case == 'sugar-crash':
            mood = 5 if 'Sugary' in foods else np.random.randint(2, 5)
            energy = 2 if 'Sugary' in foods else np.random.randint(3, 6)
        else:
            mood = np.random.randint(3, 6)
            energy = np.random.randint(3, 6)

        demo_data.append({
            "Date": date,
            "Foods": ', '.join(foods),
            "Activities": ', '.join(acts),
            "Mood": mood,
            "Energy": energy
        })

    return pd.DataFrame(demo_data)

app.layout = html.Div([
    html.H1("\ud83c\udf31 MindFuel: Mood & Health Predictor", style={'textAlign': 'center'}),

    dcc.Store(id='last-submit-time', data=None),
    dcc.Store(id='data-store', data=data.to_dict('records')),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),

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

        html.Button("Submit", id='submit-btn', n_clicks=0),
        html.Button("Demo Entry", id='demo-btn', n_clicks=0, style={'marginLeft': '10px'}),
        html.Button("Export CSV", id='export-btn', n_clicks=0, style={'marginLeft': '10px'}),
        html.Button("Reset to Original Data", id='reset-btn', n_clicks=0, style={'marginLeft': '10px'}),
        dcc.Download(id="download-dataframe-csv"),

        html.Div(id='submit-timer', style={'color': 'red', 'marginTop': '10px'}),

        html.Hr(),
        html.Label("\ud83d\udd04 Switch Demo Case:"),
        dcc.Dropdown(
            options=[
                {'label': 'Balanced', 'value': 'balanced'},
                {'label': 'High Energy', 'value': 'high-energy'},
                {'label': 'Low Energy', 'value': 'low-energy'},
                {'label': 'Sugar Crash', 'value': 'sugar-crash'}
            ],
            value='balanced',
            id='demo-case-selector'
        )
    ], style={'width': '80%', 'margin': 'auto'}),

    html.H3("\ud83d\udcc8 Mood & Energy Trends"),
    dcc.Graph(id='trend-graph'),

    html.H3("\ud83e\udde0 Predictive Insight"),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px"})
])

@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Output('last-submit-time', 'data'),
    Output('data-store', 'data'),
    Input('submit-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value'),
    State('last-submit-time', 'data'),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def update(n, foods, acts, mood, energy, last_submit, data_records):
    now = time.time()

    if last_submit and (now - last_submit < 1200):
        raise PreventUpdate

    data_df = pd.DataFrame(data_records)
    today = datetime.date.today()

    new_row = {
        "Date": today,
        "Foods": ', '.join(foods) if foods else '',
        "Activities": ', '.join(acts) if acts else '',
        "Mood": mood,
        "Energy": energy
    }
    data_df = pd.concat([data_df, pd.DataFrame([new_row])], ignore_index=True)
    data_df.to_csv(DATA_FILE, index=False)

    fig = px.line(data_df, x='Date', y=['Mood', 'Energy'], title='Mood & Energy Over Time',
                  color_discrete_map={'Mood': 'blue', 'Energy': 'green'})

    insight = []
    if not data_df.empty:
        recent = data_df.tail(5)
        if recent['Mood'].mean() > 3.5:
            insight.append("\ud83d\ude0a You're on a roll! Mood's been great lately.")
        if 'Sugary' in ','.join(recent['Foods']):
            insight.append("\ud83c\udf6d High sugar intake might be affecting energy consistency.")
        if 'Exercise' in ','.join(recent['Activities']):
            insight.append("\ud83d\udcaa Days with exercise usually show higher energy.")
    if not insight:
        insight = ["\ud83d\udcca Not enough data yet to detect trends. Keep logging!"]

    return fig, html.Ul([html.Li(i) for i in insight]), now, data_df.to_dict('records')

@app.callback(
    Output('submit-timer', 'children'),
    Input('interval-component', 'n_intervals'),
    State('last-submit-time', 'data')
)
def update_timer(n_intervals, last_submit):
    if not last_submit:
        return ""

    remaining = 1200 - (time.time() - last_submit)
    if remaining <= 0:
        return "\u2705 You can submit now."
    else:
        minutes, seconds = divmod(int(remaining), 60)
        return f"\u23f3 Next submission allowed in {minutes:02}:{seconds:02} min"

@app.callback(
    Output('food-input', 'value'),
    Output('activity-input', 'value'),
    Output('mood-input', 'value'),
    Output('energy-input', 'value'),
    Input('demo-btn', 'n_clicks'),
    prevent_initial_call=True
)
def demo_fill(n_clicks):
    return (
        list(np.random.choice(food_tags, size=np.random.randint(1, 3), replace=False)),
        list(np.random.choice(activities, size=np.random.randint(1, 3), replace=False)),
        np.random.randint(2, 5),
        np.random.randint(2, 5)
    )

@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Output('data-store', 'data'),
    Input('demo-case-selector', 'value')
)
def switch_demo_case(case):
    data_df = generate_demo_data(days=30, case=case)
    data_df.to_csv(DATA_FILE, index=False)

    color_map = {
        'balanced': {'Mood': 'blue', 'Energy': 'green'},
        'high-energy': {'Mood': 'purple', 'Energy': 'orange'},
        'low-energy': {'Mood': 'grey', 'Energy': 'brown'},
        'sugar-crash': {'Mood': 'red', 'Energy': 'yellow'}
    }

    fig = px.line(data_df, x='Date', y=['Mood', 'Energy'], title='Mood & Energy Over Time',
                  color_discrete_map=color_map.get(case, {'Mood': 'blue', 'Energy': 'green'}))

    insight = []
    if not data_df.empty:
        recent = data_df.tail(5)
        if recent['Mood'].mean() > 3.5:
            insight.append("\ud83d\ude0a You're on a roll! Mood's been great lately.")
        if 'Sugary' in ','.join(recent['Foods']):
            insight.append("\ud83c\udf6d High sugar intake might be affecting energy consistency.")
        if 'Exercise' in ','.join(recent['Activities']):
            insight.append("\ud83d\udcaa Days with exercise usually show higher energy.")
    if not insight:
        insight = ["\ud83d\udcca Not enough data yet to detect trends. Keep logging!"]

    return fig, html.Ul([html.Li(i) for i in insight]), data_df.to_dict('records')

@app.callback(
    Output('data-store', 'data'),
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Input('reset-btn', 'n_clicks'),
    prevent_initial_call=True
)
def reset_data(n_clicks):
    data_df = BASE_DATA.copy()
    data_df.to_csv(DATA_FILE, index=False)

    fig = px.line(data_df, x='Date', y=['Mood', 'Energy'], title='Mood & Energy Over Time',
                  color_discrete_map={'Mood': 'blue', 'Energy': 'green'})

    insight = []
    if not data_df.empty:
        recent = data_df.tail(5)
        if recent['Mood'].mean() > 3.5:
            insight.append("\ud83d\ude0a You're on a roll! Mood's been great lately.")
        if 'Sugary' in ','.join(recent['Foods']):
            insight.append("\ud83c\udf6d High sugar intake might be affecting energy consistency.")
        if 'Exercise' in ','.join(recent['Activities']):
            insight.append("\ud83d\udcaa Days with exercise usually show higher energy.")
    if not insight:
        insight = ["\ud83d\udcca Not enough data yet to detect trends. Keep logging!"]

    return data_df.to_dict('records'), fig, html.Ul([html.Li(i) for i in insight])

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("export-btn", "n_clicks"),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def export_data(n_clicks, data_records):
    df = pd.DataFrame(data_records)
    temp_file = "temp_export.csv"
    df.to_csv(temp_file, index=False)
    return dcc.send_file(temp_file)

if __name__ == '__main__':
    app.run_server(debug=True)
