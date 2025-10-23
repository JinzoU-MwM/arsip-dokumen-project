"""
Event handlers for document processing pipeline
"""

import os
import asyncio
import httpx
from pathlib import Path
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class DocumentEventHandler:
    """Handles document events and triggers processing pipeline"""

    def __init__(self, file_monitor):
        self.file_monitor = file_monitor
        self.logger = structlog.get_logger().bind(component="event_handler")

        # Service URLs (configure via environment variables)
        self.ai_processor_url = os.getenv("AI_PROCESSOR_URL", "http://localhost:8002")
        self.validation_url = os.getenv("VALIDATION_URL", "http://localhost:8003")
        self.drive_service_url = os.getenv("DRIVE_SERVICE_URL", "http://localhost:8004")
        self.notification_url = os.getenv("NOTIFICATION_URL", "http://localhost:8005")

        # HTTP client for service communication
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def process_document(self, file_path: str, event_type: str) -> Dict[str, Any]:
        """
        Process a document through the complete pipeline:
        File -> AI Processing -> Validation -> Drive Upload -> Notification
        """
        self.logger.info("Starting document processing",
                        file_path=file_path, event_type=event_type)

        try:
            # Step 1: Submit to AI Processing Service
            ai_result = await self._submit_to_ai_processor(file_path, event_type)
            if not ai_result or not ai_result.get("success"):
                raise Exception(f"AI processing failed: {ai_result.get('error', 'Unknown error')}")

            processing_id = ai_result.get("processing_id")
            self.logger.info("AI processing submitted", processing_id=processing_id)

            # Step 2: Wait for AI processing to complete and get results
            ai_results = await self._wait_for_ai_completion(processing_id)
            if not ai_results:
                raise Exception("AI processing timeout or failure")

            self.logger.info("AI processing completed",
                           classification=ai_results.get("classification"),
                           confidence=ai_results.get("confidence"))

            # Step 3: Submit to Validation Engine
            validation_result = await self._submit_to_validation(ai_results)
            if not validation_result.get("success"):
                self.logger.warning("Validation failed", errors=validation_result.get("errors", []))

            # Step 4: Upload to Google Drive
            drive_result = await self._upload_to_drive(file_path, ai_results)
            if not drive_result.get("success"):
                raise Exception(f"Drive upload failed: {drive_result.get('error')}")

            self.logger.info("Drive upload completed",
                           drive_url=drive_result.get("drive_url"),
                           folder_id=drive_result.get("folder_id"))

            # Step 5: Send notification
            notification_result = await self._send_notification(
                file_path, ai_results, validation_result, drive_result
            )

            # Compile final result
            final_result = {
                "success": True,
                "file_path": file_path,
                "processing_id": processing_id,
                "ai_results": ai_results,
                "validation_result": validation_result,
                "drive_result": drive_result,
                "notification_sent": notification_result.get("success", False),
                "timestamp": asyncio.get_event_loop().time()
            }

            self.logger.info("Document processing completed successfully",
                           file_path=file_path, processing_id=processing_id)

            return final_result

        except Exception as e:
            self.logger.error("Document processing failed",
                            file_path=file_path, error=str(e))

            # Send error notification
            await self._send_error_notification(file_path, str(e))

            return {
                "success": False,
                "file_path": file_path,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }

    async def _submit_to_ai_processor(self, file_path: str, event_type: str) -> Optional[Dict[str, Any]]:
        """Submit document to AI processing service"""
        try:
            payload = {
                "file_path": file_path,
                "event_type": event_type,
                "priority": "normal" if event_type != "manual" else "high"
            }

            response = await self.http_client.post(
                f"{self.ai_processor_url}/process-document",
                json=payload
            )

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error("AI processor request failed",
                                status_code=response.status_code,
                                response_text=response.text)
                return None

        except Exception as e:
            self.logger.error("Failed to submit to AI processor", error=str(e))
            return None

    async def _wait_for_ai_completion(self, processing_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """Wait for AI processing to complete"""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                response = await self.http_client.get(
                    f"{self.ai_processor_url}/processing-status/{processing_id}"
                )

                if response.status_code == 200:
                    status_data = response.json()

                    if status_data.get("status") == "completed":
                        return status_data.get("results")
                    elif status_data.get("status") == "failed":
                        self.logger.error("AI processing failed",
                                        processing_id=processing_id,
                                        error=status_data.get("error"))
                        return None
                    else:
                        # Still processing, wait and retry
                        await asyncio.sleep(5)
                else:
                    self.logger.error("Failed to check AI processing status",
                                    processing_id=processing_id,
                                    status_code=response.status_code)
                    await asyncio.sleep(5)

            except Exception as e:
                self.logger.error("Error checking AI processing status",
                                processing_id=processing_id, error=str(e))
                await asyncio.sleep(5)

        self.logger.error("AI processing timeout", processing_id=processing_id)
        return None

    async def _submit_to_validation(self, ai_results: Dict[str, Any]) -> Dict[str, Any]:
        """Submit AI results to validation engine"""
        try:
            payload = {
                "ai_results": ai_results,
                "validation_type": "completeness"
            }

            response = await self.http_client.post(
                f"{self.validation_url}/validate",
                json=payload
            )

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error("Validation request failed",
                                status_code=response.status_code,
                                response_text=response.text)
                return {"success": False, "errors": ["Validation service unavailable"]}

        except Exception as e:
            self.logger.error("Failed to submit to validation", error=str(e))
            return {"success": False, "errors": [str(e)]}

    async def _upload_to_drive(self, file_path: str, ai_results: Dict[str, Any]) -> Dict[str, Any]:
        """Upload document to Google Drive"""
        try:
            payload = {
                "file_path": file_path,
                "document_type": ai_results.get("classification", "unknown"),
                "company_info": ai_results.get("extracted_entities", {}).get("company", {}),
                "metadata": {
                    "processing_id": ai_results.get("processing_id"),
                    "confidence": ai_results.get("confidence"),
                    "classification": ai_results.get("classification")
                }
            }

            response = await self.http_client.post(
                f"{self.drive_service_url}/upload-document",
                json=payload
            )

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error("Drive upload failed",
                                status_code=response.status_code,
                                response_text=response.text)
                return {"success": False, "error": "Drive service unavailable"}

        except Exception as e:
            self.logger.error("Failed to upload to drive", error=str(e))
            return {"success": False, "error": str(e)}

    async def _send_notification(self, file_path: str, ai_results: Dict[str, Any],
                                validation_result: Dict[str, Any], drive_result: Dict[str, Any]) -> Dict[str, Any]:
        """Send success notification"""
        try:
            # Extract company name from AI results
            company_name = "Unknown Company"
            extracted_entities = ai_results.get("extracted_entities", {})
            if "company" in extracted_entities and "name" in extracted_entities["company"]:
                company_name = extracted_entities["company"]["name"]

            payload = {
                "notification_type": "processing_complete",
                "company_name": company_name,
                "document_path": file_path,
                "document_type": ai_results.get("classification", "unknown"),
                "confidence": ai_results.get("confidence", 0),
                "drive_url": drive_result.get("drive_url"),
                "validation_status": "passed" if validation_result.get("success") else "failed",
                "missing_documents": validation_result.get("missing_documents", []),
                "processing_time": ai_results.get("processing_time", 0)
            }

            response = await self.http_client.post(
                f"{self.notification_url}/send-notification",
                json=payload
            )

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error("Notification failed",
                                status_code=response.status_code,
                                response_text=response.text)
                return {"success": False}

        except Exception as e:
            self.logger.error("Failed to send notification", error=str(e))
            return {"success": False}

    async def _send_error_notification(self, file_path: str, error_message: str) -> None:
        """Send error notification"""
        try:
            payload = {
                "notification_type": "processing_error",
                "document_path": file_path,
                "error_message": error_message,
                "timestamp": asyncio.get_event_loop().time()
            }

            # Fire and forget for error notifications
            asyncio.create_task(
                self.http_client.post(
                    f"{self.notification_url}/send-notification",
                    json=payload
                )
            )

        except Exception as e:
            self.logger.error("Failed to send error notification", error=str(e))

    async def cleanup(self):
        """Cleanup resources"""
        if self.http_client:
            await self.http_client.aclose()