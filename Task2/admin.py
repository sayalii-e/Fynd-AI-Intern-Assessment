import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="Admin Dashboard", page_icon="📊", layout="wide")

def get_db():
    mongo_uri = os.getenv("MONGO_URI", st.secrets.get("MONGO_URI", None))
    if not mongo_uri:
        st.error("⚠️ MONGO_URI not found. Please set it in environment variables or Streamlit secrets.")
        st.stop()
    client = MongoClient(mongo_uri)
    return client["feedbackDB"]["feedbacks"]

def get_dataframe():
    collection = get_db()
    data = list(collection.find({}, {"_id": 0}))
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    return df

def main():
    st.title("📊 Admin Dashboard")
    st.write("Monitor and analyze customer feedback in real-time.")

    if st.button("🔄 Refresh Data"):
        st.rerun()

    df = get_dataframe()
    if df.empty:
        st.info("📭 No feedback submissions yet.")
        return

    st.header("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Submissions", len(df))
    with col2:
        st.metric("Average Rating", f"{df['rating'].mean():.2f} ⭐")
    with col3:
        pos = (df['rating'] >= 4).sum()
        st.metric("Positive Feedback", f"{pos/len(df)*100:.1f}%")
    with col4:
        neg = (df['rating'] <= 2).sum()
        st.metric("Negative Feedback", neg)

    st.markdown("---")
    st.header("📊 Analytics")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df["rating"].value_counts().sort_index(), title="Rating Distribution")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        timeline = df.groupby("date").size().reset_index(name="count")
        fig2 = px.line(timeline, x="date", y="count", markers=True, title="Feedback Over Time")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.header("🔍 All Feedback")

    for _, row in df.sort_values("timestamp", ascending=False).iterrows():
        with st.expander(f"⭐ {row['rating']} — {row['timestamp']}"):
            st.write(f"**Review:** {row['review']}")
            st.info(f"**Summary:** {row['ai_summary']}")
            st.success(f"**Response:** {row['ai_response']}")
            st.warning(f"**Actions:**\n{row['ai_actions']}")

    st.markdown("---")
    st.download_button(
        "📥 Export as CSV",
        df.to_csv(index=False),
        file_name=f"feedback_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()