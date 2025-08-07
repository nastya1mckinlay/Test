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

# Initial states
submission_times = []
user_score = {'score': 0, 'counter': 0}
demo_cases = {
    "Healthy & Exercise": [
        {"Foods": "Healthy", "Activities": "Exercise", "Mood": 5, "Energy": 5},
        {"Foods": "Protein", "Activities": "Exercise", "Mood": 5, "Energy": 4},
        {"Foods": "Healthy", "Activities": "Outdoors", "Mood": 4, "Energy": 4},
        {"Foods": "Healthy", "Activities": "Studying", "Mood": 4, "Energy": 3},
    ],
    "Junk & Gaming": [
        {"Foods": "Junk", "Activities": "Gaming", "Mood": 2, "Energy": 2},
        {"Foods": "Sugary", "Activities": "Gaming", "Mood": 1, "Energy": 2},
        {"Foods": "Junk", "Activities": "None", "Mood": 2, "Energy": 1},
    ],
    "Sugar & Party": [
        {"Foods": "Sugary", "Activities": "Socializing", "Mood": 3, "Energy": 2},
        {"Foods": "Carbs", "Activities": "Party", "Mood": 3, "Energy": 3},
        {"Foods": "Sugary", "Activities": "Outdoors", "Mood": 2, "Energy": 2},
    ]
}
all_demo_rows = []
date_base = datetime.date.today()
for i, (label, group) in enumerate(demo_cases.items()):
    for j, entry in enumerate(group):
        entry = entry.copy()
        entry["Date"] = date_base - datetime.timedelta(days=len(all_demo_rows))
        all_demo_rows.append(entry)
demo_data = pd.DataFrame(all_demo_rows)
user_data = pd.DataFrame(columns=['Date', 'Foods', 'Activities', 'Mood', 'Energy'])

# Layout
app.layout = html.Div([
    dcc.Store(id='demo-data', data=demo_data.to_dict('records')),
    dcc.Store(id='user-data', data=user_data.to_dict('records')),
    dcc.Store(id='active-mode', data='demo'),

    html.Div([
        html.H1("\ud83c\udf31 MindFuel", style={'textAlign': 'left'}),
        html.Div(id='score-display', style={'fontSize': '18px', 'marginTop': '4px'})
    ], style={'marginBottom': '10px'}),

    html.Div([
        html.Button("\ud83c\udf10 Demo Mode", id='demo-btn', n_clicks=0, style={'marginRight': '10px'}),
        html.Button("\ud83d\udcca Track My Data", id='track-btn', n_clicks=0, style={'marginRight': '10px'}),
        html.Button("\u2705 Submit Entry", id='submit-btn', n_clicks=0, disabled=True)
    ], style={'marginBottom': '10px'}),

    html.Div([
        html.Label("Select a Demo Case:"),
        dcc.Dropdown(list(demo_cases.keys()), id='demo-select', value=list(demo_cases.keys())[0], style={'marginBottom': '10px'})
    ]),

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

    dcc.Graph(id='trend-graph', style={'height': '300px'}),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px", 'fontSize': '14px'})
])

# Toggle mode
@app.callback(
    Output('submit-btn', 'disabled'),
    Output('active-mode', 'data'),
    Input('demo-btn', 'n_clicks'),
    Input('track-btn', 'n_clicks')
)
def toggle_mode(demo_clicks, track_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return True, 'demo'
    triggered = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered == 'track-btn':
        return False, 'user'
    else:
        return True, 'demo'

# Submit entry
@app.callback(
    Output('user-data', 'data'),
    Input('submit-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value'),
    State('user-data', 'data'),
    State('active-mode', 'data')
)
def handle_entry(submit_clicks, foods, acts, mood, energy, user_records, mode):
    if mode != 'user' or submit_clicks == 0:
        return user_records

    now = time.time()
    submission_times[:] = [t for t in submission_times if now - t < 3600]
    if len(submission_times) >= 5:
        return user_records
    submission_times.append(now)

    today = datetime.date.today()
    new_row = {
        "Date": today,
        "Foods": ', '.join(foods) if foods else '',
        "Activities": ', '.join(acts) if acts else '',
        "Mood": mood,
        "Energy": energy
    }
    data = pd.DataFrame(user_records)
    new_entry_df = pd.DataFrame([new_row])
    data = pd.concat([data, new_entry_df], ignore_index=True).tail(50)

    if 'Healthy' in new_row['Foods'] or 'Exercise' in new_row['Activities']:
        user_score['score'] += 2
    if 'Sugary' in new_row['Foods'] or 'Junk' in new_row['Foods']:
        user_score['score'] -= 1
    user_score['counter'] += 1

    return data.to_dict('records')

# Update graph/insight/score
@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Output('score-display', 'children'),
    Input('demo-data', 'data'),
    Input('user-data', 'data'),
    Input('active-mode', 'data'),
    Input('demo-select', 'value')
)
def update_graphs(demo_records, user_records, mode, demo_case):
    score_text = f"\u2b50 Score: {user_score['score']}" if mode == 'user' else ""
    if mode == 'demo':
        filtered = [r for r in demo_records if r['Foods'] in [d['Foods'] for d in demo_cases[demo_case]]]
        data = pd.DataFrame(filtered)
    else:
        data = pd.DataFrame(user_records)

    if not data.empty:
        data['Date'] = pd.to_datetime(data['Date']).dt.date
        if mode == 'user':
            data = data.tail(50)
            data['group'] = (data.index // 5) * 5
            grouped = data.groupby('group').mean(numeric_only=True).reset_index()
            fig = px.line(grouped, x='group', y=['Mood', 'Energy'], markers=True)
        else:
            fig = px.line(data, x='Date', y=['Mood', 'Energy'], markers=True)

        recent = data.tail(5)
        all_foods = ','.join(recent['Foods'].dropna())
        all_acts = ','.join(recent['Activities'].dropna())

        insight = []
        if recent['Mood'].mean() > 3.5:
            insight.append("\ud83d\ude0a Great mood lately!")
        if 'Sugary' in all_foods:
            insight.append("\ud83c\udf6d Watch sugar intake.")
        if 'Exercise' in all_acts:
            insight.append("\ud83d\udcaa Exercise helps energy!")
        if 'Junk' in all_foods and recent['Mood'].mean() < 3:
            insight.append("\ud83c\udf54 Junk food may be lowering mood.")
        if not insight:
            insight = ["\ud83d\udcca Keep logging to see insights."]
    else:
        fig = px.line(title="No data yet")
        insight = ["\ud83d\udcca No data to show."]

    return fig, html.Ul([html.Li(i) for i in insight]), score_text

if __name__ == '__main__':
    app.run_server(debug=True)
