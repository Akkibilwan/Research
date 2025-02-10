import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
# API Key
API_KEY = "AIzaSyDxxBiK_1nHKYRUgb-FS_EcPNa_tTOmI6Q"
def get_search_suggestions(query):
    """Get search suggestions for the given query."""
    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=5,
            regionCode="US"
        )
        response = request.execute()
        suggestions = []
        for item in response["items"]:
            suggestions.append(item["snippet"]["title"])
        return suggestions
    except Exception as e:
        return []
def get_channel_info(channel_id):
    """Get channel details."""
    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        response = request.execute()
        if response["items"]:
            channel_data = response["items"][0]
            return {
                "title": channel_data["snippet"]["title"],
                "subscribers": channel_data["statistics"].get("subscriberCount", "N/A"),
                "total_views": channel_data["statistics"].get("viewCount", "N/A"),
                "thumbnail": channel_data["snippet"]["thumbnails"]["default"]["url"]
            }
        return None
    except Exception as e:
        return None
def calculate_outlier_score(views, likes, comments, publish_date):
    """Calculate an outlier score (1-100) based on video metrics and recency."""
    try:
        views = int(views) if views != 'N/A' else 0
        likes = int(likes) if likes != 'N/A' else 0
        comments = int(comments) if comments != 'N/A' else 0
        publish_datetime = datetime.strptime(publish_date, "%Y-%m-%dT%H:%M:%SZ")
        age_days = (datetime.now() - publish_datetime).days + 1
        engagement_rate = ((likes + comments) / views) if views > 0 else 0
        views_per_day = views / age_days
        normalized_views = min(views_per_day / 10000, 1)
        normalized_engagement = min(engagement_rate * 100, 1)
        combined_score = (normalized_views * 0.7) + (normalized_engagement * 0.3)
        outlier_score = round(combined_score * 100)
        return max(1, min(100, outlier_score))
    except Exception as e:
        return 1
def youtube_search(query, max_results=10):
    """Enhanced YouTube search with video and channel metrics."""
    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results,
            order="viewCount"
        )
        response = request.execute()
        results = []
        for item in response["items"]:
            video_id = item["id"]["videoId"]
            channel_id = item["snippet"]["channelId"]
            # Get detailed video statistics
            video_request = youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            )
            video_response = video_request.execute()
            if video_response["items"]:
                video_data = video_response["items"][0]
                statistics = video_data["statistics"]
                publish_date = video_data["snippet"]["publishedAt"]
                # Get channel info
                channel_info = get_channel_info(channel_id)
                views = statistics.get("viewCount", "N/A")
                likes = statistics.get("likeCount", "N/A")
                comments = statistics.get("commentCount", "N/A")
                outlier_score = calculate_outlier_score(views, likes, comments, publish_date)
                results.append({
                    "video_id": video_id,
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "publish_date": publish_date,
                    "outlier_score": outlier_score,
                    "channel": channel_info,
                    "video_url": f"https://www.youtube.com/watch?v={video_id}",
                    "channel_url": f"https://www.youtube.com/channel/{channel_id}"
                })
        results.sort(key=lambda x: int(x["views"]) if x["views"] != "N/A" else 0, reverse=True)
        return results
    except Exception as e:
        st.error(f"Error in YouTube search: {str(e)}")
        return []
def format_number(num):
    """Format large numbers to K/M/B format."""
    try:
        num = int(num)
        if num >= 1000000000:
            return f"{num/1000000000:.1f}B"
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        if num >= 1000:
            return f"{num/1000:.1f}K"
        return str(num)
    except:
        return "N/A"
def main():
    """Enhanced main function with search suggestions and channel info."""
    st.set_page_config(page_title="YouTube Research Tool", layout="wide")
    st.title("YouTube Topic Research & Analytics Tool")
    st.markdown("---")
    # Search interface with suggestions
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_term = st.text_input("Enter a search term:", "machine learning")
        if search_term:
            suggestions = get_search_suggestions(search_term)
            if suggestions:
                selected_suggestion = st.selectbox("Related searches:", ["Current search"] + suggestions)
                if selected_suggestion != "Current search":
                    search_term = selected_suggestion
    with col2:
        num_results = st.slider("Number of results:", 5, 20, 10)
    with col3:
        sort_by = st.selectbox("Sort by:", ["Views", "Outlier Score"])
    if st.button("Search", type="primary"):
        with st.spinner("Searching YouTube..."):
            results = youtube_search(search_term, num_results)
        if results:
            if sort_by == "Outlier Score":
                results.sort(key=lambda x: x["outlier_score"], reverse=True)
            # Top performer section
            top_video = results[0]
            st.markdown("### :trophy: Top Performing Video")
            with st.container():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(top_video["thumbnail"])
                with col2:
                    st.markdown(f"**[{top_video['title']}]({top_video['video_url']})**")
                    if top_video["channel"]:
                        st.markdown(f"**Channel:** [{top_video['channel']['title']}]({top_video['channel_url']}) "
                                  f"({format_number(top_video['channel']['subscribers'])} subscribers)")
                    metrics_col1, metrics_col2 = st.columns(2)
                    with metrics_col1:
                        st.metric("Views", format_number(top_video['views']))
                    with metrics_col2:
                        st.metric("Outlier Score", top_video["outlier_score"])
            st.markdown("### All Results")
            for result in results:
                with st.container():
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.image(result["thumbnail"])
                    with col2:
                        st.markdown(f"**[{result['title']}]({result['video_url']})**")
                        if result["channel"]:
                            st.markdown(f"**Channel:** [{result['channel']['title']}]({result['channel_url']}) "
                                      f"({format_number(result['channel']['subscribers'])} subscribers)")
                        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                        with metrics_col1:
                            st.metric("Views", format_number(result['views']))
                        with metrics_col2:
                            st.metric("Likes", format_number(result['likes']))
                        with metrics_col3:
                            st.metric("Comments", format_number(result['comments']))
                        with metrics_col4:
                            st.metric("Outlier Score", result["outlier_score"])
                        publish_date = datetime.strptime(result["publish_date"], "%Y-%m-%dT%H:%M:%SZ")
                        st.write(f"Published: {publish_date.strftime('%B %d, %Y')}")
                        st.markdown(f"[Watch on YouTube]({result['video_url']})")
                st.markdown("---")
        else:
            st.warning("No results found. Try a different search term.")
if __name__ == "__main__":
    main()
