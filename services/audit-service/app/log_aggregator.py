"""
Log Aggregator
Aggregates logs from multiple services and provides search capabilities
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime, timedelta
from elasticsearch import AsyncElasticsearch
import pandas as pd
import io

from .models import (
    LogSearchRequest,
    LogSearchResponse,
    ExportRequest,
    ExportResponse,
    ExportFormat
)


class LogAggregator:
    """Service for aggregating and searching logs"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="LogAggregator")
        self.elasticsearch_client = None
        self.index_patterns = {
            "audit_events": "audit-events-*",
            "security_events": "security-events-*",
            "business_events": "business-events-*",
            "performance_events": "performance-events-*",
            "application_logs": "app-logs-*"
        }

    async def initialize(self):
        """Initialize the log aggregator"""
        self.logger.info("Initializing Log Aggregator")

        try:
            # Initialize Elasticsearch connection
            es_host = "http://localhost:9200"  # Would get from config
            self.elasticsearch_client = AsyncElasticsearch([es_host])

            # Test connection
            if await self.elasticsearch_client.ping():
                self.logger.info("Elasticsearch connection successful")
            else:
                raise Exception("Failed to connect to Elasticsearch")

            # Create index templates if needed
            await self._setup_index_templates()

            self.logger.info("Log Aggregator initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize Log Aggregator", error=str(e))
            raise

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Log Aggregator")
        if self.elasticsearch_client:
            await self.elasticsearch_client.close()

    async def search_logs(self, request: LogSearchRequest) -> LogSearchResponse:
        """Search logs across all indices"""
        try:
            start_time = asyncio.get_event_loop().time()

            # Build Elasticsearch query
            es_query = await self._build_search_query(request)

            # Determine which indices to search
            indices = await self._get_search_indices(request.event_type)

            # Execute search
            response = await self.elasticsearch_client.search(
                index=indices,
                body=es_query,
                size=request.limit,
                _source=True
            )

            # Process results
            hits = response.get('hits', {}).get('hits', [])
            events = [hit['_source'] for hit in hits]

            # Add event IDs and format timestamps
            for i, event in enumerate(events):
                if '_id' not in event:
                    event['_id'] = hits[i]['_id']
                if 'timestamp' in event and isinstance(event['timestamp'], str):
                    event['timestamp'] = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))

            search_time = (asyncio.get_event_loop().time() - start_time) * 1000
            total_count = response.get('hits', {}).get('total', {}).get('value', 0)
            has_more = request.limit < total_count

            return LogSearchResponse(
                success=True,
                query=request.query,
                total_count=total_count,
                events=events,
                search_time_ms=search_time,
                has_more=has_more
            )

        except Exception as e:
            self.logger.error("Log search failed", error=str(e))
            raise

    async def export_logs(self, request: ExportRequest) -> ExportResponse:
        """Export logs in specified format"""
        try:
            export_id = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{asyncio.current_task().get_name()}"
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(hours=24)

            self.logger.info("Starting log export",
                           export_id=export_id,
                           format=request.format.value,
                           query=request.query)

            # Get all matching logs
            all_logs = []
            from_i = 0
            size = 1000

            while True:
                # Search with pagination
                es_query = await self._build_search_query_from_audit_query(request.query)
                indices = await self._get_search_indices()

                response = await self.elasticsearch_client.search(
                    index=indices,
                    body=es_query,
                    size=size,
                    from_=from_i,
                    _source=True
                )

                hits = response.get('hits', {}).get('hits', [])
                if not hits:
                    break

                batch_events = [hit['_source'] for hit in hits]
                all_logs.extend(batch_events)

                from_i += size

                # Safety check to prevent infinite loops
                if len(batch_events) < size:
                    break

            # Convert to requested format
            content, filename, media_type = await self._convert_logs_to_format(
                all_logs, request.format, request.export_name
            )

            # Store export data (in production, would store in object storage)
            export_data = {
                'content': content,
                'filename': filename,
                'media_type': media_type,
                'created_at': created_at,
                'expires_at': expires_at
            }

            # Cache export data temporarily
            if not hasattr(self, '_export_cache'):
                self._export_cache = {}
            self._export_cache[export_id] = export_data

            return ExportResponse(
                export_id=export_id,
                query=request.query,
                format=request.format,
                status="completed",
                created_at=created_at,
                expires_at=expires_at,
                file_size_bytes=len(content),
                record_count=len(all_logs)
            )

        except Exception as e:
            self.logger.error("Log export failed", error=str(e))
            raise

    async def get_export_file(self, export_id: str) -> Optional[Dict[str, Any]]:
        """Get exported file data"""
        try:
            if not hasattr(self, '_export_cache'):
                return None

            export_data = self._export_cache.get(export_id)
            if not export_data:
                return None

            # Check if expired
            if datetime.utcnow() > export_data['expires_at']:
                del self._export_cache[export_id]
                return None

            return export_data

        except Exception as e:
            self.logger.error("Failed to get export file", export_id=export_id, error=str(e))
            return None

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        try:
            # Get last 24 hours of performance events
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)

            es_query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"event_category": "performance"}},
                            {"range": {"timestamp": {"gte": start_time.isoformat(), "lte": end_time.isoformat()}}}
                        ]
                    }
                },
                "aggs": {
                    "avg_response_time": {
                        "avg": {"field": "duration_ms"}
                    },
                    "requests_per_minute": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": "1m"
                        }
                    },
                    "error_rate": {
                        "avg": {"field": "error_rate_percent"}
                    },
                    "avg_cpu": {
                        "avg": {"field": "cpu_usage_percent"}
                    },
                    "avg_memory": {
                        "avg": {"field": "memory_usage_mb"}
                    },
                    "slow_endpoints": {
                        "terms": {
                            "field": "service_name.keyword",
                            "size": 10,
                            "order": {"avg_duration": "desc"}
                        },
                        "aggs": {
                            "avg_duration": {
                                "avg": {"field": "duration_ms"}
                            }
                        }
                    }
                }
            }

            response = await self.elasticsearch_client.search(
                index=self.index_patterns["performance_events"],
                body=es_query,
                size=0
            )

            aggs = response.get('aggregations', {})

            summary = {
                "average_response_time_ms": aggs.get("avg_response_time", {}).get("value", 0),
                "requests_per_minute": self._calculate_rpm_from_buckets(aggs.get("requests_per_minute", {}).get("buckets", [])),
                "error_rate_percent": aggs.get("error_rate", {}).get("value", 0),
                "cpu_usage_percent": aggs.get("avg_cpu", {}).get("value", 0),
                "memory_usage_mb": aggs.get("avg_memory", {}).get("value", 0),
                "slowest_endpoints": [
                    {"endpoint": bucket["key"], "avg_duration_ms": bucket["avg_duration"]["value"]}
                    for bucket in aggs.get("slow_endpoints", {}).get("buckets", [])
                ],
                "performance_alerts": await self._get_performance_alerts(start_time, end_time)
            }

            return summary

        except Exception as e:
            self.logger.error("Failed to get performance summary", error=str(e))
            return {}

    async def _build_search_query(self, request: LogSearchRequest) -> Dict[str, Any]:
        """Build Elasticsearch search query"""
        query = {
            "query": {
                "bool": {
                    "must": []
                }
            },
            "sort": [
                {"timestamp": {"order": "desc"}}
            ]
        }

        # Add text search
        if request.query:
            query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": request.query,
                    "fields": ["description", "action", "event_type", "details"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })

        # Add time range
        if request.start_time or request.end_time:
            time_range = {}
            if request.start_time:
                time_range["gte"] = request.start_time.isoformat()
            if request.end_time:
                time_range["lte"] = request.end_time.isoformat()

            query["query"]["bool"]["must"].append({
                "range": {"timestamp": time_range}
            })

        # Add filters
        if request.user_id:
            query["query"]["bool"]["must"].append({
                "term": {"user_id": request.user_id}
            })

        if request.company_id:
            query["query"]["bool"]["must"].append({
                "term": {"company_id": request.company_id}
            })

        if request.event_type:
            query["query"]["bool"]["must"].append({
                "term": {"event_type": request.event_type}
            })

        # If no query terms, match all
        if not query["query"]["bool"]["must"]:
            query["query"] = {"match_all": {}}

        return query

    async def _build_search_query_from_audit_query(self, query) -> Dict[str, Any]:
        """Build search query from AuditQuery"""
        es_query = {
            "query": {
                "bool": {
                    "must": []
                }
            },
            "sort": [
                {"timestamp": {"order": "desc"}}
            ]
        }

        # Convert AuditQuery to ES query
        if query.user_id:
            es_query["query"]["bool"]["must"].append({"term": {"user_id": query.user_id}})

        if query.company_id:
            es_query["query"]["bool"]["must"].append({"term": {"company_id": query.company_id}})

        if query.event_type:
            es_query["query"]["bool"]["must"].append({"term": {"event_type": query.event_type.value}})

        if query.start_time or query.end_time:
            time_range = {}
            if query.start_time:
                time_range["gte"] = query.start_time.isoformat()
            if query.end_time:
                time_range["lte"] = query.end_time.isoformat()
            es_query["query"]["bool"]["must"].append({"range": {"timestamp": time_range}})

        if query.search_text:
            es_query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query.search_text,
                    "fields": ["description", "action", "details"],
                    "type": "best_fields"
                }
            })

        if not es_query["query"]["bool"]["must"]:
            es_query["query"] = {"match_all": {}}

        return es_query

    async def _get_search_indices(self, event_type: Optional[str] = None) -> str:
        """Get appropriate indices for search"""
        if event_type:
            # Map event types to index patterns
            type_mapping = {
                "audit": self.index_patterns["audit_events"],
                "security": self.index_patterns["security_events"],
                "business": self.index_patterns["business_events"],
                "performance": self.index_patterns["performance_events"]
            }
            return type_mapping.get(event_type, "*")
        else:
            # Search all relevant indices
            return ",".join(self.index_patterns.values())

    async def _convert_logs_to_format(
        self,
        logs: List[Dict[str, Any]],
        format: ExportFormat,
        export_name: Optional[str] = None
    ) -> tuple[bytes, str, str]:
        """Convert logs to requested export format"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = export_name or f"audit_logs_{timestamp}"

        if format == ExportFormat.JSON:
            content = json.dumps(logs, indent=2, default=str).encode('utf-8')
            filename = f"{base_name}.json"
            media_type = "application/json"

        elif format == ExportFormat.CSV:
            # Convert to DataFrame and then to CSV
            df = pd.json_normalize(logs)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            content = csv_buffer.getvalue().encode('utf-8')
            filename = f"{base_name}.csv"
            media_type = "text/csv"

        elif format == ExportFormat.XML:
            # Simple XML conversion
            xml_content = ['<?xml version="1.0" encoding="UTF-8"?>', '<logs>']
            for log in logs:
                xml_content.append('<log>')
                for key, value in log.items():
                    xml_content.append(f'<{key}>{str(value)}</{key}>')
                xml_content.append('</log>')
            xml_content.append('</logs>')

            content = '\n'.join(xml_content).encode('utf-8')
            filename = f"{base_name}.xml"
            media_type = "application/xml"

        elif format == ExportFormat.PDF:
            # Would generate actual PDF here
            # For now, return text content
            text_content = [f"Audit Log Export - {timestamp}"]
            text_content.append("=" * 50)
            for i, log in enumerate(logs, 1):
                text_content.append(f"\nLog {i}:")
                for key, value in log.items():
                    text_content.append(f"  {key}: {value}")

            content = '\n'.join(text_content).encode('utf-8')
            filename = f"{base_name}.txt"  # Using .txt as placeholder
            media_type = "text/plain"

        else:
            raise ValueError(f"Unsupported export format: {format}")

        return content, filename, media_type

    async def _setup_index_templates(self):
        """Setup Elasticsearch index templates"""
        try:
            # Define template for audit events
            audit_template = {
                "index_patterns": ["audit-events-*"],
                "template": {
                    "mappings": {
                        "properties": {
                            "timestamp": {"type": "date"},
                            "event_id": {"type": "keyword"},
                            "event_type": {"type": "keyword"},
                            "event_category": {"type": "keyword"},
                            "user_id": {"type": "integer"},
                            "company_id": {"type": "integer"},
                            "description": {"type": "text"},
                            "action": {"type": "keyword"},
                            "outcome": {"type": "keyword"},
                            "ip_address": {"type": "ip"},
                            "details": {"type": "object"}
                        }
                    }
                }
            }

            # Create template
            await self.elasticsearch_client.indices.put_index_template(
                name="audit-events-template",
                body=audit_template
            )

            self.logger.info("Index templates created successfully")

        except Exception as e:
            self.logger.error("Failed to setup index templates", error=str(e))

    def _calculate_rpm_from_buckets(self, buckets: List[Dict[str, Any]]) -> float:
        """Calculate requests per minute from histogram buckets"""
        if not buckets:
            return 0.0

        total_requests = sum(bucket.get("doc_count", 0) for bucket in buckets)
        return total_requests / len(buckets) if buckets else 0.0

    async def _get_performance_alerts(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get performance alerts for the time period"""
        try:
            # Search for performance events that indicate alerts
            es_query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"event_category": "performance"}},
                            {"term": {"alert": True}},
                            {"range": {"timestamp": {"gte": start_time.isoformat(), "lte": end_time.isoformat()}}}
                        ]
                    }
                },
                "sort": [
                    {"timestamp": {"order": "desc"}}
                ],
                "size": 10
            }

            response = await self.elasticsearch_client.search(
                index=self.index_patterns["performance_events"],
                body=es_query
            )

            hits = response.get('hits', {}).get('hits', [])
            alerts = [hit['_source'] for hit in hits]

            return alerts

        except Exception as e:
            self.logger.error("Failed to get performance alerts", error=str(e))
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get log aggregator statistics"""
        try:
            # Get index statistics
            stats = await self.elasticsearch_client.indices.stats(index="_all")
            indices_stats = stats.get('indices', {})

            total_docs = sum(index_stats.get('total', {}).get('docs', {}).get('count', 0) for index_stats in indices_stats.values())
            total_size = sum(index_stats.get('total', {}).get('store', {}).get('size_in_bytes', 0) for index_stats in indices_stats.values())

            return {
                "service": "log_aggregator",
                "status": "active",
                "total_documents": total_docs,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "indices_count": len(indices_stats),
                "cached_exports": len(getattr(self, '_export_cache', {})),
                "supported_formats": ["json", "csv", "xml", "pdf"]
            }

        except Exception as e:
            self.logger.error("Failed to get stats", error=str(e))
            return {
                "service": "log_aggregator",
                "status": "error",
                "error": str(e)
            }