# Weekly Case Aggregation and Prediction System

This system aggregates daily case data into weekly summaries, trains SARIMAX models, and provides 4-week forecasts for disease cases.

## Features

- **Daily Case Submission**: Submit individual daily case records
- **Weekly Aggregation**: Automatically sum daily cases into weekly totals
- **Model Training**: Train SARIMAX models for each ICD10 code
- **4-Week Forecasting**: Predict cases for the next 4 weeks
- **Scheduled Processing**: Automatic weekly aggregation and monthly model training
- **API Endpoints**: RESTful API for manual operations and data retrieval
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## Database Schema

The system works with the following database tables:

- `daily_case`: Stores individual daily case records
- `weekly_case`: Stores aggregated weekly case summaries
- `predictions`: Stores model predictions with confidence intervals
- `monthly_case_complete`: Additional case metadata
- `penyakit`: Disease information with ICD10 codes

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
DB_HOST=your_db_host
DB_PORT=your_db_port
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

3. Create the predictions table:
```bash
psql -h your_db_host -U your_db_user -d your_db_name -f create_predictions_table.sql
```

## Usage

### 1. Manual Weekly Aggregation

#### Using the Script
```bash
# Process all unprocessed weeks
python weekly_aggregator.py

# Process specific week
python weekly_aggregator.py --week 202401

# Process only the latest week
python weekly_aggregator.py --latest

# Process current week
python weekly_aggregator.py --current
```

#### Using the API
```bash
# Trigger aggregation for all unprocessed weeks
curl -X POST "http://localhost:8000/aggregate_weekly/"

# Trigger aggregation for specific week
curl -X POST "http://localhost:8000/aggregate_weekly/?target_yearweek=202401"
```

### 2. Manual Model Training and Prediction

#### Using the Script
```bash
# Train models and make predictions for all ICD10 codes
python model_trainer.py --train

# Train with custom forecast steps
python model_trainer.py --train --steps 6
```

#### Using the API
```bash
# Train models and make predictions
curl -X POST "http://localhost:8000/train_models/"

# Train with custom forecast steps
curl -X POST "http://localhost:8000/train_models/?forecast_steps=6"
```

### 3. Automated Scheduling (Recommended)

#### Start the Monthly Scheduler
```bash
python monthly_scheduler.py start
```

The scheduler will automatically:
- Run weekly aggregation every Sunday at 23:59
- Run model training and forecasting on the last day of each month at 23:00

#### Check Scheduler Status
```bash
python monthly_scheduler.py status
```

#### Manual Triggers
```bash
# Manually trigger weekly aggregation
python monthly_scheduler.py weekly

# Manually trigger model training
python monthly_scheduler.py train
```

#### Stop the Scheduler
```bash
python monthly_scheduler.py stop
```

### 4. API Endpoints

#### Submit Daily Case
```bash
curl -X POST "http://localhost:8000/submit_case/" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15",
    "cases": 25,
    "code": "A00"
  }'
```

#### Get Weekly Statistics
```bash
# Get all weekly stats
curl "http://localhost:8000/weekly_stats/"

# Get stats for specific week
curl "http://localhost:8000/weekly_stats/?yearweek=202401"
```

#### Get Predictions
```bash
# Get all predictions
curl "http://localhost:8000/predictions/"

# Get predictions for specific ICD10 code
curl "http://localhost:8000/predictions/?icd10_code=A00"

# Get predictions for specific model version
curl "http://localhost:8000/predictions/?model_version=A00_20240101_52"
```

#### Get Latest Yearweek
```bash
curl "http://localhost:8000/latest_yearweek/"
```

### 5. Running the FastAPI Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## How It Works

### Weekly Aggregation Process

1. **Data Collection**: Daily cases are stored in the `daily_case` table with a `yearweek` field
2. **Aggregation**: The system groups daily cases by `yearweek` and `ICD10_code`
3. **Weekly Summary**: Creates weekly totals with the Monday of each week as reference
4. **Conflict Handling**: Uses `ON CONFLICT` to update existing weekly records

### Model Training and Prediction Process

1. **Data Preparation**: Retrieves weekly case data for each ICD10 code
2. **Model Training**: Trains SARIMAX models with seasonal patterns
3. **Forecasting**: Generates 4-week predictions with confidence intervals
4. **Storage**: Saves predictions to the `predictions` table
5. **Versioning**: Each model gets a unique version identifier

### Scheduling Logic

- **Weekly Aggregation**: Every Sunday at 23:59 (end of week)
- **Monthly Model Training**: Last day of month at 23:00
- **Scope**: Processes current week's data and retrains all models
- **Error Handling**: Comprehensive logging and error recovery
- **Graceful Shutdown**: Handles system signals properly

