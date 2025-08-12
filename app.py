import plotly.graph_objects as go

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
    score_text = f"⭐ Score: {user_score['score']}" if mode == 'user' else ""
    if mode == 'demo':
        filtered = [r for r in demo_records if r['Foods'] in [d['Foods'] for d in demo_cases[demo_case]]]
        data = pd.DataFrame(filtered)
    else:
        data = pd.DataFrame(user_records)

    if not data.empty:
        data['Date'] = pd.to_datetime(data['Date']).dt.date
        if mode == 'user':
            data = data.tail(50)

        # Sort by date to keep lines smooth
        data = data.sort_values("Date")

        fig = go.Figure()

        # Mood line
        fig.add_trace(go.Scatter(
            x=data['Date'], y=data['Mood'],
            mode='lines+markers',
            line=dict(color='#00e5ff', width=3),
            marker=dict(size=6),
            name='Mood'
        ))

        # Energy line
        fig.add_trace(go.Scatter(
            x=data['Date'], y=data['Energy'],
            mode='lines+markers',
            line=dict(color='#ff4081', width=3),
            marker=dict(size=6),
            name='Energy'
        ))

        # Ribbon for Mood > Energy
        above_mask = data['Mood'] > data['Energy']
        fig.add_trace(go.Scatter(
            x=data['Date'][above_mask].tolist() + data['Date'][above_mask][::-1].tolist(),
            y=data['Mood'][above_mask].tolist() + data['Energy'][above_mask][::-1].tolist(),
            fill='toself',
            fillcolor='rgba(255, 238, 88, 0.2)',  # yellow
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo='skip',
            showlegend=False
        ))

        # Ribbon for Energy >= Mood
        below_mask = data['Energy'] >= data['Mood']
        fig.add_trace(go.Scatter(
            x=data['Date'][below_mask].tolist() + data['Date'][below_mask][::-1].tolist(),
            y=data['Mood'][below_mask].tolist() + data['Energy'][below_mask][::-1].tolist(),
            fill='toself',
            fillcolor='rgba(118, 255, 3, 0.2)',  # neon green
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo='skip',
            showlegend=False
        ))

        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#111111',
            paper_bgcolor='#111111',
            font=dict(color='white'),
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis=dict(range=[1, 5], title='Level (1–5)'),
            xaxis_title='Date'
        )

        recent = data.tail(5)
        all_foods = ','.join(recent['Foods'].dropna())
        all_acts = ','.join(recent['Activities'].dropna())

        insight = []
        if recent['Mood'].mean() > 3.5:
            insight.append("😊 Great mood lately!")
        if 'Sugary' in all_foods:
            insight.append("🍬 Watch sugar intake.")
        if 'Exercise' in all_acts:
            insight.append("💪 Exercise helps energy!")
        if 'Junk' in all_foods and recent['Mood'].mean() < 3:
            insight.append("🍔 Junk food may be lowering mood.")
        if not insight:
            insight = ["📊 Keep logging to see insights."]
    else:
        fig = go.Figure().update_layout(template='plotly_dark')
        insight = ["📊 No data to show."]

    return fig, html.Ul([html.Li(i) for i in insight]), score_text
