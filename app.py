import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import datetime
import plotly.express as px
import os
import time
import pickle
from sklearn.preprocessing import MultiLabelBinarizer

app = dash.Dash(__name__)
server = app.server

DATA_FILE = "data.csv"
food_tags = ['Healthy', 'Sugary', 'Junk', 'Protein', 'Carbs']
activities = ['Exercise', 'Socializing', 'Gaming', 'Studying', 'Outdoors', 'None']

# Load models and encoders
with open('mood_model.pkl', 'rb') as f:
    mood_model = pickle.load(f)
with open('energy_model.pkl', 'rb') as f:
    energy_model = pickle.load(f)
with open('mlb_food.pkl', 'rb') as f:
    mlb_food = pickle.load(f)
with open('mlb_act.pkl', 'rb') as f:
    mlb_act = pickle.load(f)

# Load data
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    else:
        return pd.DataFrame(columns=['Date', 'Foods', 'Activities', 'Mood', 'Energy'])

submission_times = []
user_score = {'score': 0, 'counter': 0}

demo_data = pd.DataFrame([
    {"Date": datetime.date.today() - datetime.timedelta(days=6), "Foods": "Healthy", "Activities": "Exercise", "Mood": 5, "Energy": 5},
    {"Date": datetime.date.today() - datetime.timedelta(days=5), "Foods": "Junk", "Activities": "Gaming", "Mood": 2, "Energy": 2},
    {"Date": datetime.date.today() - datetime.timedelta(days=4), "Foods": "Sugary", "Activities": "Party", "Mood": 3, "Energy": 2},
    {"Date": datetime.date.today() - datetime.timedelta(days=3), "Foods": "Healthy", "Activities": "Outdoors", "Mood": 4, "Energy": 4},
    {"Date": datetime.date.today() - datetime.timedelta(days=2), "Foods": "Protein", "Activities": "Studying", "Mood": 3, "Energy": 3},
    {"Date": datetime.date.today() - datetime.timedelta(days=1), "Foods": "Carbs", "Activities": "Socializing", "Mood": 4, "Energy": 3},
    {"Date": datetime.date.today(), "Foods": "Healthy, Protein", "Activities": "Exercise", "Mood": 5, "Energy": 5},
])
user_data = load_data()

# Helper for ML input
def prepare_features(food_list, act_list):
    food_vec = mlb_food.transform([food_list])[0] if food_list else [0]*len(mlb_food.classes_)
    act_vec = mlb_act.transform([act_list])[0] if act_list else [0]*len(mlb_act.classes_)
    return list(food_vec) + list(act_vec)

# Predict next 3 days Mood & Energy
def predict_next_days(data, n=3):
    preds = []
    if data.empty:
        return preds
    last_entry = data.iloc[-1]
    food_list = [f.strip() for f in last_entry['Foods'].split(',')] if last_entry['Foods'] else []
    act_list = [a.strip() for a in last_entry['Activities'].split(',')] if last_entry['Activities'] else []

    features = prepare_features(food_list, act_list)

    for day_offset in range(1, n+1):
        mood_pred = mood_model.predict([features])[0]
        energy_pred = energy_model.predict([features])[0]
        pred_date = last_entry['Date'] + datetime.timedelta(days=day_offset)
        preds.append({'Date': pred_date, 'Mood': mood_pred, 'Energy': energy_pred})
    return preds

# Layout
app.layout = html.Div([
    dcc.Store(id='demo-data', data=demo_data.to_dict('records')),
    dcc.Store(id='user-data', data=user_data.to_dict('records')),
    dcc.Store(id='active-mode', data='demo'),

    html.Div([
        html.H1("🌱 MindFuel", style={'display': 'inline-block', 'marginRight': '20px'}),
        html.Div(id='score-display', style={'fontSize': '18px', 'display': 'inline-block', 'verticalAlign': 'middle'})
    ], style={'marginBottom': '10px'}),

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

    dcc.Graph(id='trend-graph', style={'height': '300px'}),
    html.Div(id='insight-output', style={"padding": "10px", "border": "1px solid #ccc", "borderRadius": "10px", 'fontSize': '14px'})
])

# Toggle mode callback
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

# Submit entry callback
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

    # Update score
    if 'Healthy' in new_row['Foods'] or 'Exercise' in new_row['Activities']:
        user_score['score'] += 2
    if 'Sugary' in new_row['Foods'] or 'Junk' in new_row['Foods']:
        user_score['score'] -= 1
    user_score['counter'] += 1

    return data.to_dict('records')

# Update graph/insight/score with prediction
@app.callback(
    Output('trend-graph', 'figure'),
    Output('insight-output', 'children'),
    Output('score-display', 'children'),
    Input('demo-data', 'data'),
    Input('user-data', 'data'),
    Input('active-mode', 'data')
)
def update_graphs(demo_records, user_records, mode):
    data_records = demo_records if mode == 'demo' else user_records
    data = pd.DataFrame(data_records)
    score_text = f"⭐ Score: {user_score['score']}" if mode == 'user' else ""

    if not data.empty:
        data['Date'] = pd.to_datetime(data['Date']).dt.date

        if mode == 'user':
            data = data.tail(50)
            data['group'] = (data.index // 5) * 5
            grouped = data.groupby('group').mean(numeric_only=True).reset_index()

            fig = px.line(grouped, x='group', y=['Mood', 'Energy'], title='')

            # Predict next 3 days and plot dashed lines
            preds = predict_next_days(data, n=3)
            if preds:
                pred_df = pd.DataFrame(preds)
                pred_df['group'] = grouped['group'].max() + 5 + pred_df.index * 5
                fig.add_scatter(x=pred_df['group'], y=pred_df['Mood'],
                                mode='lines+markers', name='Predicted Mood',
                                line=dict(dash='dash', color='red'))
                fig.add_scatter(x=pred_df['group'], y=pred_df['Energy'],
                                mode='lines+markers', name='Predicted Energy',
                                line=dict(dash='dash', color='orange'))

            fig.update_layout(xaxis_title='Entry group (avg of 5)', yaxis_title='Value (1-5)')
        else:
            fig = px.line(data, x='Date', y=['Mood', 'Energy'], title='')
            fig.update_layout(xaxis_title='Date', yaxis_title='Value (1-5)')

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
        if 'Junk' in all_foods and recent['Mood'].mean() < 3:
            insight.append("🍔 Junk food may be lowering mood.")
        if not insight:
            insight = ["📊 Keep logging to see insights."]
    else:
        fig = px.line(title="No data yet")
        insight = ["📊 No data to show."]

    return fig, html.Ul([html.Li(i) for i in insight]), score_text

if __name__ == '__main__':
    app.run_server(debug=True)
