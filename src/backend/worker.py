#!/usr/bin/env python
"""
Celery worker startup script
Run with: python -m app.worker or celery -A app.celery_app worker
"""

import os
import logging
from app.celery_app import celery_app

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("🚀 Starting Celery Worker...")
    logger.info(f"Broker: {celery_app.conf.broker_connection_retry_on_startup}")
    
    celery_app.start([
        "worker",
        "--loglevel=info",
        "--concurrency=4",
        "--queues=celery,draft_generation,message_processing,voice_synthesis,avatar_generation",
    ])
