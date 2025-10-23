"""
File monitoring service using watchdog
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import structlog

from .event_handlers import DocumentEventHandler

logger = structlog.get_logger()


class LegalDocumentHandler(FileSystemEventHandler):
    """Handler for legal document file system events"""

    def __init__(self, file_monitor):
        self.file_monitor = file_monitor
        self.logger = structlog.get_logger().bind(component="file_handler")

    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self.logger.info("File created", path=event.src_path)
            asyncio.create_task(self.file_monitor.queue_event(event.src_path, "created"))

    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            self.logger.info("File modified", path=event.src_path)
            asyncio.create_task(self.file_monitor.queue_event(event.src_path, "modified"))

    def on_moved(self, event):
        """Handle file move events"""
        if not event.is_directory:
            self.logger.info("File moved", src_path=event.src_path, dest_path=event.dest_path)
            asyncio.create_task(self.file_monitor.queue_event(event.dest_path, "moved"))

    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory:
            self.logger.info("File deleted", path=event.src_path)
            asyncio.create_task(self.file_monitor.queue_event(event.src_path, "deleted"))


class DocumentFileMonitor:
    """Main document file monitoring service"""

    def __init__(self):
        self.observers: Dict[str, Observer] = {}
        self.event_queue = asyncio.Queue()
        self.event_handler = DocumentEventHandler(self)
        self.is_monitoring = False
        self.processed_count = 0
        self.last_processed = None
        self.logger = structlog.get_logger().bind(component="file_monitor")

        # Default watched folders (can be configured via environment)
        self.watched_folders = [
            os.getenv("WATCH_FOLDER_1", "D:/Download Legalitas"),
            os.getenv("WATCH_FOLDER_2", "D:/Documents/Legal/Queue")
        ]

        # Supported document extensions
        self.supported_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.ppt', '.pptx', '.jpg', '.jpeg', '.png',
            '.tiff', '.bmp', '.rtf', '.txt'
        }

    async def start(self):
        """Start file monitoring"""
        if self.is_monitoring:
            self.logger.warning("File monitoring already started")
            return

        self.logger.info("Starting file monitoring", folders=self.watched_folders)

        for folder_path in self.watched_folders:
            if os.path.exists(folder_path):
                await self._start_watching_folder(folder_path)
            else:
                self.logger.warning("Watch folder does not exist", folder=folder_path)

        self.is_monitoring = True
        self.logger.info("File monitoring started successfully")

    async def stop(self):
        """Stop file monitoring"""
        if not self.is_monitoring:
            self.logger.warning("File monitoring not running")
            return

        self.logger.info("Stopping file monitoring")

        for observer in self.observers.values():
            observer.stop()
            observer.join()

        self.observers.clear()
        self.is_monitoring = False
        self.logger.info("File monitoring stopped")

    async def _start_watching_folder(self, folder_path: str):
        """Start watching a specific folder"""
        try:
            observer = Observer()
            observer.schedule(self.event_handler, folder_path, recursive=True)
            observer.start()
            self.observers[folder_path] = observer
            self.logger.info("Started watching folder", folder=folder_path)
        except Exception as e:
            self.logger.error("Failed to start watching folder", folder=folder_path, error=str(e))

    async def queue_event(self, file_path: str, event_type: str):
        """Queue a file event for processing"""
        # Filter for supported document types
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_extensions:
            self.logger.debug("Skipping unsupported file type", file_path=file_path, extension=file_ext)
            return

        # Create event data
        event_data = {
            "file_path": file_path,
            "event_type": event_type,
            "file_size": 0,
            "timestamp": time.time()
        }

        # Get file size if file exists
        try:
            if os.path.exists(file_path):
                event_data["file_size"] = os.path.getsize(file_path)
        except Exception as e:
            self.logger.warning("Failed to get file size", file_path=file_path, error=str(e))

        # Add to processing queue
        await self.event_queue.put(event_data)
        self.logger.info("Queued file event", file_path=file_path, event_type=event_type)

    async def process_queued_events(self):
        """Process events from the queue"""
        self.logger.info("Starting event processing")

        while self.is_monitoring or not self.event_queue.empty():
            try:
                # Wait for events with timeout
                event_data = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._process_event(event_data)
            except asyncio.TimeoutError:
                # No events to process, continue loop
                continue
            except Exception as e:
                self.logger.error("Error processing event", error=str(e))

        self.logger.info("Event processing stopped")

    async def _process_event(self, event_data: Dict[str, Any]):
        """Process a single file event"""
        try:
            file_path = event_data["file_path"]
            event_type = event_data["event_type"]

            self.logger.info("Processing file event", file_path=file_path, event_type=event_type)

            # Skip deleted files
            if event_type == "deleted":
                self.logger.info("Skipping deleted file", file_path=file_path)
                return

            # Wait for file to be fully written (especially for large files)
            await self._wait_for_file_ready(file_path)

            # Process the document
            event_handler = DocumentEventHandler(self)
            result = await event_handler.process_document(file_path, event_type)

            if result:
                self.processed_count += 1
                self.last_processed = file_path
                self.logger.info("Document processed successfully",
                               file_path=file_path, result=result)
            else:
                self.logger.warning("Document processing failed", file_path=file_path)

        except Exception as e:
            self.logger.error("Failed to process event",
                            file_path=event_data.get("file_path"),
                            error=str(e))

    async def _wait_for_file_ready(self, file_path: str, timeout: int = 30):
        """Wait for file to be fully written and accessible"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check if file exists and is not being written to
                if os.path.exists(file_path):
                    # Try to open file in read mode to check if it's accessible
                    with open(file_path, 'rb') as f:
                        # Check file size stability (wait for size to stop changing)
                        size1 = os.path.getsize(file_path)
                        await asyncio.sleep(1)
                        size2 = os.path.getsize(file_path)

                        if size1 == size2:
                            return True

                await asyncio.sleep(1)
            except (IOError, OSError, PermissionError):
                # File is being written to or is locked
                await asyncio.sleep(1)
                continue

        # If we get here, the file wasn't ready within timeout
        self.logger.warning("File not ready within timeout", file_path=file_path, timeout=timeout)
        return False

    async def handle_manual_processing(self, event_data):
        """Handle manually triggered document processing"""
        file_path = event_data.file_path
        event_type = event_data.event_type

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        event_handler = DocumentEventHandler(self)
        result = await event_handler.process_document(file_path, event_type)

        if result:
            self.processed_count += 1
            self.last_processed = file_path

        return result

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "is_active": self.is_monitoring,
            "watched_folders": list(self.observers.keys()),
            "total_documents_processed": self.processed_count,
            "last_processed_document": self.last_processed
        }