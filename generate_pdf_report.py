import os
import time
from reportlab.pdfgen import canvas  # Corrected import
from reportlab.lib.pagesizes import letter
import pandas as pd
import plotly.express as px
import plotly.io as pio
import tempfile
import logging

# Assuming these are part of your project; adjust imports if paths differ
from narrative_analyzer import NarrativeAnalyzer
from lexicon import NarrativeLexicon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def generate_pdf_report(df: pd.DataFrame, model, lexicon: NarrativeLexicon, filename_prefix="report"):
    """
    Generate a PDF report summarizing migration narrative analysis.

    Args:
        df (pd.DataFrame): DataFrame containing tweet data.
        model: Trained model for analysis (assumed to be passed from caller).
        lexicon (NarrativeLexicon): Lexicon object for narrative descriptions.
        filename_prefix (str): Prefix for the output PDF filename.

    Returns:
        str or None: Path to the generated PDF or None if an error occurs.
    """
    try:
        # Create reports directory and define filepath
        filepath = os.path.join("reports", f"{filename_prefix}_{int(time.time())}.pdf")
        os.makedirs("reports", exist_ok=True)

        # Initialize Canvas for PDF generation
        c = canvas.Canvas(filepath, pagesize=letter)

        # Title and metadata
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, "Migration Narrative Analysis Report")
        c.setFont("Helvetica", 12)
        c.drawString(100, 730, f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Sentiment Distribution Plot
        if 'sentiment' in df.columns:
            fig = px.histogram(df, x="sentiment", title="Sentiment Distribution")
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                pio.write_image(fig, tmpfile.name, format="png")
                c.drawImage(tmpfile.name, 100, 500, width=400, height=200)
                os.remove(tmpfile.name)

        # New page for Cluster Summary
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "Cluster Summary")
        c.setFont("Helvetica", 12)
        y = 700
        for cluster in df['topic_id'].unique():
            if cluster != -1:
                cluster_df = df[df['topic_id'] == cluster]
                c.drawString(100, y, f"Cluster {cluster}: {len(cluster_df)} Tweets")
                top_tweet = cluster_df.sort_values('risk_score', ascending=False).iloc[0]['text']
                c.drawString(120, y - 20, f"Top Tweet: {top_tweet[:100]}...")
                y -= 40

        # New page for Influential Accounts
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "Influential Accounts")
        c.setFont("Helvetica", 12)
        y = 700
        influential = df.groupby('user').agg({'followers': 'max', 'retweets': 'sum'}).nlargest(5, 'retweets')
        for user, row in influential.iterrows():
            c.drawString(100, y, f"{user}: {row['followers']} Followers, {row['retweets']} Retweets")
            y -= 20

        # New page for Sentiment Over Time
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "Sentiment Over Time")
        fig = px.line(df.groupby(df['date'].dt.date)['sentiment'].mean(), title="Sentiment Over Time")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            pio.write_image(fig, tmpfile.name, format="png")
            c.drawImage(tmpfile.name, 100, 500, width=400, height=200)
            os.remove(tmpfile.name)

        # New page for Narrative Lexicon
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "Narrative Lexicon")
        c.setFont("Helvetica", 12)
        y = 700
        for topic_id, description in lexicon.get_lexicon().items():
            c.drawString(100, y, f"Cluster {topic_id}: {description}")
            y -= 20

        # Save the PDF
        c.save()
        logging.info(f"PDF report generated: {filepath}")
        return filepath

    except Exception as e:
        logging.error(f"Error generating PDF report: {e}")
        return None