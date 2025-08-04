#!/usr/bin/env python3
"""
Weekly Case Aggregator Script

This script aggregates daily cases into weekly cases and can be run:
1. Manually for specific weeks
2. Automatically for all unprocessed weeks
3. As a scheduled job (weekly at end of week)

Usage:
    python weekly_aggregator.py                    # Process all unprocessed weeks
    python weekly_aggregator.py --week 202401      # Process specific week
    python weekly_aggregator.py --latest           # Process latest week only
"""

import argparse
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from db import SessionLocal
from crud import aggregate_daily_to_weekly, get_latest_yearweek, get_weekly_stats, generate_yearweek

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weekly_aggregator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def process_weekly_aggregation(target_yearweek: str = None, latest_only: bool = False):
    """
    Process weekly aggregation
    
    Args:
        target_yearweek: Specific yearweek to process (format: YYYYWW)
        latest_only: If True, only process the latest week
    """
    db = SessionLocal()
    try:
        if latest_only:
            latest_week = get_latest_yearweek(db)
            if latest_week:
                logger.info(f"Processing latest week: {latest_week}")
                aggregate_daily_to_weekly(db, latest_week)
                logger.info(f"Successfully processed week: {latest_week}")
            else:
                logger.warning("No data found in daily_case table")
        elif target_yearweek:
            logger.info(f"Processing specific week: {target_yearweek}")
            aggregate_daily_to_weekly(db, target_yearweek)
            logger.info(f"Successfully processed week: {target_yearweek}")
        else:
            logger.info("Processing all unprocessed weeks")
            aggregate_daily_to_weekly(db)
            logger.info("Successfully processed all unprocessed weeks")
            
    except Exception as e:
        logger.error(f"Error during weekly aggregation: {str(e)}")
        raise
    finally:
        db.close()

def get_current_yearweek() -> str:
    """Get the current yearweek"""
    today = date.today()
    return generate_yearweek(today)

def main():
    parser = argparse.ArgumentParser(description='Weekly Case Aggregator')
    parser.add_argument('--week', type=str, help='Specific yearweek to process (format: YYYYWW)')
    parser.add_argument('--latest', action='store_true', help='Process only the latest week')
    parser.add_argument('--current', action='store_true', help='Process current week')
    
    args = parser.parse_args()
    
    if args.week:
        process_weekly_aggregation(target_yearweek=args.week)
    elif args.latest:
        process_weekly_aggregation(latest_only=True)
    elif args.current:
        current_week = get_current_yearweek()
        process_weekly_aggregation(target_yearweek=current_week)
    else:
        process_weekly_aggregation()

if __name__ == "__main__":
    main() 