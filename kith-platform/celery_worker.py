#!/usr/bin/env python3
"""
Celery Worker for Kith Platform
Run this script to start a Celery worker process
"""

import os
from app.celery_app import celery_app

if __name__ == '__main__':
    # Start the Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=default,ai_processing,telegram_sync'
    ])
