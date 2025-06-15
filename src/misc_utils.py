from dash import html
import plotly.graph_objects as go

def get_rain_icon(rain_mm):
    if rain_mm < 0.2:
        return html.I(className="bi bi-sun", style={"fontSize": "1.8rem", "color": "#f7c948"})
    elif rain_mm < 2:
        return html.I(className="bi bi-cloud-sun", style={"fontSize": "1.8rem", "color": "#f0ad4e"})
    elif rain_mm < 5:
        return html.I(className="bi bi-cloud-drizzle", style={"fontSize": "1.8rem", "color": "#17a2b8"})
    elif rain_mm < 10:
        return html.I(className="bi bi-cloud-rain", style={"fontSize": "1.8rem", "color": "#0d6efd"})
    elif rain_mm < 20:
        return html.I(className="bi bi-cloud-rain-heavy", style={"fontSize": "1.8rem", "color": "#0d6efd"})
    else:
        return html.I(className="bi bi-cloud-lightning-rain", style={"fontSize": "1.8rem", "color": "#280452"})


def pressure_gauge_figure(pressure_value):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pressure_value,
            number={"suffix": "Pa", "font": {"size": 32, "color": "black", "family": "sans-serif"}},
            gauge={
                'axis': {'range': [90000, 110000], 'tickwidth': 1, 'tickcolor': "gray"},
                'bar': {'color': "black"},
                'borderwidth': 0,
                'bgcolor': "rgb(230, 230, 230)",
            },
            domain={'x': [0, 1], 'y': [0, 1]}
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",  
            margin=dict(t=50, b=40, l=30, r=30),
            height=220
        )
        return fig