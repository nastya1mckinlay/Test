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

def explode_tags(df, column):
    df = df.copy()
    df[column] = df[column].fillna('').apply(lambda x: [i.strip() for i in x.split(',')] if x else [])
    return df.explode(column)

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
        html.Button("Submit", id='submit-btn', n_clicks=0),
        html.Button("Export CSV", id='export-btn', n_clicks=0),
        dcc.Download(id="download-dataframe-csv")
    ], style={'width': '80%', 'margin': 'auto'}),

    html.H3("📈 Mood & Energy Trends"),
    dcc.Graph(id='trend-graph'),

    html.H3("🧠 Predictive Insight"),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px"}),

    html.H3("🍽️ Average Mood by Food Tag"),
    dcc.Graph(id='food-mood-graph'),

    html.H3("🏃 Average Energy by Activity Tag"),
    dcc.Graph(id='activity-energy-graph'),
])

@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Output('food-mood-graph', 'figure'),
    Output('activity-energy-graph', 'figure'),
    Input('submit-btn', 'n_clicks'),
    State('food-input', 'value'),
    State('activity-input', 'value'),
    State('mood-input', 'value'),
    State('energy-input', 'value')
)
def update(n, foods, acts, mood, energy):
    data = load_data()
    today = datetime.date.today()

    if n > 0:
        # Prevent duplicate entry for same date
        if today not in data['Date'].values:
            new_row = {
                "Date": today,
                "Foods": ', '.join(foods) if foods else '',
                "Activities": ', '.join(acts) if acts else '',
                "Mood": mood,
                "Energy": energy
            }
            data = data.append(new_row, ignore_index=True)
            data.to_csv(DATA_FILE, index=False)

    # Reload after possible append
    data = load_data()

    # Mood & Energy trends over time
    fig_trends = px.line(data, x='Date', y=['Mood', 'Energy'], title='Mood & Energy Over Time')

    # Insight logic
    insight = []
    if not data.empty:
        recent = data.tail(5)
        if recent['Mood'].mean() > 3.5:
            insight.append("😊 You're on a roll! Mood's been great lately.")
        if 'Sugary' in ','.join(recent['Foods']):
            insight.append("🍭 High sugar intake might be affecting energy consistency.")
        if 'Exercise' in ','.join(recent['Activities']):
            insight.append("💪 Days with exercise usually show higher energy.")
    if not insight:
        insight = ["📊 Not enough data yet to detect trends. Keep logging!"]

    # Explode Foods & Activities for group stats
    foods_exp = explode_tags(data, 'Foods')
    acts_exp = explode_tags(data, 'Activities')

    # Average Mood by Food
    food_stats = foods_exp.groupby('Foods')[['Mood', 'Energy']].mean().reset_index()
    fig_food_mood = px.bar(food_stats, x='Foods', y='Mood',
                           title='Average Mood by Food Tag',
                           labels={'Mood': 'Average Mood', 'Foods': 'Food Tag'})

    # Average Energy by Activity
    activity_stats = acts_exp.groupby('Activities')[['Mood', 'Energy']].mean().reset_index()
    fig_act_energy = px.bar(activity_stats, x='Activities', y='Energy',
                            title='Average Energy by Activity Tag',
                            labels={'Energy': 'Average Energy', 'Activities': 'Activity Tag'})

    return fig_trends, html.Ul([html.Li(i) for i in insight]), fig_food_mood, fig_act_energy

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("export-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_data(n_clicks):
    return dcc.send_file(DATA_FILE)

if __name__ == '__main__':
    app.run_server(debug=True)
