import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="📊",
    layout="wide"
)

# File path for data storage
DATA_FILE = "feedback_data.json"

# Load data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

# Convert data to DataFrame
def get_dataframe():
    data = load_data()
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    return df

# Main app
def main():
    st.title("📊 Admin Dashboard")
    st.write("Monitor and analyze customer feedback in real-time")
    
    # Auto-refresh every 30 seconds
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    # Add auto-refresh info
    st.caption("Dashboard updates automatically. Click refresh for manual update.")
    
    # Load data
    df = get_dataframe()
    
    if df.empty:
        st.info("📭 No feedback submissions yet. Waiting for customer reviews...")
        return
    
    # Key Metrics
    st.header("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Submissions", len(df))
    
    with col2:
        avg_rating = df['rating'].mean()
        st.metric("Average Rating", f"{avg_rating:.2f} ⭐")
    
    with col3:
        positive_feedback = len(df[df['rating'] >= 4])
        positive_pct = (positive_feedback / len(df)) * 100
        st.metric("Positive Feedback", f"{positive_pct:.1f}%")
    
    with col4:
        negative_feedback = len(df[df['rating'] <= 2])
        st.metric("Negative Feedback", negative_feedback, 
                 delta=f"{negative_feedback} need attention", 
                 delta_color="inverse")
    
    st.markdown("---")
    
    # Visualizations
    st.header("📊 Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Rating Distribution
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
        # Feedback Over Time
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
    
    # Sentiment Gauge
    col1, col2, col3 = st.columns(3)
    
    with col2:
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
    
    # Filters
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
    
    # Apply filters
    filtered_df = df[df['rating'].isin(filter_rating)]
    
    # Apply sorting
    if sort_by == "Newest First":
        filtered_df = filtered_df.sort_values('timestamp', ascending=False)
    elif sort_by == "Oldest First":
        filtered_df = filtered_df.sort_values('timestamp', ascending=True)
    elif sort_by == "Highest Rating":
        filtered_df = filtered_df.sort_values('rating', ascending=False)
    elif sort_by == "Lowest Rating":
        filtered_df = filtered_df.sort_values('rating', ascending=True)
    
    st.write(f"Showing {len(filtered_df)} of {len(df)} submissions")
    
    # Display submissions
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
                
                # Rating indicator
                stars = "⭐" * row['rating']
                st.markdown(f"### {stars}")
                
                # Sentiment badge
                if row['rating'] >= 4:
                    st.success("😊 Positive")
                elif row['rating'] == 3:
                    st.warning("😐 Neutral")
                else:
                    st.error("😞 Negative")
    
    st.markdown("---")
    
    # Export data
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
        json_data = filtered_df.to_json(orient='records', indent=2)
        st.download_button(
            label="📥 Download as JSON",
            data=json_data,
            file_name=f"feedback_data_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()