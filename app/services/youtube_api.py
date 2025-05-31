from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import config
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class YouTubeAPIService:
    def __init__(self):
        self.service = self.get_youtube_service()

    def get_youtube_service(self):
        try :
            return build(
                config.YOUTUBE_API_SERVICE_NAME,
                config.YOUTUBE_API_VERSION,
                developerKey=config.YOUTUBE_API_KEY,
            )
        except Exception as e:
            logger.error(f"Error when creating youtube service : {e}")
            raise

    def resolve_channel_identifier(self, channel_identifier: str) -> Optional[str]:

        try:
            if channel_identifier.startswith('UC'):
                return channel_identifier

            if channel_identifier.startswith("@"):
                handle = channel_identifier[1:]
                try:
                    handle_response = self.service.channels().list(
                        part="id",
                        forHandle=handle  # new in API 2022
                    ).execute()

                    if handle_response['items']:
                        return handle_response['items'][0]['id']
                    
                except Exception as handle_exc:
                    logger.warning(f"Handle lookup failed: {handle_exc}")

            try:
                channels_response = self.service.channels().list(
                    part="id",
                    forUsername=channel_identifier
                ).execute()
                if channels_response['items']:
                    return channels_response['items'][0]['id']
            except Exception as username_exc:
                logger.warning(f"Username lookup failed: {username_exc}")

            # Last resort: search for channel by name (caution: high quota usage!)
            try:
                search_response = self.service.search().list(
                    part="snippet",
                    q=channel_identifier,
                    type="channel",
                    maxResults=1
                ).execute()
                if search_response['items']:
                    return search_response['items'][0]['snippet']['channelId']
            except Exception as search_exc:
                logger.warning(f"Channel search lookup failed: {search_exc}")

            # Nothing found
            return None

        except HttpError as e:
            logger.error(f"Error when resolving channel identifier: {e}")
            return None

        

    def get_channel_info(self, channel_identifier: str) -> Optional[Dict]:
        try:
            channel_id = self.resolve_channel_identifier(channel_identifier)
            if not channel_id:
                logger.error(f"Cannot find channel ID for identfier : {channel_identifier}")
                return None
            
            logger.info(f"Channel ID resolved: {channel_id}")



            channel_response = self.service.channels().list(
                part="snippet,statistics",
                id=channel_id
            ).execute()
            
            if channel_response['items']:
                channel_info = channel_response['items'][0]
                logger.info(f"Channel found: {channel_info['snippet']['title']}")
                return channel_info
            
            return None
            
        except HttpError as e:
            logger.error(f"Youtube API error for channel {channel_id}: {e}")
            return None
        
        except Exception as e:
            logger.error("Unexpected Error")
            return None
        
    def get_channel_videos(self, channel_identifier: str, max_results: int = None) -> List[Dict]:
        if max_results is None:
            max_results = config.MAX_TOTAL_VIDEOS

        channel_id = self.resolve_channel_identifier(channel_identifier)
        if not channel_id:
            logger.error(f"Cannot find channel ID for identifier: {channel_identifier}")
            return []

        # --- New method: playlist uploads ---
        uploads_playlist_id = 'UU' + channel_id[2:]

        videos = []
        next_page_token = None

        try:
            while len(videos) < max_results:
                playlist_request = self.service.playlistItems().list(
                    part="contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),  # 50 max per page
                    pageToken=next_page_token,
                )
                playlist_response = playlist_request.execute()

                if not playlist_response['items']:
                    break

                # Get the videoIds
                video_ids = [item['contentDetails']['videoId'] for item in playlist_response['items']]
                video_details = self.get_video_details(video_ids)
                videos.extend(video_details)
                logger.info(f"Retrieved {len(videos)} until now...")

                # Pagination
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break

        except HttpError as e:
            logger.error(f"Error while requesting videos: {e}")

        logger.info(f"Retrieved videos in total: {len(videos)}")
        return videos

    
    def get_video_details(self, video_ids: List[str]) -> List[dict]:
        results = []
        try:
            # Process in batches of 50 (max allowed by the API)
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                request = self.service.videos().list(
                    part="snippet,statistics",
                    id=','.join(batch_ids)
                )
                response = request.execute()
                results.extend(response.get('items', []))

        except HttpError as e:
            logger.error(f"Error while requesting video details: {e}")
            
        return results
