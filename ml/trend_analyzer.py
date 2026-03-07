import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from sklearn.linear_model import LinearRegression

def generate_trend_forecast(monthly_values):
    """
    Given a list of dicts with 'month' and 'value', predicts the next 3 months.
    Returns:
    {
      "forecast": [{"month": "2026-04", "predicted_value": N}, ...],
      "trend_direction": "UP|DOWN|STABLE",
      "confidence": 0.0-1.0
    }
    """
    if len(monthly_values) < 3:
        return {"forecast": [], "trend_direction": "STABLE", "confidence": 0.0}
        
    df = pd.DataFrame(monthly_values)
    df['date'] = pd.to_datetime(df['month'])
    df = df.sort_values('date').set_index('date')
    
    y = df['value'].values
    
    forecast_values = []
    trend = "STABLE"
    conf = 0.5
    
    try:
        # Try ARIMA
        model = ARIMA(y, order=(1,1,1))
        model_fit = model.fit()
        forecast_values = model_fit.forecast(steps=3)
        conf = 0.8
    except:
        # Fallback to LinearRegression
        X = np.arange(len(y)).reshape(-1, 1)
        model = LinearRegression()
        model.fit(X, y)
        X_pred = np.arange(len(y), len(y) + 3).reshape(-1, 1)
        forecast_values = model.predict(X_pred)
        conf = 0.6
        
    # Determine direction
    if len(forecast_values) > 0 and y[-1] > 0:
        change = (forecast_values[-1] - y[-1]) / y[-1]
        if change > 0.05:
            trend = "UP"
        elif change < -0.05:
            trend = "DOWN"
            
    # Generate future months
    last_date = df.index[-1]
    forecast = []
    
    for i, val in enumerate(forecast_values):
        # Add months
        next_date = last_date + pd.DateOffset(months=i+1)
        forecast.append({
            "month": next_date.strftime('%Y-%m'),
            "predicted_value": float(max(0, val)) # no negative predictions
        })
        
    return {
        "forecast": forecast,
        "trend_direction": trend,
        "confidence": conf
    }
