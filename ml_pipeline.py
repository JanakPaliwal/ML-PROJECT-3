import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error, r2_score

DATA_DIR = r"C:\Users\ADMIN\.gemini\antigravity\scratch\mandi_price_forecasting"

def load_data(crop_name):
    filepath = os.path.join(DATA_DIR, f"{crop_name}_real_dataset.csv")
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df

def treat_outliers_iqr(series):
    q25 = series.quantile(0.25)
    q75 = series.quantile(0.75)
    iqr = q75 - q25
    lower_bound = q25 - 1.5 * iqr
    upper_bound = q75 + 1.5 * iqr
    return series.clip(lower=lower_bound, upper=upper_bound)

def create_features(df, lag_days=3):
    df_feat = df.copy()
    # Outlier treatment on median_price
    df_feat['median_price_clean'] = treat_outliers_iqr(df_feat['median_price'])
    
    # Create lag features
    for lag in range(1, lag_days + 1):
        df_feat[f'lag_price_{lag}'] = df_feat['median_price_clean'].shift(lag)
        df_feat[f'lag_mandis_{lag}'] = df_feat['mandis_reporting'].shift(lag)
    
    # Rolling statistics over previous days
    df_feat['rolling_mean_3'] = df_feat['median_price_clean'].shift(1).rolling(window=3).mean()
    df_feat['rolling_std_3'] = df_feat['median_price_clean'].shift(1).rolling(window=3).std().fillna(0)
    
    feature_cols = [f'lag_price_{lag}' for lag in range(1, lag_days + 1)] + \
                   [f'lag_mandis_{lag}' for lag in range(1, lag_days + 1)] + \
                   ['rolling_mean_3', 'rolling_std_3']
    
    # Drop only rows where feature_cols or target are NaN (i.e. first 3 rows)
    df_model = df_feat.dropna(subset=feature_cols + ['median_price_clean']).reset_index(drop=True)
    
    return df_model, feature_cols

def train_and_evaluate_models(crop_name):
    df = load_data(crop_name)
    df_model, feature_cols = create_features(df, lag_days=3)
    
    X = df_model[feature_cols].values
    y = df_model['median_price_clean'].values
    
    # Split train and test (Time-series split: test on the latest 7 days)
    test_size = 7
    X_train, X_test = X[:-test_size], X[-test_size:]
    y_train, y_test = y[:-test_size], y[-test_size:]
    test_dates = df_model['date'].iloc[-test_size:].dt.strftime('%Y-%m-%d').tolist()
    
    models = {
        "Linear Regression (Lag Features)": LinearRegression(),
        "Polynomial Regression (Degree 2)": Pipeline([
            ('poly', PolynomialFeatures(degree=2, include_bias=False)),
            ('linear', Ridge(alpha=10.0))  # Ridge regularized poly to avoid overfitting small N
        ]),
        "Ridge Regression": Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=1.0))
        ]),
        "k-NN Regressor (k=3)": Pipeline([
            ('scaler', StandardScaler()),
            ('knn', KNeighborsRegressor(n_neighbors=3, weights='distance'))
        ]),
        "Multi-Layer Perceptron (MLP)": Pipeline([
            ('scaler', StandardScaler()),
            ('mlp', MLPRegressor(hidden_layer_sizes=(16, 8), activation='relu', max_iter=2000, random_state=42))
        ])
    }
    
    results = {}
    fitted_models = {}
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Metrics
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        mape = mean_absolute_percentage_error(y_test, y_pred) * 100
        r2 = r2_score(y_test, y_pred)
        
        results[name] = {
            "rmse": round(float(rmse), 2),
            "mae": round(float(mae), 2),
            "mape": round(float(mape), 2),
            "r2": round(float(r2), 4),
            "test_predictions": [round(float(p), 2) for p in y_pred],
            "actual": [round(float(a), 2) for a in y_test],
            "test_dates": test_dates
        }
        fitted_models[name] = model

    # Select best model based on MAE
    best_model_name = min(results, key=lambda k: results[k]['mae'])
    
    # Generate 7-day future recursive forecast
    best_model = fitted_models[best_model_name]
    recent_prices = df_model['median_price_clean'].tolist()
    recent_mandis = df_model['mandis_reporting'].tolist()
    
    future_forecast = []
    last_date = df_model['date'].iloc[-1]
    
    curr_prices = recent_prices.copy()
    curr_mandis = recent_mandis.copy()
    
    for day in range(1, 8):
        next_date = last_date + timedelta(days=day)
        
        # Build features for next day
        lag1 = curr_prices[-1]
        lag2 = curr_prices[-2]
        lag3 = curr_prices[-3]
        lag_m1 = curr_mandis[-1]
        lag_m2 = curr_mandis[-2]
        lag_m3 = curr_mandis[-3]
        roll_mean = np.mean([curr_prices[-1], curr_prices[-2], curr_prices[-3]])
        roll_std = np.std([curr_prices[-1], curr_prices[-2], curr_prices[-3]])
        
        x_future = np.array([[lag1, lag2, lag3, lag_m1, lag_m2, lag_m3, roll_mean, roll_std]])
        pred_val = float(best_model.predict(x_future)[0])
        
        pct_change = (pred_val - curr_prices[-1]) / curr_prices[-1] * 100
        volatility_flag = "High Spike Alert" if pct_change > 5 else ("Price Crash Alert" if pct_change < -5 else "Normal Fluctuation")
        
        future_forecast.append({
            "date": next_date.strftime('%Y-%m-%d'),
            "predicted_price": round(pred_val, 2),
            "pct_change": round(pct_change, 2),
            "volatility_flag": volatility_flag
        })
        curr_prices.append(pred_val)
        curr_mandis.append(int(np.mean([lag_m1, lag_m2, lag_m3])))
        
    return {
        "crop": crop_name,
        "results": results,
        "best_model": best_model_name,
        "future_forecast": future_forecast,
        "historical_data": df[['date', 'median_price', 'mandis_reporting', 'low_price', 'high_price']].assign(
            date=df['date'].dt.strftime('%Y-%m-%d')
        ).to_dict(orient='records')
    }

if __name__ == "__main__":
    t_out = train_and_evaluate_models("tomato")
    o_out = train_and_evaluate_models("onion")
    
    output_path = os.path.join(DATA_DIR, "forecasting_results.json")
    with open(output_path, "w") as f:
        json.dump({"tomato": t_out, "onion": o_out}, f, indent=2)
    print("Forecasting models trained and results saved successfully to:", output_path)
