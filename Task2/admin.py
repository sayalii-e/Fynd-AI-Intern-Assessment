import streamlit as st
import os
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from bson import ObjectId

st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="📊",
    layout="wide"
)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "fynd"  
COLLECTION_NAME = "user_feedback"    


def get_mongo_client():
    """Get MongoDB client with proper error handling"""
    try:
        mongodb_uri = st.secrets.get("MONGODB_URI") or os.getenv("MONGODB_URI")
    except:
        mongodb_uri = os.getenv("MONGODB_URI")
    
    if not mongodb_uri:
        st.error("⚠️ MONGODB_URI not found. Please set it in your environment variables or Streamlit secrets.")
        st.stop()
    
    return MongoClient(mongodb_uri)

def get_database():
    """Get MongoDB database connection"""
    client = get_mongo_client()
    return client[DB_NAME]

def get_feedback_collection():
    """Get feedback collection using the defined COLLECTION_NAME"""
    db = get_database()
    return db[COLLECTION_NAME]

def load_data():
    """Load all feedback from MongoDB"""
    collection = get_feedback_collection()
    return list(collection.find())

def get_dataframe():
    """Convert feedback data to pandas DataFrame"""
    data = load_data()
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
    return df

def main():
    st.title("📊 Admin Dashboard")
    st.write("Monitor and analyze customer feedback in real-time")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    st.caption("Dashboard updates automatically. Click refresh for manual update.")
    
    df = get_dataframe()
    
    if df.empty:
        st.info("📭 No feedback submissions yet. Waiting for customer reviews...")
        return
    
    st.header("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Submissions", len(df))
    
    with col2:
        avg_rating = df['rating'].mean()
        st.metric("Average Rating", f"{avg_rating:.2f} ⭐")
    
    with col3:
        positive_feedback = len(df[df['rating'] >= 4])
        positive_pct = (positive_feedback / len(df)) * 100 if len(df) > 0 else 0
        st.metric("Positive Feedback", f"{positive_pct:.1f}%")
    
    with col4:
        negative_feedback = len(df[df['rating'] <= 2])
        st.metric("Negative Feedback", negative_feedback, 
                 delta=f"{negative_feedback} need attention", 
                 delta_color="inverse")
    
    st.markdown("---")
    
    st.header("📊 Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        rating_counts = df['rating'].value_counts().sort_index()
        fig_ratings = px.bar(
            x=rating_counts.index,
            y=rating_counts.values,
            labels={'x': 'Rating (Stars)', 'y': 'Count'},
            title='Rating Distribution',
            color=rating_counts.index,
            color_continuous_scale='RdYlGn'
        )
        fig_ratings.update_layout(showlegend=False)
        st.plotly_chart(fig_ratings, use_container_width=True)
    
    with col2:
        feedback_by_date = df.groupby('date').size().reset_index(name='count')
        fig_timeline = px.line(
            feedback_by_date,
            x='date',
            y='count',
            title='Feedback Submissions Over Time',
            markers=True
        )
        fig_timeline.update_layout(
            xaxis_title='Date',
            yaxis_title='Number of Submissions'
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col2:
        avg_rating = df['rating'].mean()
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_rating,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Satisfaction"},
            gauge={
                'axis': {'range': [0, 5]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 2], 'color': "lightcoral"},
                    {'range': [2, 3.5], 'color': "lightyellow"},
                    {'range': [3.5, 5], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 4
                }
            }
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    st.markdown("---")
    
    st.header("🔍 Feedback Submissions")
    
    col1, col2 = st.columns(2)
    with col1:
        filter_rating = st.multiselect(
            "Filter by Rating",
            options=[1, 2, 3, 4, 5],
            default=[1, 2, 3, 4, 5]
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            options=["Newest First", "Oldest First", "Highest Rating", "Lowest Rating"]
        )
    
    filtered_df = df[df['rating'].isin(filter_rating)]
    
    if sort_by == "Newest First":
        filtered_df = filtered_df.sort_values('timestamp', ascending=False)
    elif sort_by == "Oldest First":
        filtered_df = filtered_df.sort_values('timestamp', ascending=True)
    elif sort_by == "Highest Rating":
        filtered_df = filtered_df.sort_values('rating', ascending=False)
    elif sort_by == "Lowest Rating":
        filtered_df = filtered_df.sort_values('rating', ascending=True)
    
    st.write(f"Showing {len(filtered_df)} of {len(df)} submissions")
    
    for idx, row in filtered_df.iterrows():
        with st.expander(
            f"⭐ {row['rating']} stars - {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
            expanded=False
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📝 Customer Review")
                st.write(row['review'])
                
                st.subheader("🤖 AI Summary")
                st.info(row['ai_summary'])
                
                st.subheader("💬 AI Response")
                st.success(row['ai_response'])
            
            with col2:
                st.subheader("✅ Recommended Actions")
                st.warning(row['ai_actions'])
                
                stars = "⭐" * row['rating']
                st.markdown(f"### {stars}")
                
                if row['rating'] >= 4:
                    st.success("😊 Positive")
                elif row['rating'] == 3:
                    st.warning("😐 Neutral")
                else:
                    st.error("😞 Negative")
    
    st.markdown("---")
    
    st.header("💾 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"feedback_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        json_data = filtered_df.to_json(orient='records', indent=2, default_handler=str)
        st.download_button(
            label="📥 Download as JSON",
            data=json_data,
            file_name=f"feedback_data_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()