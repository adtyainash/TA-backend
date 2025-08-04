#!/usr/bin/env python3
"""
Weekly Aggregation Scheduler

This script schedules the weekly aggregation to run automatically at the end of each week.
It uses APScheduler to run the aggregation every Sunday at 23:59.

Usage:
    python scheduler.py start    # Start the scheduler
    python scheduler.py stop     # Stop the scheduler
    python scheduler.py status   # Check scheduler status
"""

import sys
import logging
import signal
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from weekly_aggregator import process_weekly_aggregation, get_current_yearweek

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def weekly_aggregation_job():
    """Job function to run weekly aggregation"""
    try:
        logger.info("Starting scheduled weekly aggregation job")
        current_week = get_current_yearweek()
        logger.info(f"Processing week: {current_week}")
        
        # Process the current week
        process_weekly_aggregation(target_yearweek=current_week)
        
        logger.info("Weekly aggregation job completed successfully")
    except Exception as e:
        logger.error(f"Error in weekly aggregation job: {str(e)}")

def start_scheduler():
    """Start the scheduler"""
    global scheduler
    
    if scheduler and scheduler.running:
        logger.info("Scheduler is already running")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule job to run every Sunday at 23:59 (end of week)
    # This ensures we capture all data for the week
    scheduler.add_job(
        func=weekly_aggregation_job,
        trigger=CronTrigger(day_of_week='sun', hour=23, minute=59),
        id='weekly_aggregation',
        name='Weekly Case Aggregation',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started. Weekly aggregation will run every Sunday at 23:59")
    
    # Print next run time
    job = scheduler.get_job('weekly_aggregation')
    if job:
        logger.info(f"Next run scheduled for: {job.next_run_time}")

def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    else:
        logger.info("Scheduler is not running")

def get_scheduler_status():
    """Get scheduler status"""
    global scheduler
    
    if not scheduler:
        logger.info("Scheduler is not initialized")
        return
    
    if scheduler.running:
        logger.info("Scheduler is running")
        job = scheduler.get_job('weekly_aggregation')
        if job:
            logger.info(f"Next run scheduled for: {job.next_run_time}")
            logger.info(f"Job enabled: {job.next_run_time is not None}")
    else:
        logger.info("Scheduler is not running")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}. Shutting down scheduler...")
    stop_scheduler()
    sys.exit(0)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scheduler.py [start|stop|status]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if command == 'start':
        start_scheduler()
        try:
            # Keep the script running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Shutting down...")
            stop_scheduler()
    
    elif command == 'stop':
        stop_scheduler()
    
    elif command == 'status':
        get_scheduler_status()
    
    else:
        print("Invalid command. Use: start, stop, or status")
        sys.exit(1)

if __name__ == "__main__":
    main() 