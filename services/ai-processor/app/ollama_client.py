"""
Ollama LLM client for local AI processing
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
import structlog
import httpx

logger = structlog.get_logger()


class OllamaClient:
    """Client for Ollama LLM API"""

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3:70b")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        self.client = None
        self.logger = structlog.get_logger().bind(component="ollama_client")

    async def initialize(self):
        """Initialize the Ollama client"""
        self.client = httpx.AsyncClient(timeout=self.timeout)

        # Test connection and model availability
        try:
            await self._test_connection()
            await self._check_model_availability()
            self.logger.info("Ollama client initialized successfully",
                           model=self.model_name,
                           url=self.base_url)
        except Exception as e:
            self.logger.error("Failed to initialize Ollama client", error=str(e))
            raise

    async def _test_connection(self):
        """Test connection to Ollama server"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise Exception(f"Ollama server returned status {response.status_code}")
        except Exception as e:
            raise Exception(f"Cannot connect to Ollama server at {self.base_url}: {str(e)}")

    async def _check_model_availability(self):
        """Check if the required model is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            models = response.json().get("models", [])

            model_names = [model["name"] for model in models]
            if self.model_name not in model_names:
                self.logger.warning("Model not found locally, attempting to pull",
                                   model=self.model_name)
                await self._pull_model()

        except Exception as e:
            self.logger.warning("Failed to check model availability", error=str(e))

    async def _pull_model(self):
        """Pull the required model"""
        try:
            self.logger.info("Pulling model", model=self.model_name)

            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": self.model_name}
            ) as response:
                async for line in response.aiter_lines():
                    try:
                        data = json.loads(line)
                        status = data.get("status", "")
                        if "downloading" in status.lower():
                            self.logger.info("Model download progress", status=status)
                    except json.JSONDecodeError:
                        continue

            self.logger.info("Model pull completed", model=self.model_name)

        except Exception as e:
            self.logger.error("Failed to pull model", model=self.model_name, error=str(e))
            raise

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from the LLM"""
        try:
            # Build request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            # Make request
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API returned status {response.status_code}: {response.text}")

            result = response.json()
            return result.get("response", "").strip()

        except Exception as e:
            self.logger.error("Failed to generate response", error=str(e))
            raise

    async def analyze_document(
        self,
        text_content: str,
        classification_result: Dict[str, Any],
        entities: Dict[str, Any],
        company_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze document using LLM"""
        try:
            # Prepare system prompt for legal document analysis
            system_prompt = """
            You are an expert legal document analyst specializing in Indonesian legal documents.
            Analyze the provided document and extract key information.
            Focus on compliance, completeness, and business implications.
            Provide analysis in JSON format with the following structure:
            {
                "document_summary": "Brief summary of the document",
                "key_insights": ["List of key insights"],
                "compliance_status": "compliant/non_compliant/partially_compliant",
                "missing_information": ["List of missing information"],
                "business_impact": "Description of business impact",
                "recommended_actions": ["List of recommended actions"],
                "confidence_score": 0.95
            }
            """

            # Build the prompt
            prompt = f"""
            Please analyze this legal document:

            DOCUMENT TEXT:
            {text_content[:3000]}  # Limit text to avoid context window issues

            CLASSIFICATION RESULTS:
            - Category: {classification_result.get('category', 'unknown')}
            - Confidence: {classification_result.get('confidence', 0)}

            EXTRACTED ENTITIES:
            {json.dumps(entities, indent=2, default=str)}

            COMPANY HINT: {company_hint or 'Not specified'}

            Please provide comprehensive analysis focusing on:
            1. Document completeness and compliance
            2. Missing required information
            3. Business impact assessment
            4. Recommended next steps
            """

            # Generate analysis
            analysis_text = await self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=2000
            )

            # Parse JSON response
            try:
                # Extract JSON from response (in case there's surrounding text)
                import re
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    analysis_json = json.loads(json_match.group())
                else:
                    # Fallback if JSON parsing fails
                    analysis_json = {
                        "document_summary": analysis_text[:500],
                        "key_insights": ["Analysis completed"],
                        "compliance_status": "requires_review",
                        "missing_information": [],
                        "business_impact": "Document processed",
                        "recommended_actions": ["Review document manually"],
                        "confidence_score": 0.7
                    }
            except json.JSONDecodeError:
                # Fallback for JSON parsing errors
                analysis_json = {
                    "document_summary": analysis_text[:500],
                    "key_insights": ["Analysis completed"],
                    "compliance_status": "requires_review",
                    "missing_information": [],
                    "business_impact": "Document processed",
                    "recommended_actions": ["Review document manually"],
                    "confidence_score": 0.7
                }

            # Add metadata
            analysis_json["model_used"] = self.model_name
            analysis_json["processing_timestamp"] = asyncio.get_event_loop().time()

            return analysis_json

        except Exception as e:
            self.logger.error("Document analysis failed", error=str(e))
            # Return fallback analysis
            return {
                "document_summary": f"Analysis failed: {str(e)}",
                "key_insights": ["Processing error occurred"],
                "compliance_status": "requires_manual_review",
                "missing_information": ["Unable to analyze automatically"],
                "business_impact": "Manual review required",
                "recommended_actions": ["Review document manually", "Check system logs"],
                "confidence_score": 0.0,
                "error": str(e)
            }

    async def extract_company_info(self, text_content: str) -> Dict[str, Any]:
        """Extract company information from document"""
        try:
            system_prompt = """
            You are a business information extraction expert.
            Extract company information from the provided text.
            Return results in JSON format:
            {
                "company_name": "Company name or null",
                "npwp": "Tax ID number or null",
                "company_type": "PT/CV/etc or null",
                "industry": "Industry sector or null",
                "address": "Address or null",
                "contact_info": "Contact information or null",
                "confidence": 0.95
            }
            """

            prompt = f"""
            Extract company information from this legal document:

            {text_content[:2000]}
            """

            result = await self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2
            )

            # Parse JSON response
            try:
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"company_name": None, "confidence": 0.0}
            except json.JSONDecodeError:
                return {"company_name": None, "confidence": 0.0}

        except Exception as e:
            self.logger.error("Company info extraction failed", error=str(e))
            return {"company_name": None, "confidence": 0.0, "error": str(e)}

    async def validate_document_completeness(
        self,
        text_content: str,
        document_type: str,
        required_elements: List[str]
    ) -> Dict[str, Any]:
        """Validate document completeness"""
        try:
            system_prompt = f"""
            You are a legal document validation expert.
            Validate if the document contains all required elements for a {document_type}.
            Required elements: {', '.join(required_elements)}

            Return results in JSON format:
            {{
                "is_complete": true/false,
                "missing_elements": ["list of missing elements"],
                "present_elements": ["list of present elements"],
                "validation_notes": "Additional notes about validation",
                "confidence": 0.95
            }}
            """

            prompt = f"""
            Validate completeness of this {document_type} document:

            {text_content[:2000]}

            Required elements: {', '.join(required_elements)}
            """

            result = await self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1  # Very low temperature for validation
            )

            # Parse JSON response
            try:
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"is_complete": False, "confidence": 0.0}
            except json.JSONDecodeError:
                return {"is_complete": False, "confidence": 0.0}

        except Exception as e:
            self.logger.error("Document validation failed", error=str(e))
            return {"is_complete": False, "confidence": 0.0, "error": str(e)}

    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()