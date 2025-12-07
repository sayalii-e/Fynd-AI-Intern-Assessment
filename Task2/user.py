import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from groq import Groq

load_dotenv()

st.set_page_config(page_title="Customer Feedback System", page_icon="⭐", layout="centered")

# MongoDB connection
def get_db():
    mongo_uri = os.getenv("MONGO_URI", st.secrets.get("MONGO_URI", None))
    if not mongo_uri:
        st.error("⚠️ MONGO_URI not found. Set it in environment variables or Streamlit secrets.")
        st.stop()
    client = MongoClient(mongo_uri)
    return client["feedbackDB"]["feedbacks"]

# GROQ client
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", None))
    if not api_key:
        st.error("⚠️ GROQ_API_KEY not found.")
        st.stop()
    return Groq(api_key=api_key)

def generate_ai_response(rating, review):
    client = get_groq_client()
    prompt = f"""You are a customer service AI. A customer left this review:

Rating: {rating}/5
Review: {review}

Write a warm, professional, concise (2–3 sentence) response addressing their feedback."""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"AI failed: {e}")
        return "Thank you for your feedback!"

def generate_summary(review):
    client = get_groq_client()
    prompt = f"Summarize this customer review in one concise sentence: {review}"
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=50
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return "Feedback summary unavailable"

def generate_actions(rating, review):
    client = get_groq_client()
    prompt = f"""Suggest 2–3 specific next actions for the business based on this feedback:

Rating: {rating}/5
Review: {review}

Output as bullet points."""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=150
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return "• Review and address feedback\n• Follow up with customer"

def main():
    st.title("⭐ Customer Feedback System")
    st.write("We value your opinion! Please share your experience with us.")

    collection = get_db()

    with st.form("feedback_form", clear_on_submit=True):
        rating = st.slider("Select rating", 1, 5, 5, format="%d ⭐")
        review = st.text_area("Your review", placeholder="Type your feedback here...", height=150)
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True)

        if submitted:
            if not review.strip():
                st.error("Please write a review before submitting.")
            else:
                with st.spinner("Processing your feedback..."):
                    ai_response = generate_ai_response(rating, review)
                    ai_summary = generate_summary(review)
                    ai_actions = generate_actions(rating, review)

                    entry = {
                        "timestamp": datetime.now().isoformat(),
                        "rating": rating,
                        "review": review,
                        "ai_response": ai_response,
                        "ai_summary": ai_summary,
                        "ai_actions": ai_actions,
                    }
                    collection.insert_one(entry)
                    st.success("✅ Feedback submitted successfully!")
                    st.info(f"**Our Response:**\n\n{ai_response}")
                    if rating >= 4:
                        st.balloons()

    st.caption("Your feedback helps us improve. Thank you!")

if __name__ == "__main__":
    main()