### Data Flow

```
Daily Cases → Weekly Aggregation → Weekly Summary → Model Training → Predictions
     ↓              ↓                    ↓              ↓              ↓
daily_case    weekly_aggregator    weekly_case   model_trainer   predictions
```

## Model Details

### SARIMAX Configuration
- **Order**: (2, 0, 0) - AR(2) model
- **Seasonal Order**: (0, 1, 1, seasonal_period) - Seasonal differencing
- **Seasonal Period**: Automatically determined based on data length
- **Forecast Steps**: 4 weeks (configurable)

### Prediction Storage
- **Primary Key**: `ICD10_code/yearweek/model_version`
- **Confidence Intervals**: Lower and upper bounds for uncertainty
- **Model Versioning**: Date and data size included in version
- **Actual vs Predicted**: Flag to distinguish predictions from actual values

## Logging

The system provides comprehensive logging:

- **weekly_aggregator.log**: Manual aggregation operations
- **scheduler.log**: Scheduled job execution
- **monthly_scheduler.log**: Combined scheduler operations
- **model_trainer.log**: Model training and prediction operations
- **Console output**: Real-time status updates

## Error Handling

- Database connection errors are logged and handled gracefully
- Missing data scenarios are handled with appropriate warnings
- Model training failures are logged with detailed error messages
- Transaction rollback on errors
- Automatic retry mechanisms for failed operations

## Monitoring

### Check Logs
```bash
# View aggregation logs
tail -f weekly_aggregator.log

# View scheduler logs
tail -f monthly_scheduler.log

# View model training logs
tail -f model_trainer.log
```

### Database Queries
```sql
-- Check weekly aggregation status
SELECT 
    dc.yearweek,
    COUNT(dc.daily_case_pk) as daily_records,
    COUNT(wc.weekly_case_pk) as weekly_records
FROM daily_case dc
LEFT JOIN weekly_case wc ON dc.yearweek = wc.yearweek
GROUP BY dc.yearweek
ORDER BY dc.yearweek DESC;

-- Check latest predictions
SELECT 
    p."ICD10_code",
    p.yearweek,
    p.predicted_cases,
    p.confidence_lower,
    p.confidence_upper,
    p.model_version
FROM predictions p
WHERE p.is_actual = 0
ORDER BY p.yearweek DESC, p."ICD10_code";

-- Compare predictions with actuals
SELECT 
    p.yearweek,
    p."ICD10_code",
    p.predicted_cases,
    wc.cases as actual_cases,
    ABS(p.predicted_cases - wc.cases) as absolute_error
FROM predictions p
JOIN weekly_case wc ON p.yearweek = wc.yearweek AND p."ICD10_code" = wc."ICD10_code"
WHERE p.is_actual = 0
ORDER BY p.yearweek DESC;
```

## Deployment on VM

### Using PM2 (Recommended)
```bash
# Install PM2
npm install -g pm2

# Start both backend and scheduler
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Set up PM2 to start on boot
pm2 startup
```

### Using Systemd
```bash
# Create systemd service file
sudo cp monthly-scheduler.service /etc/systemd/system/

# Edit the service file with your actual paths
sudo nano /etc/systemd/system/monthly-scheduler.service

# Enable and start the service
sudo systemctl enable monthly-scheduler
sudo systemctl start monthly-scheduler
```

### Using Direct Process
```bash
# Start scheduler in background
nohup python monthly_scheduler.py start > monthly_scheduler.log 2>&1 &

# Check if it's running
ps aux | grep monthly_scheduler
```

## Troubleshooting

### Common Issues

1. **Scheduler not running**: Check if the process is active and logs for errors
2. **Missing weekly data**: Verify daily_case table has data for the target week
3. **Model training failures**: Check if statsmodels and dependencies are installed
4. **Database connection**: Ensure environment variables are correctly set
5. **Permission issues**: Check file permissions for log files and model directory

### Debug Mode

Enable debug logging by modifying the logging level in the scripts:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Production Deployment

For production deployment, consider:

1. **Process Management**: Use PM2 or systemd for scheduler
2. **Database Optimization**: Add indexes on frequently queried columns
3. **Model Storage**: Use cloud storage for model files
4. **Monitoring**: Set up alerts for failed aggregations and model training
5. **Backup**: Regular database backups before aggregation
6. **Load Balancing**: Multiple API instances for high availability
7. **Resource Management**: Monitor CPU and memory usage during model training

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc` 