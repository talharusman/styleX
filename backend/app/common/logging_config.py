"""
Structured Logging Configuration

Configures logging with structured format for debugging and monitoring.
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter for production"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in ["name", "msg", "args", "created", "filename", 
                             "funcName", "levelname", "levelno", "lineno",
                             "module", "msecs", "pathname", "process",
                             "processName", "relativeCreated", "stack_info",
                             "thread", "threadName", "exc_info", "exc_text",
                             "message", "taskName"]:
                    log_data[key] = value
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for development"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[1;31m" # Bold Red
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    structured: bool = False
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom format string (optional)
        log_file: Path to log file (optional)
        structured: Use structured JSON logging (for production)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Default format
    default_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    format_string = log_format or default_format
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter(format_string))
    
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logging.info("Logging configured", extra={"log_level": log_level})


class RequestLogger:
    """Middleware for logging HTTP requests"""
    
    def __init__(self):
        self.logger = logging.getLogger("stylex.requests")
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Log HTTP request details"""
        self.logger.info(
            f"{method} {path} - {status_code}",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
                "user_id": user_id
            }
        )
