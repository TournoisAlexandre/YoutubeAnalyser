import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from dataclasses import dataclass
from typing import Optional

load_dotenv()


API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("YOUTUBE API KEY not found in .env")

@dataclass
class Config:

    YOUTUBE_API_SERVICE_NAME: str = 'youtube'
    YOUTUBE_API_VERSION: str = 'v3'
    YOUTUBE_API_KEY: str = os.getenv('YOUTUBE_API_KEY')
    
    DATABASE_PATH: str = 'data/youtube.db'
    
    GOLD_THRESHOLD: float = 0.8  # Top 20%
    BRONZE_THRESHOLD: float = 0.2  # Bottom 20%
    
    MAX_VIDEOS_PER_REQUEST: int = 50
    MAX_TOTAL_VIDEOS: int = 500
    
    def __post_init__(self):
        if not self.YOUTUBE_API_KEY:
            raise ValueError("YOUTUBE_API_KEY not found in .env file")

# Instance globale
config = Config()