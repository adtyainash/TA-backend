-- Create predictions table for storing model forecasts
CREATE TABLE IF NOT EXISTS public.predictions (
    prediction_pk text NOT NULL,
    "ICD10_code" text,
    yearweek text,
    predicted_cases double precision,
    confidence_lower double precision,
    confidence_upper double precision,
    model_version text,
    created_at date,
    is_actual bigint DEFAULT 0,
    CONSTRAINT predictions_pkey PRIMARY KEY (prediction_pk)
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_predictions_icd10 ON public.predictions("ICD10_code");
CREATE INDEX IF NOT EXISTS idx_predictions_yearweek ON public.predictions(yearweek);
CREATE INDEX IF NOT EXISTS idx_predictions_model_version ON public.predictions(model_version);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON public.predictions(created_at);

-- Add comments for documentation
COMMENT ON TABLE public.predictions IS 'Stores model predictions for disease cases';
COMMENT ON COLUMN public.predictions.prediction_pk IS 'Primary key: ICD10_code/yearweek/model_version';
COMMENT ON COLUMN public.predictions.predicted_cases IS 'Predicted number of cases';
COMMENT ON COLUMN public.predictions.confidence_lower IS 'Lower bound of confidence interval';
COMMENT ON COLUMN public.predictions.confidence_upper IS 'Upper bound of confidence interval';
COMMENT ON COLUMN public.predictions.model_version IS 'Version identifier for the model';
COMMENT ON COLUMN public.predictions.created_at IS 'Date when prediction was created';
COMMENT ON COLUMN public.predictions.is_actual IS '0 for prediction, 1 for actual value (when available)'; 