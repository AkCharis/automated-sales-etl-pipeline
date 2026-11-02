import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler

# Import your logger setup and your main pipeline process
from src.automated_sales_etl_pipeline.utils.logger_config import setup_pipeline_logging
from main import run_pipeline

logger = logging.getLogger(__name__)

class NewFileHandler(FileSystemEventHandler):
    """Event handler for monitoring directory changes and triggering ETL executions.

    Extends Watchdog's `FileSystemEventHandler` to intercept file creation events. 
    Filters incoming files by extension (`.csv`, `.xlsx`) and dispatches valid 
    file events to the core `run_pipeline` orchestration routine.
    """

    def on_created(self, event: FileSystemEvent) -> None:
        """Handles file system creation events within the monitored folder.

        Args:
            event (FileSystemEvent): The event object containing path information 
                and event type flags passed by the Watchdog observer.
        """
        
        # Step 1: Pre-Filtering Directory & Extension Events
        # Ignore events fired for folder creation
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        
        # Filter for allowed tabular file extensions to ignore temp files or system noise
        if filepath.suffix.lower() in ['.csv', '.xlsx']:
            logger.info(f"📥 New valid file detected: {filepath.name}")
            
            # Step 2: Triggering Pipeline Processing
            try:
                logger.info(f"⚙️ Triggering ETL pipeline execution for {filepath.name}...")
                
                # Execute single-file ETL run (Extract -> Validate -> Transform -> Load)
                run_pipeline(file_path=filepath) 
                
                logger.info("✅ Pipeline execution completed successfully.")
            except Exception as e:
                # Log execution failure and full trace without interrupting the observer thread
                logger.error(f"❌ Pipeline failed while processing {filepath.name}")
                logger.exception(e)


def start_monitoring(target_directory: str = 'data/inbox') -> None:
    """Initializes and runs the continuous directory monitoring service.

    Sets up the logging environment, verifies directory structures, attaches 
    the `NewFileHandler` listener to a Watchdog `Observer`, and maintains 
    a polling loop until manually interrupted (e.g., via Ctrl+C).

    Args:
        target_directory (str, optional): Target folder path to watch for incoming files. 
            Defaults to 'data/inbox'.
    """
    # Step 1: System & Directory Initialization
    # Initialize multi-channel pipeline logging
    setup_pipeline_logging()
    
    # Ensure target inbox directory exists on disk
    watch_path = Path(target_directory)
    watch_path.mkdir(parents=True, exist_ok=True)
    
    # Step 2: Watchdog Observer Setup & Start
    event_handler = NewFileHandler()
    observer = Observer()
    
    # Schedule event listener (non-recursive to watch immediate directory only)
    observer.schedule(event_handler, path=str(watch_path), recursive=False)
    
    logger.info(f"👀 Watchdog active. Monitoring directory: '{watch_path.resolve()}'")
    observer.start()
    
    # Step 3: Main Thread Polling Loop & Termination Handling
    # Keep the main process thread active while Watchdog runs in background threads
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.warning("🛑 Stopping watchdog monitor service...")
        observer.stop()
        
    # Block until background observer threads complete clean shutdown
    observer.join()


if __name__ == '__main__':
    start_monitoring()
