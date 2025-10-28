"""
日志配置模块
提供统一的日志配置和管理
"""

import json
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

from app.core.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        
        return super().format(record)


def setup_logging() -> None:
    """设置应用日志配置"""
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 确定日志级别
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # 确定日志格式
    use_json_format = settings.LOG_FORMAT.upper() == "JSON"
    
    # 基础日志配置
    log_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": JSONFormatter,
            },
            "colored": {
                "()": ColoredFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "colored" if not use_json_format else "json",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed" if not use_json_format else "json",
                "filename": str(log_dir / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed" if not use_json_format else "json",
                "filename": str(log_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "chromadb": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sentence_transformers": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
    }
    
    # 应用日志配置
    logging.config.dictConfig(log_config)
    
    # 设置第三方库日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(f"app.{name}")


def log_request(request_id: str, method: str, url: str, status_code: int, duration: float) -> None:
    """记录请求日志"""
    logger = get_logger("requests")
    logger.info(
        f"Request {request_id}: {method} {url} - {status_code} - {duration:.3f}s",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "method": method,
                "url": str(url),
                "status_code": status_code,
                "duration": duration,
            }
        }
    )


def log_error(error: Exception, context: str = "") -> None:
    """记录错误日志"""
    logger = get_logger("errors")
    logger.error(
        f"Error in {context}: {str(error)}",
        exc_info=True,
        extra={
            "extra_fields": {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
            }
        }
    )


def log_performance(operation: str, duration: float, **kwargs) -> None:
    """记录性能日志"""
    logger = get_logger("performance")
    logger.info(
        f"Performance: {operation} took {duration:.3f}s",
        extra={
            "extra_fields": {
                "operation": operation,
                "duration": duration,
                **kwargs,
            }
        }
    )


# 初始化日志配置
setup_logging()
