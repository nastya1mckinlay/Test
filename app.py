import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import datetime
import os
import base64
import io
from sklearn.linear_model import LinearRegression
import numpy as np

# Load dataset for demo scenarios
DATA_FILE = "mood_energy_dataset.csv"
if os.path.exists(DATA_FILE):
    mood_energy_df = pd.read_csv(DATA_FILE)
    mood_energy_df['datetime'] = pd.to_datetime(mood_energy_df['datetime'])
else:
    mood_energy_df = pd.DataFrame()  # fallback empty

scenario_options = [
    {
        'label': f"{row['food']} + {row['exercise_type']} ({row['exercise_duration']} mins)",
        'value': idx
    }
    for idx, row in mood_energy_df.iterrows()
]

horizons = [0, 2, 6, 12, 24, 48]  # hours

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Mood & Energy Trends Dashboard by Anastasia McKinlay"),

    html.Label("Select Scenario:"),
    dcc.Dropdown(
        id="scenario-dropdown",
        options=scenario_options,
        value=scenario_options[0]['value'] if scenario_options else None,
        clearable=False,
        style={"width": "60%"}
    ),

    dcc.Graph(id="trend-graph"),

    html.Div(id="insight-output", style={"marginTop": "20px", "fontSize": "18px"}),

    html.Hr(),
    html.H3("Upload Your Own Data & See Predictions"),

    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select a CSV file')]),
        style={
            'width': '50%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),

    html.Div(id="upload-insight-output", style={"marginTop": "10px", "fontSize": "16px", "color": "orange"}),

    dcc.Graph(id='user-prediction-graph', style={"marginTop": "40px"}),

    html.Hr(),
    html.H3("Enter Your Current Status for Personalized Prediction"),

    html.Div([
        html.Label("Food:"),
        dcc.Input(id='input-food', type='text', placeholder='e.g. Protein', style={'marginBottom': '10px', 'width': '40%'}),

        html.Br(),
        html.Label("Exercise Type:"),
        dcc.Input(id='input-exercise-type', type='text', placeholder='e.g. Running', style={'marginBottom': '10px', 'width': '40%'}),

        html.Br(),
        html.Label("Exercise Duration (minutes):"),
        dcc.Input(id='input-exercise-duration', type='number', min=0, max=180, value=30, style={'marginBottom': '10px', 'width': '40%'}),

        html.Br(),
        html.Label("Current Mood (1-10):"),
        dcc.Input(id='input-mood-now', type='number', min=1, max=10, value=5, style={'marginBottom': '10px', 'width': '40%'}),

        html.Br(),
        html.Label("Current Energy (1-10):"),
        dcc.Input(id='input-energy-now', type='number', min=1, max=10, value=5, style={'marginBottom': '10px', 'width': '40%'}),

        html.Br(),
        html.Button('Predict Mood & Energy Trends', id='predict-button', n_clicks=0)
    ], style={'marginTop': '20px'}),

    dcc.Graph(id='personalized-prediction-graph', style={'marginTop': '40px'}),
    html.Div(id='personalized-prediction-insight', style={"marginTop": "20px", "fontSize": "16px", "color": "green"})
])

# Scenario trend graph update
@app.callback(
    Output("trend-graph", "figure"),
    Output("insight-output", "children"),
    Input("scenario-dropdown", "value"),
)
def update_trends(selected_idx):
    if selected_idx is None or mood_energy_df.empty:
        return go.Figure(), "No data available."

    row = mood_energy_df.iloc[selected_idx]

    mood_vals = [row['mood_now']] + [row[f"mood_{h}h"] for h in horizons if h != 0]
    energy_vals = [row['energy_now']] + [row[f"energy_{h}h"] for h in horizons if h != 0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=horizons, y=mood_vals, mode='lines+markers', name="Mood",
                             line=dict(color="cyan", width=3), marker=dict(symbol='circle', size=10)))
    fig.add_trace(go.Scatter(x=horizons, y=energy_vals, mode='lines+markers', name="Energy",
                             line=dict(color="magenta", width=3), marker=dict(symbol='square', size=10)))

    fig.update_layout(
        title=f"Mood & Energy Trends for: {row['food']} + {row['exercise_type']} ({row['exercise_duration']} mins)",
        xaxis_title="Hours Ahead",
        yaxis_title="Level (1-10)",
        xaxis=dict(tickmode='array', tickvals=horizons),
        yaxis=dict(range=[0, 10]),
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white', size=14)
    )

    insights = []
    food = str(row['food']).lower()
    ex_type = str(row['exercise_type']).lower()
    duration = row['exercise_duration']

    if "sugary" in food or "junk" in food:
        insights.append("⚠️ High sugar or junk food detected, mood and energy may drop quickly.")
    if "protein" in food:
        insights.append("💪 Protein-rich food linked to more stable mood and energy.")
    if "exercise" in ex_type:
        if duration < 30:
            insights.append("🏃‍♂️ Moderate exercise can help maintain mood and energy.")
        else:
            insights.append("🏅 High exercise duration: mood stabilizes but energy might drop faster.")
    if not insights:
        insights.append("📝 Keep tracking your mood and energy for personalized insights.")

    return fig, html.Ul([html.Li(i) for i in insights])


