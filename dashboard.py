import sqlite3
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Output, Input
import threading
import webbrowser
import time
from config import DB_NAME
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

dash_app = Dash(__name__)

dash_app.layout = html.Div([
    html.H1("Migration Narrative Analyzer Dashboard", style={'textAlign': 'center', 'color': '#007ACC'}),
    dcc.Graph(id="time-series"),
    dcc.Graph(id="sentiment-dist"),
    dcc.Interval(id="interval-component", interval=60*1000, n_intervals=0)
], style={'backgroundColor': '#F5F5F5', 'padding': '20px'})

def update_time_series(n):
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM narratives", conn)
    if df.empty or 'date' not in df or df['date'].isnull().all():
        return px.line(title="Keine Daten verfügbar")
    df['date'] = pd.to_datetime(df['date'], utc=True)
    time_series = df.groupby([pd.Grouper(key='date', freq='D'), 'keywords']).size().unstack(fill_value=0)
    return px.line(time_series, title="Keyword-Häufigkeit über Zeit", labels={"value": "Anzahl Tweets", "date": "Datum"})

def update_sentiment_dist(n):
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM narratives", conn)
    if df.empty or 'sentiment' not in df:
        return px.bar(title="Keine Sentiment-Daten verfügbar")
    return px.histogram(df, x="sentiment", title="Sentiment-Verteilung", nbins=20)

dash_app.callback(Output("time-series", "figure"), Input("interval-component", "n_intervals"))(update_time_series)
dash_app.callback(Output("sentiment-dist", "figure"), Input("interval-component", "n_intervals"))(update_sentiment_dist)

def launch_dashboard():
    def run_dash():
        dash_app.run(debug=False, port=8051, use_reloader=False)
    threading.Thread(target=run_dash, daemon=True).start()
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8051")