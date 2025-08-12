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

# Load your mood_energy_dataset.csv with your columns
DATA_FILE = "mood_energy_dataset.csv"
if os.path.exists(DATA_FILE):
    mood_energy_df = pd.read_csv(DATA_FILE)
    mood_energy_df['datetime'] = pd.to_datetime(mood_energy_df['datetime'])
else:
    mood_energy_df = pd.DataFrame()  # fallback empty

# Generate scenario options dynamically from food + exercise_type + duration
scenario_options = [
    {
        'label': f"{row['food']} + {row['exercise_type']} ({row['exercise_duration']} mins)",
        'value': idx
    }
    for idx, row in mood_energy_df.iterrows()
]

# Time horizons (hours) from your column suffixes
horizons = [0, 2, 6, 12, 24, 48]  # Added 0 for initial time

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Mood & Energy Trends Dashboard"),

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

    dcc.Graph(id='user-prediction-graph', style={"marginTop": "40px"}),

    html.Div(id="upload-insight-output", style={"marginTop": "20px", "fontSize": "16px", "color": "orange"})
])

@app.callback(
    Output("trend-graph", "figure"),
    Output("insight-output", "children"),
    Input("scenario-dropdown", "value"),
)
def update_trends(selected_idx):
    if selected_idx is None or mood_energy_df.empty:
        return go.Figure(), "No data available."

    # Select row by index
    row = mood_energy_df.iloc[selected_idx]

    # Extract mood and energy values at horizons including time 0
    mood_vals = [row['mood_now']] + [row[f"mood_{h}h"] for h in horizons if h != 0]
    energy_vals = [row['energy_now']] + [row[f"energy_{h}h"] for h in horizons if h != 0]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=horizons, y=mood_vals,
        mode='lines+markers',
        name="Mood",
        line=dict(color="cyan", width=3),
        marker=dict(symbol='circle', size=10)
    ))

    fig.add_trace(go.Scatter(
        x=horizons, y=energy_vals,
        mode='lines+markers',
        name="Energy",
        line=dict(color="magenta", width=3),
        marker=dict(symbol='square', size=10)
    ))

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

    # Insights
    insights = []
    if "sugary" in str(row['food']).lower() or "junk" in str(row['food']).lower():
        insights.append("⚠️ High sugar or junk food detected, mood and energy may drop quickly.")
    if "protein" in str(row['food']).lower():
        insights.append("💪 Protein-rich food linked to more stable mood and energy.")
    if "exercise" in str(row['exercise_type']).lower():
        duration = row['exercise_duration']
        if duration < 30:
            insights.append("🏃‍♂️ Moderate exercise can help maintain mood and energy.")
        else:
            insights.append("🏅 High exercise duration: mood stabilizes but energy might drop faster.")
    if not insights:
        insights.append("📝 Keep tracking your mood and energy for personalized insights.")

    insight_html = html.Ul([html.Li(i) for i in insights])

    return fig, insight_html


@app.callback(
    Output('user-prediction-graph', 'figure'),
    Output('upload-insight-output', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def process_uploaded_file(contents, filename):
    if contents is None:
        return go.Figure(), ""

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        # Assume CSV file
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return go.Figure(layout={'title': f'Error loading file: {str(e)}'}), ""

    # Check for required columns
    required_cols = {'mood_now', 'energy_now', 'mood_48h', 'energy_48h'}
    if not required_cols.issubset(set(df.columns)):
        return go.Figure(layout={'title': 'CSV missing required columns: mood_now, energy_now, mood_48h, energy_48h'}), ""

    # Train simple Linear Regression models to predict 48h mood and energy from current mood and energy
    features = df[['mood_now', 'energy_now']].values
    target_mood = df['mood_48h'].values
    target_energy = df['energy_48h'].values

    model_mood = LinearRegression().fit(features, target_mood)
    model_energy = LinearRegression().fit(features, target_energy)

    preds_mood = model_mood.predict(features)
    preds_energy = model_energy.predict(features)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=target_mood, mode='markers', name='Actual Mood 48h'))
    fig.add_trace(go.Scatter(y=preds_mood, mode='lines', name='Predicted Mood 48h'))
    fig.add_trace(go.Scatter(y=target_energy, mode='markers', name='Actual Energy 48h'))
    fig.add_trace(go.Scatter(y=preds_energy, mode='lines', name='Predicted Energy 48h'))

    fig.update_layout(
        title=f"Predictions from uploaded file: {filename}",
        yaxis_title="Level (1-10)",
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white', size=14)
    )

    insight_text = "✅ Model trained on your data! Actual vs predicted mood and energy at 48h shown."

    return fig, insight_text


if __name__ == '__main__':
    app.run_server(debug=True)
