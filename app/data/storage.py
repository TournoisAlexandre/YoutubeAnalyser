from sqlalchemy import (
    create_engine, Column, Boolean, String, Integer, BigInteger, DateTime, Text, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine("sqlite:///data/youtube.db", echo=False)
Session = sessionmaker(bind=engine)

class Channel(Base):
    __tablename__ = "channels"
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    subscribers = Column(BigInteger)
    video_count = Column(Integer)
    view_count = Column(BigInteger)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    videos = relationship("Video", back_populates="channel")
    
    # New history fields
    subscriber_history = Column(Text, nullable=True)  # JSON: [{"date": "2025-01-01", "count": 1000}, ...]
    view_count_history = Column(Text, nullable=True)  # JSON: [{"date": "2025-01-01", "count": 50000}, ...]

class Video(Base):
    __tablename__ = "videos"
    id = Column(String, primary_key=True)
    channel_id = Column(String, ForeignKey("channels.id"))
    title = Column(String)
    description = Column(Text)
    published_at = Column(DateTime)
    view_count = Column(BigInteger)
    like_count = Column(BigInteger)
    comment_count = Column(BigInteger)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    channel = relationship("Channel", back_populates="videos")
    hidden = Column(Boolean, nullable=False, default=False)
    analysis = Column(Text, nullable=True)
    
    # New history fields
    view_count_history = Column(Text, nullable=True)    # JSON: [{"date": "2025-01-01", "count": 1000}, ...]
    like_count_history = Column(Text, nullable=True)    # JSON: [{"date": "2025-01-01", "count": 50}, ...]
    comment_count_history = Column(Text, nullable=True) # JSON: [{"date": "2025-01-01", "count": 10}, ...]

def init_db():
    Base.metadata.create_all(engine)

# Helper functions for history management
def parse_history_json(history_str: Optional[str]) -> List[Dict]:
    """Parse history JSON string to list of dicts, return empty list if None or invalid"""
    if not history_str:
        return []
    try:
        return json.loads(history_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse history JSON: {e}")
        return []

def serialize_history_json(history_list: List[Dict]) -> str:
    """Serialize history list to JSON string"""
    return json.dumps(history_list)

def add_history_point(current_history_str: Optional[str], new_count: int, date_str: Optional[str] = None) -> str:
    """Add a new data point to history JSON"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    history = parse_history_json(current_history_str)
    
    # Check if we already have data for this date
    for point in history:
        if point.get("date") == date_str:
            # Update existing point
            point["count"] = new_count
            return serialize_history_json(history)
    
    # Add new point
    history.append({"date": date_str, "count": new_count})
    
    # Keep history sorted by date
    history.sort(key=lambda x: x["date"])
    
    return serialize_history_json(history)

def get_history_for_date_range(history_str: Optional[str], start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    """Get history points within a date range"""
    history = parse_history_json(history_str)
    
    if not start_date and not end_date:
        return history
    
    filtered = []
    for point in history:
        point_date = point.get("date")
        if not point_date:
            continue
            
        if start_date and point_date < start_date:
            continue
        if end_date and point_date > end_date:
            continue
            
        filtered.append(point)
    
    return filtered

def get_latest_history_point(history_str: Optional[str]) -> Optional[Dict]:
    """Get the most recent history point"""
    history = parse_history_json(history_str)
    if not history:
        return None
    
    # History should be sorted, but just in case
    return max(history, key=lambda x: x.get("date", ""))

def initialize_history_if_empty(current_value: int, current_history_str: Optional[str]) -> str:
    """Initialize history with current value if history is empty"""
    if current_history_str and parse_history_json(current_history_str):
        return current_history_str  # Already has history
    
    # Create initial history point with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    return serialize_history_json([{"date": today, "count": current_value}])

def save_channel_info(data: dict):
    sess = Session()
    try:
        ch = sess.query(Channel).get(data["id"]) or Channel(id=data["id"])
        ch.title = data["snippet"]["title"]
        ch.description = data["snippet"].get("description", "")
        stats = data["statistics"]
        
        # Update current values
        new_subscribers = int(stats.get("subscriberCount", 0))
        new_video_count = int(stats.get("videoCount", 0))
        new_view_count = int(stats.get("viewCount", 0))
        
        ch.subscribers = new_subscribers
        ch.video_count = new_video_count
        ch.view_count = new_view_count
        ch.fetched_at = datetime.utcnow()
        
        # Update history
        ch.subscriber_history = add_history_point(ch.subscriber_history, new_subscribers)
        ch.view_count_history = add_history_point(ch.view_count_history, new_view_count)
        
        sess.add(ch)
        sess.commit()
        logger.info(f"Channel {ch.title} updated with history")
        
    except Exception as e:
        sess.rollback()
        logger.error(f"Error saving channel info: {e}")
        raise
    finally:
        sess.close()

def save_videos(channel_id: str, videos: List[dict]):
    sess = Session()
    try:
        for v in videos:
            vid = sess.query(Video).get(v["id"]) or Video(id=v["id"])
            vid.channel_id = channel_id
            vid.title = v["snippet"]["title"]
            vid.description = v["snippet"].get("description", "")
            vid.published_at = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            
            stats = v["statistics"]
            
            # Update current values
            new_view_count = int(stats.get("viewCount", 0))
            new_like_count = int(stats.get("likeCount", 0))
            new_comment_count = int(stats.get("commentCount", 0))
            
            vid.view_count = new_view_count
            vid.like_count = new_like_count
            vid.comment_count = new_comment_count
            vid.fetched_at = datetime.utcnow()
            
            # Update history
            vid.view_count_history = add_history_point(vid.view_count_history, new_view_count)
            vid.like_count_history = add_history_point(vid.like_count_history, new_like_count)
            vid.comment_count_history = add_history_point(vid.comment_count_history, new_comment_count)
            
            sess.add(vid)
            
        sess.commit()
        logger.info(f"Saved {len(videos)} videos with history for channel {channel_id}")
        
    except Exception as e:
        sess.rollback()
        logger.error(f"Error saving videos: {e}")
        raise
    finally:
        sess.close()

def get_channel_subscriber_history(channel_id: str) -> List[Dict]:
    """Get subscriber history for a channel"""
    sess = Session()
    try:
        channel = sess.query(Channel).get(channel_id)
        if not channel:
            return []
        return parse_history_json(channel.subscriber_history)
    finally:
        sess.close()

def get_channel_view_history(channel_id: str) -> List[Dict]:
    """Get view count history for a channel"""
    sess = Session()
    try:
        channel = sess.query(Channel).get(channel_id)
        if not channel:
            return []
        return parse_history_json(channel.view_count_history)
    finally:
        sess.close()

def get_video_view_history(video_id: str) -> List[Dict]:
    """Get view count history for a video"""
    sess = Session()
    try:
        video = sess.query(Video).get(video_id)
        if not video:
            return []
        return parse_history_json(video.view_count_history)
    finally:
        sess.close()

def get_channel_video_publication_dates(channel_id: str) -> List[Dict]:
    """Get publication dates and titles of all videos for a channel (for timeline markers)"""
    sess = Session()
    try:
        videos = sess.query(Video).filter(
            Video.channel_id == channel_id,
            Video.hidden == False
        ).order_by(Video.published_at).all()
        
        return [
            {
                "date": video.published_at.strftime("%Y-%m-%d"),
                "title": video.title,
                "video_id": video.id
            }
            for video in videos
        ]
    finally:
        sess.close()

