import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import datetime
import os

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
horizons = [2, 6, 12, 24, 48]

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
    html.H3("Add Your Data (User Mode) - Coming Soon!"),
    # You can extend input forms here for user input if desired.
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

    # Extract mood and energy values at horizons
    mood_vals = [row[f"mood_{h}h"] for h in horizons]
    energy_vals = [row[f"energy_{h}h"] for h in horizons]

    # Create traces for mood and energy
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


if __name__ == '__main__':
    app.run_server(debug=True)
