import logging
import os
from app.services.youtube_api import YouTubeAPIService
from app.data.storage import init_db, save_channel_info, save_videos

logging.basicConfig(level=logging.INFO)

def read_channels_from_file(file_path="channels.txt"):
    """Read channel identifiers from a text file, one per line."""
    if not os.path.exists(file_path):
        logging.error(f"Channels file not found: {file_path}")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        channels = [line.strip() for line in f.readlines() if line.strip()]
    
    logging.info(f"Loaded {len(channels)} channels from {file_path}")
    return channels

def update_channels_data():
    """Update data for all channels in the channels.txt file."""
    init_db()
    yt = YouTubeAPIService()
    channels_to_fetch = read_channels_from_file()
    
    if not channels_to_fetch:
        logging.warning("No channels to fetch. Please add channels to channels.txt")
        return
    
    for identifier in channels_to_fetch:
        logging.info(f"Fetching data for channel: {identifier}")
        ch_info = yt.get_channel_info(identifier)
        if not ch_info:
            logging.warning(f"Could not fetch info for channel {identifier}")
            continue
        save_channel_info(ch_info)

        vids = yt.get_channel_videos(identifier, max_results=200)
        if vids:
            save_videos(ch_info["id"], vids)
            logging.info(f"Saved {len(vids)} videos for channel {identifier}")
        else:
            logging.warning(f"No videos fetched for channel {identifier}")

    logging.info("Data update completed.")

if __name__ == "__main__":
    update_channels_data()
