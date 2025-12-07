import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq
from pymongo import MongoClient
from bson.json_util import default

load_dotenv()

st.set_page_config(
    page_title="Customer Feedback System",
    page_icon="⭐",
    layout="centered"
)

# <CHANGE> Initialize MongoDB connection
def get_mongo_client():
    try:
        mongodb_uri = st.secrets.get("MONGODB_URI") or os.getenv("MONGODB_URI")
    except:
        mongodb_uri = os.getenv("MONGODB_URI")
    
    if not mongodb_uri:
        st.error("⚠️ MONGODB_URI not found. Please set it in your environment variables or Streamlit secrets.")
        st.stop()
    
    return MongoClient(mongodb_uri)

def get_database():
    client = get_mongo_client()
    return client.get_database()

def get_feedback_collection():
    db = get_database()
    return db.feedback

def get_groq_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        st.error("⚠️ GROQ_API_KEY not found. Please set it in your environment variables or Streamlit secrets.")
        st.stop()
    
    return Groq(api_key=api_key)

# <CHANGE> Replace JSON file operations with MongoDB operations
def load_data():
    collection = get_feedback_collection()
    return list(collection.find().sort("_id", -1))

def save_data(feedback_entry):
    collection = get_feedback_collection()
    collection.insert_one(feedback_entry)

def generate_ai_response(rating, review):
    client = get_groq_client()
    
    prompt = f"""You are a customer service AI. A customer has left the following feedback:

Rating: {rating}/5 stars
Review: {review}

Generate a personalized, empathetic response to this customer. The response should:
1. Thank them for their feedback
2. Address their specific concerns or praise
3. Be warm and professional
4. Be concise (2-3 sentences)

Response:"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"AI response generation failed: {str(e)}")
        return "Thank you for your feedback! We appreciate you taking the time to share your experience with us."

def generate_summary(review):
    client = get_groq_client()
    
    prompt = f"""Summarize the following customer review in one concise sentence (max 15 words):

Review: {review}

Summary:"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=50
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"Summary generation failed: {str(e)}")
        return "Customer feedback received"

def generate_actions(rating, review):
    client = get_groq_client()
    
    prompt = f"""Based on this customer feedback, suggest 2-3 specific actionable next steps for the business:

Rating: {rating}/5 stars
Review: {review}

Provide only the action items as a bullet-point list. Be specific and practical.

Actions:"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=200
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"Actions generation failed: {str(e)}")
        return "• Review and address customer feedback\n• Follow up with customer if needed"

def main():
    st.title("⭐ Customer Feedback System")
    st.write("We value your opinion! Please share your experience with us.")
    
    with st.form("feedback_form", clear_on_submit=True):
        
        st.subheader("How would you rate your experience?")
        rating = st.slider("Select rating", min_value=1, max_value=5, value=5, 
                          format="%d ⭐")
        
        
        st.subheader("Tell us more about your experience")
        review = st.text_area("Your review", placeholder="Share your thoughts...", 
                             height=150, max_chars=10000)
        
        
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True)
        
        if submitted:
            if not review.strip():
                st.error("Please write a review before submitting.")
            else:
                with st.spinner("Processing your feedback..."):
                    
                    ai_response = generate_ai_response(rating, review)
                    ai_summary = generate_summary(review)
                    ai_actions = generate_actions(rating, review)
                    
                    
                    feedback_entry = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                        "timestamp": datetime.now().isoformat(),
                        "rating": rating,
                        "review": review,
                        "ai_response": ai_response,
                        "ai_summary": ai_summary,
                        "ai_actions": ai_actions
                    }
                    
                    save_data(feedback_entry)
                    
                    st.success("✅ Thank you for your feedback!")
                    
                    st.info(f"**Our Response:**\n\n{ai_response}")
                    
                    if rating >= 4:
                        st.balloons()

    st.markdown("---")
    st.caption("Your feedback helps us improve our service. Thank you!")

if __name__ == "__main__":
    main()