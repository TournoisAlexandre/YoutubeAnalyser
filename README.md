# YoutubeAnalyser

A tool for YouTube content creators that helps analyze the content of other YouTube channels.

## Features

- Automatic retrieval of YouTube channel data (channel information and videos)
- Storage of data in a local SQLite database
- Interactive dashboard to visualize and analyze data
- Detailed statistical analysis of videos (engagement, views, likes, comments)
- Ability to add personal analysis for each video
- Automatic daily data updates

## Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file at the root of the project with your YouTube API key:
   ```
   YOUTUBE_API_KEY=your_youtube_api_key
   ```
4. Create a `channels.txt` file with the list of channels to analyze (one per line)
5. Run `python main.py` to retrieve the data
6. Launch the dashboard with `streamlit run main_app.py`

## Configuration

- `channels.txt`: List of YouTube channels to monitor (one per line)
- `config.py`: General application configuration
- `AUTOMATION_SETUP.md`: Instructions for setting up automated updates

## Automation

To configure automated daily updates, see the [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) file.

## Project Structure

- `app/`: Main source code
  - `data/`: Database management
  - `services/`: Services (YouTube API)
- `data/`: Data (SQLite database)
- `main.py`: Data retrieval script
- `main_app.py`: Streamlit application (dashboard)
- `daily_update.py`: Script for automated updates
- `channels.txt`: List of channels to monitor
