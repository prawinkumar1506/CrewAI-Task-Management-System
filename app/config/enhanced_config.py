"""
Enhanced Configuration Management System
Features:
- Environment variable support
- Configuration validation
- Performance tuning
- Multiple environment support
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pydantic import BaseSettings, Field, validator
import json
from pathlib import Path

class DatabaseConfig(BaseSettings):
    """Database configuration settings"""
    mongodb_conn_str: str = Field(
        default="mongodb+srv://prawin2310095:zmbzpjc186ub3WAS@taskmgmt.ad7exfr.mongodb.net/taskmgmt?retryWrites=true&w=majority",
        env="MONGODB_CONN_STR"
    )
    db_name: str = Field(default="taskmgmt", env="DB_NAME")
    max_connections: int = Field(default=100, env="DB_MAX_CONNECTIONS")
    connection_timeout: int = Field(default=30, env="DB_CONNECTION_TIMEOUT")
    
    class Config:
        env_prefix = "DB_"

class CacheConfig(BaseSettings):
    """Cache configuration settings"""
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    default_ttl: int = Field(default=300, env="CACHE_DEFAULT_TTL")
    max_memory: str = Field(default="256mb", env="CACHE_MAX_MEMORY")
    enable_clustering: bool = Field(default=False, env="CACHE_CLUSTERING")
    
    class Config:
        env_prefix = "CACHE_"

class LLMConfig(BaseSettings):
    """LLM configuration settings"""
    primary_model: str = Field(default="gemini/gemini-1.5-flash", env="LLM_PRIMARY_MODEL")
    fallback_model: str = Field(default="gpt-3.5-turbo", env="LLM_FALLBACK_MODEL")
    api_key: str = Field(default="AIzaSyDREOvD_AgBvzs9SyvTJyV77ruHswMT74s", env="LLM_API_KEY")
    temperature: float = Field(default=0.3, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=2048, env="LLM_MAX_TOKENS")
    request_timeout: int = Field(default=30, env="LLM_REQUEST_TIMEOUT")
    rate_limit_per_minute: int = Field(default=60, env="LLM_RATE_LIMIT")
    
    class Config:
        env_prefix = "LLM_"

class AsyncConfig(BaseSettings):
    """Async processing configuration"""
    enable_async: bool = Field(default=True, env="ENABLE_ASYNC")
    max_workers: int = Field(default=4, env="ASYNC_MAX_WORKERS")
    max_process_workers: int = Field(default=2, env="ASYNC_MAX_PROCESS_WORKERS")
    task_timeout: int = Field(default=300, env="ASYNC_TASK_TIMEOUT")
    enable_priority_queue: bool = Field(default=True, env="ASYNC_PRIORITY_QUEUE")
    
    class Config:
        env_prefix = "ASYNC_"

class MonitoringConfig(BaseSettings):
    """Monitoring and metrics configuration"""
    enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
    health_check_interval: int = Field(default=60, env="HEALTH_CHECK_INTERVAL")
    performance_monitoring: bool = Field(default=True, env="PERFORMANCE_MONITORING")
    metrics_export_port: int = Field(default=8000, env="METRICS_EXPORT_PORT")
    enable_prometheus: bool = Field(default=False, env="ENABLE_PROMETHEUS")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    class Config:
        env_prefix = "MONITORING_"

class SecurityConfig(BaseSettings):
    """Security configuration settings"""
    enable_authentication: bool = Field(default=False, env="ENABLE_AUTHENTICATION")
    jwt_secret_key: str = Field(default="your-secret-key", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    max_requests_per_minute: int = Field(default=100, env="MAX_REQUESTS_PER_MINUTE")
    
    class Config:
        env_prefix = "SECURITY_"

class PerformanceConfig(BaseSettings):
    """Performance tuning configuration"""
    enable_connection_pooling: bool = Field(default=True, env="ENABLE_CONNECTION_POOLING")
    connection_pool_size: int = Field(default=10, env="CONNECTION_POOL_SIZE")
    enable_query_optimization: bool = Field(default=True, env="ENABLE_QUERY_OPTIMIZATION")
    batch_size: int = Field(default=100, env="BATCH_SIZE")
    enable_compression: bool = Field(default=True, env="ENABLE_COMPRESSION")
    memory_limit_mb: int = Field(default=512, env="MEMORY_LIMIT_MB")
    
    class Config:
        env_prefix = "PERFORMANCE_"

class EnhancedConfig(BaseSettings):
    """Main configuration class that combines all settings"""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    cache: CacheConfig = CacheConfig()
    llm: LLMConfig = LLMConfig()
    async_config: AsyncConfig = AsyncConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    security: SecurityConfig = SecurityConfig()
    performance: PerformanceConfig = PerformanceConfig()
    
    # Feature flags
    enable_rag: bool = Field(default=True, env="ENABLE_RAG")
    enable_automation: bool = Field(default=True, env="ENABLE_AUTOMATION")
    enable_background_tasks: bool = Field(default=True, env="ENABLE_BACKGROUND_TASKS")
    
    # File paths
    config_file: Optional[str] = Field(default=None, env="CONFIG_FILE")
    log_file: str = Field(default="logs/task_manager.log", env="LOG_FILE")
    data_dir: str = Field(default="data", env="DATA_DIR")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_config_file()
        self._validate_config()
    
    def _load_config_file(self):
        """Load configuration from file if specified"""
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                
                # Update settings from file
                for key, value in file_config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                    elif hasattr(self.database, key):
                        setattr(self.database, key, value)
                    elif hasattr(self.cache, key):
                        setattr(self.cache, key, value)
                    # Add more component checks as needed
                        
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
    
    def _validate_config(self):
        """Validate configuration settings"""
        # Validate database connection
        if not self.database.mongodb_conn_str:
            raise ValueError("MongoDB connection string is required")
        
        # Validate LLM settings
        if not self.llm.api_key:
            raise ValueError("LLM API key is required")
        
        # Validate cache settings
        if self.cache.enable_caching and not self.cache.redis_url:
            raise ValueError("Redis URL is required when caching is enabled")
    
    def get_database_url(self) -> str:
        """Get formatted database URL"""
        return self.database.mongodb_conn_str
    
    def get_cache_url(self) -> str:
        """Get formatted cache URL"""
        return self.cache.redis_url
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": self.monitoring.log_level,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": self.log_file,
            "max_bytes": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5
        }
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-related settings"""
        return {
            "connection_pooling": self.performance.enable_connection_pooling,
            "pool_size": self.performance.connection_pool_size,
            "query_optimization": self.performance.enable_query_optimization,
            "batch_size": self.performance.batch_size,
            "compression": self.performance.enable_compression,
            "memory_limit": self.performance.memory_limit_mb
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "database": self.database.dict(),
            "cache": self.cache.dict(),
            "llm": self.llm.dict(),
            "async_config": self.async_config.dict(),
            "monitoring": self.monitoring.dict(),
            "security": self.security.dict(),
            "performance": self.performance.dict(),
            "features": {
                "rag": self.enable_rag,
                "automation": self.enable_automation,
                "background_tasks": self.enable_background_tasks
            }
        }
    
    def save_to_file(self, filepath: str):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'EnhancedConfig':
        """Create configuration from file"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            config_data = json.load(f)
        
        return cls(**config_data)

# Global configuration instance
config = EnhancedConfig()

# Convenience functions
def get_config() -> EnhancedConfig:
    """Get global configuration instance"""
    return config

def reload_config():
    """Reload configuration from environment and files"""
    global config
    config = EnhancedConfig()

def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return config.database

def get_cache_config() -> CacheConfig:
    """Get cache configuration"""
    return config.cache

def get_llm_config() -> LLMConfig:
    """Get LLM configuration"""
    return config.llm

def get_monitoring_config() -> MonitoringConfig:
    """Get monitoring configuration"""
    return config.monitoring 