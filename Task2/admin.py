import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from groq import Groq
from pymongo import MongoClient

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "feedback_system"  # Specify your database name here
COLLECTION_NAME = "user_feedback"

def get_database():
    """Get MongoDB database connection"""
    if not MONGODB_URI:
        st.error("MONGODB_URI environment variable not set")
        st.stop()
    client = MongoClient(MONGODB_URI)
    return client[DB_NAME]

def get_feedback_collection():
    """Get feedback collection"""
    db = get_database()
    return db[COLLECTION_NAME]

def load_data():
    """Load all feedback from MongoDB"""
    collection = get_feedback_collection()
    return list(collection.find({}, {"_id": 0}))

def get_dataframe():
    """Convert MongoDB data to DataFrame"""
    data = load_data()
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_groq_insights(feedback_list):
    """Get AI insights from Groq"""
    client = Groq()
    feedback_text = "\n".join([f"- {item['feedback']}" for item in feedback_list])
    
    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {"role": "system", "content": "You are a customer feedback analysis expert. Provide concise, actionable insights."},
            {"role": "user", "content": f"Analyze these customer feedback items and provide key insights:\n\n{feedback_text}"}
        ],
        temperature=1,
        max_tokens=1024,
    )
    return completion.choices[0].message.content

def main():
    st.set_page_config(page_title="Customer Feedback System - Admin", layout="wide")
    st.title("📊 Admin Dashboard - Customer Feedback Analysis")
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    df = get_dataframe()
    
    if df.empty:
        st.info("No feedback data available yet.")
        return
    
    # Summary Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Feedbacks", len(df))
    
    with col2:
        avg_rating = df["rating"].mean()
        st.metric("Average Rating", f"{avg_rating:.2f}/5")
    
    with col3:
        st.metric("Total Categories", df["category"].nunique())
    
    with col4:
        st.metric("Unique Users", df["email"].nunique())
    
    st.markdown("---")
    
    # Feedback Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Feedback by Category")
        category_counts = df["category"].value_counts()
        st.bar_chart(category_counts)
    
    with col2:
        st.subheader("Rating Distribution")
        rating_counts = df["rating"].value_counts().sort_index()
        st.bar_chart(rating_counts)
    
    st.markdown("---")
    
    # AI Insights
    st.subheader("🤖 AI-Powered Insights")
    if st.button("Generate AI Insights"):
        feedback_list = load_data()
        if feedback_list:
            with st.spinner("Generating insights..."):
                insights = get_groq_insights(feedback_list)
                st.success(insights)
    
    st.markdown("---")
    
    # Detailed Feedback Table
    st.subheader("📋 All Feedback")
    st.dataframe(df, use_container_width=True)
    
    # Export option
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()