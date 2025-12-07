import os
import json
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

def save_data(data):
    """Save feedback to MongoDB"""
    collection = get_feedback_collection()
    collection.insert_one(data)

def load_all_data():
    """Load all feedback from MongoDB"""
    collection = get_feedback_collection()
    return list(collection.find({}, {"_id": 0}))

def get_groq_response(user_message):
    """Get response from Groq API"""
    client = Groq()
    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {"role": "system", "content": "You are a helpful customer feedback analysis assistant."},
            {"role": "user", "content": user_message}
        ],
        temperature=1,
        max_tokens=1024,
    )
    return completion.choices[0].message.content

def main():
    st.set_page_config(page_title="Customer Feedback System - User", layout="wide")
    st.title("📝 Customer Feedback Form")
    
    st.markdown("---")
    
    with st.form("feedback_form"):
        st.subheader("Share Your Feedback")
        
        name = st.text_input("Your Name", placeholder="Enter your name")
        email = st.text_input("Your Email", placeholder="Enter your email")
        rating = st.slider("Rate Your Experience", 1, 5, 3)
        category = st.selectbox("Feedback Category", ["Product", "Service", "Support", "Other"])
        feedback_text = st.text_area("Your Feedback", placeholder="Tell us what you think...", height=150)
        
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            if not name or not email or not feedback_text:
                st.error("Please fill in all required fields!")
            else:
                feedback_entry = {
                    "name": name,
                    "email": email,
                    "rating": int(rating),
                    "category": category,
                    "feedback": feedback_text,
                    "timestamp": datetime.now().isoformat()
                }
                
                save_data(feedback_entry)
                st.success("✅ Thank you! Your feedback has been saved.")
                
                with st.spinner("Generating AI response..."):
                    ai_prompt = f"Analyze this customer feedback and provide a brief response:\n\nName: {name}\nRating: {rating}/5\nCategory: {category}\nFeedback: {feedback_text}"
                    ai_response = get_groq_response(ai_prompt)
                    st.info(f"**AI Response:**\n\n{ai_response}")

if __name__ == "__main__":
    main()