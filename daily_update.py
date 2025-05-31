import logging
import datetime
import traceback
import os
from main import update_channels_data


script_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_dir, "update_logs.txt")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler()
    ],
    force=True
)

def main():
    start_time = datetime.datetime.now()
    logging.info(f"Starting daily update at {start_time}")
    
    try:
        update_channels_data()
        logging.info("Daily update completed successfully.")
    except Exception as e:
        logging.error(f"Error during daily update: {e}")
        logging.error(traceback.format_exc())
    
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    logging.info(f"Update process finished at {end_time} (Duration: {duration})")
    
    # Ensure all logs are written to file
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'flush'):
            handler.flush()

if __name__ == "__main__":
    main()
