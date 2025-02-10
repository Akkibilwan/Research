import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime
import os
import pandas as pd
import numpy as np

# Load API Key from environment variable
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    st.error("API Key is missing. Please set the API_KEY environment variable.")
    st.stop()

def get_search_suggestions(query):
    """Fetch YouTube search suggestions."""
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
        return [item["snippet"]["title"] for item in response["items"]]
    except Exception:
        return []

def get_channel_info(channel_id):
    """Fetch channel details from YouTube API."""
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
    except Exception:
        return None

def youtube_search(query, max_results=10):
    """Fetch YouTube search results with video and channel metrics."""
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
            channel_info = get_channel_info(channel_id)
            results.append({
                "video_id": video_id,
                "title": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                "channel": channel_info,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "channel_url": f"https://www.youtube.com/channel/{channel_id}"
            })
        return results
    except Exception as e:
        st.error(f"Error in YouTube search: {str(e)}")
        return []

def main():
    """Streamlit app for YouTube topic research."""
    st.set_page_config(page_title="YouTube Research Tool", layout="wide")
    st.title("YouTube Topic Research & Analytics Tool")
    st.markdown("---")
    
    search_term = st.text_input("Enter a search term:", "machine learning")
    num_results = st.slider("Number of results:", 5, 20, 10)
    
    if st.button("Search", type="primary"):
        with st.spinner("Searching YouTube..."):
            results = youtube_search(search_term, num_results)
        
        if results:
            st.markdown("### Search Results")
            for result in results:
                st.image(result["thumbnail"])
                st.markdown(f"**[{result['title']}]({result['video_url']})**")
                if result["channel"]:
                    st.markdown(f"**Channel:** [{result['channel']['title']}]({result['channel_url']})")
    
if __name__ == "__main__":
    main()
