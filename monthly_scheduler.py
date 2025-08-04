#!/usr/bin/env python3
"""
Monthly Scheduler for Weekly Aggregation and Model Training

This script schedules:
1. Weekly aggregation (every Sunday at 23:59)
2. Monthly model retraining and forecasting (last day of month at 23:00)

Usage:
    python monthly_scheduler.py start    # Start the scheduler
    python monthly_scheduler.py stop     # Stop the scheduler
    python monthly_scheduler.py status   # Check scheduler status
"""

import sys
import logging
import signal
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from weekly_aggregator import process_weekly_aggregation, get_current_yearweek
from model_trainer import ModelTrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monthly_scheduler.log'),
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

def monthly_model_training_job():
    """Job function to run monthly model training and forecasting"""
    try:
        logger.info("Starting scheduled monthly model training job")
        
        # Initialize model trainer
        trainer = ModelTrainer()
        
        # Train models and make predictions for all ICD10 codes
        trainer.train_and_predict_all(forecast_steps=4)
        
        logger.info("Monthly model training job completed successfully")
    except Exception as e:
        logger.error(f"Error in monthly model training job: {str(e)}")

def start_scheduler():
    """Start the scheduler"""
    global scheduler
    
    if scheduler and scheduler.running:
        logger.info("Scheduler is already running")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule weekly aggregation job (every Sunday at 23:59)
    scheduler.add_job(
        func=weekly_aggregation_job,
        trigger=CronTrigger(day_of_week='sun', hour=23, minute=59),
        id='weekly_aggregation',
        name='Weekly Case Aggregation',
        replace_existing=True
    )
    
    # Schedule monthly model training job (last day of month at 23:00)
    scheduler.add_job(
        func=monthly_model_training_job,
        trigger=CronTrigger(day='last', hour=23, minute=0),
        id='monthly_model_training',
        name='Monthly Model Training and Forecasting',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Monthly scheduler started successfully!")
    logger.info("  - Weekly aggregation: Every Sunday at 23:59")
    logger.info("  - Monthly model training: Last day of month at 23:00")
    
    # Print next run times
    weekly_job = scheduler.get_job('weekly_aggregation')
    monthly_job = scheduler.get_job('monthly_model_training')
    
    if weekly_job:
        logger.info(f"Next weekly aggregation: {weekly_job.next_run_time}")
    if monthly_job:
        logger.info(f"Next monthly model training: {monthly_job.next_run_time}")

def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Monthly scheduler stopped")
    else:
        logger.info("Scheduler is not running")

def get_scheduler_status():
    """Get scheduler status"""
    global scheduler
    
    if not scheduler:
        logger.info("Scheduler is not initialized")
        return
    
    if scheduler.running:
        logger.info("Monthly scheduler is running")
        
        weekly_job = scheduler.get_job('weekly_aggregation')
        monthly_job = scheduler.get_job('monthly_model_training')
        
        if weekly_job:
            logger.info(f"Weekly aggregation - Next run: {weekly_job.next_run_time}")
            logger.info(f"Weekly aggregation - Enabled: {weekly_job.next_run_time is not None}")
        
        if monthly_job:
            logger.info(f"Monthly model training - Next run: {monthly_job.next_run_time}")
            logger.info(f"Monthly model training - Enabled: {monthly_job.next_run_time is not None}")
    else:
        logger.info("Scheduler is not running")

def manual_weekly_aggregation():
    """Manually trigger weekly aggregation"""
    try:
        logger.info("Manually triggering weekly aggregation...")
        weekly_aggregation_job()
        logger.info("Manual weekly aggregation completed")
    except Exception as e:
        logger.error(f"Error in manual weekly aggregation: {str(e)}")

def manual_model_training():
    """Manually trigger model training"""
    try:
        logger.info("Manually triggering model training...")
        monthly_model_training_job()
        logger.info("Manual model training completed")
    except Exception as e:
        logger.error(f"Error in manual model training: {str(e)}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}. Shutting down scheduler...")
    stop_scheduler()
    sys.exit(0)

def main():
    if len(sys.argv) < 2:
        print("Usage: python monthly_scheduler.py [start|stop|status|weekly|train]")
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
    
    elif command == 'weekly':
        manual_weekly_aggregation()
    
    elif command == 'train':
        manual_model_training()
    
    else:
        print("Invalid command. Use: start, stop, status, weekly, or train")
        sys.exit(1)

if __name__ == "__main__":
    main() 