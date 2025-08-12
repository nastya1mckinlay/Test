import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import datetime
import plotly.graph_objects as go
import os
import time

app = dash.Dash(__name__)
server = app.server

DATA_FILE = "data.csv"
MOOD_ENERGY_FILE = "mood_energy_dataset.csv"

food_tags = ['Healthy', 'Sugary', 'Junk', 'Protein', 'Carbs']
activities = ['None', 'Low Exercise', 'Moderate Exercise', 'High Exercise', 'Outdoors', 'Socializing', 'Gaming', 'Studying', 'Party']

# Load mood_energy dataset for scenarios
mood_energy_df = pd.read_csv(MOOD_ENERGY_FILE)
scenario_options = [{'label': row['Scenario'], 'value': row['Scenario']} for _, row in mood_energy_df.iterrows()]

# Layout
app.layout = html.Div([
    html.H1("🌟 MindFuel Mood & Energy Trends"),

    html.Label("Select Scenario:"),
    dcc.Dropdown(
        id="scenario-dropdown",
        options=scenario_options,
        value=scenario_options[0]['value'],  # Default to first scenario
        clearable=False,
        style={"width": "400px", "marginBottom": "20px"},
    ),

    dcc.Graph(id="trend-graph"),

    # Your other existing UI elements here like user/demo data inputs, buttons etc...
])

# Callback to update graph when scenario changes
@app.callback(
    Output("trend-graph", "figure"),
    Input("scenario-dropdown", "value")
)
def update_trend_graph(selected_scenario):
    if not selected_scenario:
        return go.Figure()

    # Filter dataset for selected scenario
    row = mood_energy_df[mood_energy_df['Scenario'] == selected_scenario].iloc[0]

    horizons = [2, 6, 12, 24, 48]
    mood_cols = [f"mood_{h}h" for h in horizons]
    energy_cols = [f"energy_{h}h" for h in horizons]

    mood_vals = row[mood_cols].values.astype(float)
    energy_vals = row[energy_cols].values.astype(float)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=horizons,
        y=mood_vals,
        mode="lines+markers",
        name="Mood",
        line=dict(color="#00e5ff", width=3),
        marker=dict(size=8),
    ))

    fig.add_trace(go.Scatter(
        x=horizons,
        y=energy_vals,
        mode="lines+markers",
        name="Energy",
        line=dict(color="#ff4081", width=3),
        marker=dict(size=8, symbol="square"),
    ))

    # Fill area between mood and energy with different colors
    fillcolor = ["#ffee58" if m >= e else "#69f0ae" for m, e in zip(mood_vals, energy_vals)]
    shapes = []
    for i in range(len(horizons) - 1):
        shapes.append(dict(
            type="rect",
            xref="x",
            yref="y",
            x0=horizons[i],
            y0=min(mood_vals[i], energy_vals[i]),
            x1=horizons[i + 1],
            y1=max(mood_vals[i], energy_vals[i]),
            fillcolor=fillcolor[i],
            opacity=0.15,
            line_width=0,
            layer="below",
        ))
    fig.update_layout(shapes=shapes)

    fig.update_layout(
        title=f"Mood & Energy Trends: {selected_scenario}",
        xaxis_title="Hours Ahead",
        yaxis_title="Level (1-10)",
        yaxis=dict(range=[0, 10]),
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(font=dict(size=14)),
        margin=dict(t=50, b=40, l=40, r=20),
    )
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
