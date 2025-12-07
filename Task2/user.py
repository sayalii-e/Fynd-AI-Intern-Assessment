import streamlit as st
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Customer Feedback System",
    page_icon="⭐",
    layout="centered"
)

# Initialize Groq client
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("⚠️ GROQ_API_KEY not found. Please set it in your environment variables.")
        st.stop()
    return Groq(api_key=api_key)


# File path for data storage
DATA_FILE = "feedback_data.json"

# Load existing data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

# Save data
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Generate AI response using Groq
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

# Generate AI summary
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

# Generate recommended actions
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

# Main app
def main():
    st.title("⭐ Customer Feedback System")
    st.write("We value your opinion! Please share your experience with us.")
    
    # Create form
    with st.form("feedback_form", clear_on_submit=True):
        # Star rating
        st.subheader("How would you rate your experience?")
        rating = st.slider("Select rating", min_value=1, max_value=5, value=5, 
                          format="%d ⭐")
        
        # Review text
        st.subheader("Tell us more about your experience")
        review = st.text_area("Your review", placeholder="Share your thoughts...", 
                             height=150, max_chars=10000)
        
        # Submit button
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True)
        
        if submitted:
            if not review.strip():
                st.error("Please write a review before submitting.")
            else:
                with st.spinner("Processing your feedback..."):
                    # Generate AI responses
                    ai_response = generate_ai_response(rating, review)
                    ai_summary = generate_summary(review)
                    ai_actions = generate_actions(rating, review)
                    
                    # Create feedback entry
                    feedback_entry = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                        "timestamp": datetime.now().isoformat(),
                        "rating": rating,
                        "review": review,
                        "ai_response": ai_response,
                        "ai_summary": ai_summary,
                        "ai_actions": ai_actions
                    }
                    
                    # Load, append, and save data
                    data = load_data()
                    data.append(feedback_entry)
                    save_data(data)
                    
                    # Display success message
                    st.success("✅ Thank you for your feedback!")
                    
                    # Display AI response
                    st.info(f"**Our Response:**\n\n{ai_response}")
                    
                    # Show balloons for positive ratings
                    if rating >= 4:
                        st.balloons()

    # Footer
    st.markdown("---")
    st.caption("Your feedback helps us improve our service. Thank you!")

if __name__ == "__main__":
    main()