# ML training and predictions from uploaded file
trained_models = {"mood": None, "energy": None}

@app.callback(
    Output('user-prediction-graph', 'figure'),
    Output('upload-insight-output', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def process_uploaded_file(contents, filename):
    global trained_models
    if contents is None:
        return go.Figure(), ""

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return go.Figure(layout={'title': f'Error loading file: {str(e)}'}), ""

    required_cols = {'mood_now', 'energy_now', 'mood_48h', 'energy_48h'}
    if not required_cols.issubset(df.columns):
        return go.Figure(layout={'title': 'CSV missing required columns: mood_now, energy_now, mood_48h, energy_48h'}), ""

    X = df[['mood_now', 'energy_now']].values
    y_mood = df['mood_48h'].values
    y_energy = df['energy_48h'].values

    model_mood = LinearRegression().fit(X, y_mood)
    model_energy = LinearRegression().fit(X, y_energy)

    trained_models['mood'] = model_mood
    trained_models['energy'] = model_energy

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=y_mood, mode='markers', name='Actual Mood 48h'))
    fig.add_trace(go.Scatter(y=model_mood.predict(X), mode='lines', name='Predicted Mood 48h'))
    fig.add_trace(go.Scatter(y=y_energy, mode='markers', name='Actual Energy 48h'))
    fig.add_trace(go.Scatter(y=model_energy.predict(X), mode='lines', name='Predicted Energy 48h'))

    fig.update_layout(
        title=f"Predictions from uploaded file: {filename}",
        yaxis_title="Level (1-10)",
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white', size=14)
    )

    insight_text = "✅ Model trained on your data! Now enter your current status below to see predictions."

    return fig, insight_text


# Personalized prediction from user input & trained model
@app.callback(
    Output('personalized-prediction-graph', 'figure'),
    Output('personalized-prediction-insight', 'children'),
    Input('predict-button', 'n_clicks'),
    State('input-food', 'value'),
    State('input-exercise-type', 'value'),
    State('input-exercise-duration', 'value'),
    State('input-mood-now', 'value'),
    State('input-energy-now', 'value')
)
def personalized_prediction(n_clicks, food, ex_type, duration, mood_now, energy_now):
    if n_clicks == 0 or trained_models['mood'] is None or trained_models['energy'] is None:
        return go.Figure(), ""

    # Use trained models to predict 48h mood and energy from current mood and energy
    X_input = np.array([[mood_now, energy_now]])
    pred_mood_48h = trained_models['mood'].predict(X_input)[0]
    pred_energy_48h = trained_models['energy'].predict(X_input)[0]

    # Create linear decay from now to 48h prediction for demo purposes
    pred_mood_vals = np.linspace(mood_now, pred_mood_48h, num=len(horizons))
    pred_energy_vals = np.linspace(energy_now, pred_energy_48h, num=len(horizons))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=horizons, y=pred_mood_vals, mode='lines+markers', name="Predicted Mood",
                             line=dict(color="cyan", width=3), marker=dict(symbol='circle', size=10)))
    fig.add_trace(go.Scatter(x=horizons, y=pred_energy_vals, mode='lines+markers', name="Predicted Energy",
                             line=dict(color="magenta", width=3), marker=dict(symbol='square', size=10)))

    fig.update_layout(
        title="Personalized Mood & Energy Prediction",
        xaxis_title="Hours Ahead",
        yaxis_title="Level (1-10)",
        xaxis=dict(tickmode='array', tickvals=horizons),
        yaxis=dict(range=[0, 10]),
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white', size=14)
    )

    # Simple insights based on input
    insights = []
    food_lc = (food or "").lower()
    ex_lc = (ex_type or "").lower()
    duration = duration or 0

    if "sugary" in food_lc or "junk" in food_lc:
        insights.append("⚠️ Sugary or junk food can cause mood and energy to drop faster.")
    if "protein" in food_lc:
        insights.append("💪 Protein may help stabilize mood and energy.")
    if "exercise" in ex_lc or ex_lc.strip():
        if duration < 30:
            insights.append("🏃‍♂️ Moderate exercise can help maintain mood and energy.")
        else:
            insights.append("🏅 Longer exercise may stabilize mood but energy might dip.")

    if not insights:
        insights.append("📝 Track your habits to better understand your mood and energy.")

    return fig, html.Ul([html.Li(i) for i in insights])


if __name__ == '__main__':
    app.run_server(debug=True)
