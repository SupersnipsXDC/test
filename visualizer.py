import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import networkx as nx
from dash import dcc, html, Dash
from dash.dependencies import Input, Output, State
import threading
import webbrowser
import time
from config import DB_NAME
from generate_pdf_report import generate_pdf_report

import os
from flask import send_from_directory

app_dir = os.path.abspath("reports")
dash_app = Dash(__name__, suppress_callback_exceptions=True)
server = dash_app.server

@server.route("/download/<path:filename>")
def download_pdf(filename):
    return send_from_directory(app_dir, filename, as_attachment=True)


def launch_dashboard(result_text, root):
    result_text.insert("end", "
🚀 Lade KI-Modelle...
")
    try:
        from analyzer_refactored import load_models
        load_models()
        result_text.insert("end", "✅ Modelle geladen.
")
    except Exception as e:
        result_text.insert("end", f"❌ Fehler beim Laden der Modelle: {e}
")

    result_text.insert("end", "📦 Lade Dashboard...")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM narratives", conn)
    result_text.insert("end", f"
📊 Gelesene Datensätze: {len(df)}
")
    result_text.insert("end", f"📑 Spalten: {df.columns.tolist()}
")
    result_text.insert("end", f"🧪 NaN-Zeilen: {df.isnull().sum().to_dict()}
")
    conn.close()

    if df.empty or 'date' not in df or df['date'].isnull().all():
        result_text.insert("end", "Keine Daten für Dashboard verfügbar.
")
        return

    df['date'] = pd.to_datetime(df['date'], utc=True, errors='coerce')
    if 'keywords' not in df or df['keywords'].isnull().all():
        result_text.insert("end", "Keywords fehlen für Dashboard-Plot.
")
        return

    try:
        time_series = df.groupby([pd.Grouper(key='date', freq='D'), 'keywords']).size().unstack(fill_value=0)
        fig1 = px.line(time_series, title="Keyword Frequency Over Time")
    except Exception as e:
        result_text.insert("end", f"Fehler beim Plotten: {e}
")
        return

    dash_app.layout = html.Div([
        html.H1("Migration Narrative Analyzer Dashboard"),
        dcc.Interval(id='interval-component', interval=30000, n_intervals=0),
        dcc.Graph(id="time-series", figure=fig1),
        html.Button("📥 Download PDF Report", id="pdf-button"),
        html.Div(id="pdf-output")
    ])

    @dash_app.callback(
        Output("time-series", "figure"),
        Input("interval-component", "n_intervals")
    )
    def update_fig(n):
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM narratives", conn)
        conn.close()
        df['date'] = pd.to_datetime(df['date'], utc=True, errors='coerce')
        time_series = df.groupby([pd.Grouper(key='date', freq='D'), 'keywords']).size().unstack(fill_value=0)
        return px.line(time_series, title="Keyword Frequency Over Time")

    @dash_app.callback(
        Output("pdf-output", "children"),
        Input("pdf-button", "n_clicks"),
        prevent_initial_call=True
    )
    def generate_pdf(n):
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM narratives", conn)
        conn.close()
        df['date'] = pd.to_datetime(df['date'], utc=True, errors='coerce')
        try:
            from bertopic import BERTopic
            if not os.path.exists("bertopic_model"):
                raise FileNotFoundError("BERTopic-Modell 'bertopic_model' nicht gefunden.")
            model = BERTopic.load("bertopic_model")
            filepath = generate_pdf_report(df, model, filename_prefix='report_clustered')
            pdf_name = filepath.split(os.sep)[-1]
            return html.Div([
                html.P("📄 PDF gespeichert: ", style={"display": "inline"}),
                html.A(pdf_name, href=f"/download/{pdf_name}", target="_blank")
            ])
        except Exception as e:
            return f"Fehler beim Erstellen der PDF: {e}"

    def run_dash():
        dash_app.run(debug=True, port=8051, use_reloader=False)

    threading.Thread(target=run_dash, daemon=True).start()
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8051")
    result_text.insert("end", "Dashboard gestartet unter http://127.0.0.1:8051
")
