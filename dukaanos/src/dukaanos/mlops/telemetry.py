"""Production Telemetry, Structured JSON Logging, and Observability."""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional


class JSONFormatter(logging.Formatter):
    """Formats log records as structured, machine-parsable JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": "dukaanos-retail-ai",
            "module": record.module,
            "message": record.getMessage(),
        }

        # Include custom metadata if passed
        if hasattr(record, "metadata") and isinstance(record.metadata, dict):
            log_entry.update(record.metadata)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def get_production_logger(name: str = "dukaanos.prod") -> logging.Logger:
    """Configures a standardized structured JSON logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


class TelemetryMetrics:
    """In-memory telemetry counters and latency monitors for retail operations."""

    def __init__(self):
        self.counters: Dict[str, int] = {
            "sales_transactions_processed": 0,
            "purchase_orders_created": 0,
            "ai_agent_tool_invocations": 0,
            "drift_checks_performed": 0,
        }
        self.latencies: Dict[str, list[float]] = {
            "forecasting_inference_ms": [],
            "checkout_processing_ms": [],
        }

    def increment(self, counter_name: str, delta: int = 1):
        """Increments a business or operational metric counter."""
        if counter_name in self.counters:
            self.counters[counter_name] += delta

    def record_latency(self, metric_name: str, duration_ms: float):
        """Records latency timing in milliseconds."""
        if metric_name in self.latencies:
            self.latencies[metric_name].append(round(duration_ms, 2))
            # Keep last 1,000 observations to bound memory
            if len(self.latencies[metric_name]) > 1000:
                self.latencies[metric_name].pop(0)

    def get_summary(self) -> Dict[str, Any]:
        """Returns snapshot summary of production operational metrics."""
        summary = {"counters": self.counters.copy(), "latencies_avg_ms": {}}
        for k, v in self.latencies.items():
            summary["latencies_avg_ms"][k] = round(sum(v) / len(v), 2) if v else 0.0
        return summary


telemetry = TelemetryMetrics()
prod_logger = get_production_logger()

