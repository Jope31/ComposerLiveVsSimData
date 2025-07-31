import requests
import os
from datetime import datetime, date, timedelta
import json
import time
import sys

# --- Configuration ---
# You only need to edit the SYMPHONIES list in this file.
# The Account ID, Token, and Start Date will be provided by the master script.
SYMPHONIES = {
    "Black Swan Catcher (SPY)": "OLmQh1J0ePZof2F2nEn9",
    "EZ Win": "RFgmUeWk5UgRLVb6s0tQ",
}

# --- API Endpoints ---
BACKTEST_API_BASE = "https://backtest-api.composer.trade/api/v2"
LIVE_API_BASE = "https://stagehand-api.composer.trade/api/v1"


def fetch_backtest_data(api_key, secret_key, symphony_id, start_date):
    """Fetches historical backtest data for a single symphony."""
    url = f"{BACKTEST_API_BASE}/public/symphonies/{symphony_id}/backtest"
    print(f"Fetching Backtest Data from: {url}")
    
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "x-api-key-id": api_key,
        "x-origin": "public-api"
    }
    payload = {
        "capital": 10000, "start_date": start_date, "end_date": date.today().isoformat(),
        "broker": "apex", "slippage_percent": 0.0005, "backtest_version": "v2",
        "apply_reg_fee": True, "apply_taf_fee": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"-> Successfully fetched backtest data for {symphony_id}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"--> ERROR fetching backtest data for {symphony_id}: {e}")
        return None

def fetch_live_data(api_key, secret_key, account_id, symphony_id):
    """Fetches live portfolio history for a single symphony."""
    url = f"{LIVE_API_BASE}/portfolio/accounts/{account_id}/symphonies/{symphony_id}"
    print(f"Fetching Live Data from: {url}")
    
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "x-api-key-id": api_key,
        "x-origin": "public-api"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"-> Successfully fetched live portfolio data for {symphony_id}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"--> ERROR fetching live data for {symphony_id}: {e}")
        return None

def process_and_merge_data(live_data, backtest_data, symphony_id, start_date_filter):
    """
    Processes and merges data, using the logic from the user-provided data_tester.py.
    """
    combined_performance = {}

    # 1. Process Live Data
    if live_data and 'epoch_ms' in live_data and 'deposit_adjusted_series' in live_data:
        live_points = sorted(zip(live_data['epoch_ms'], live_data['deposit_adjusted_series']))
        live_baseline = None
        for ms, value in live_points:
            # Use utcfromtimestamp to avoid local timezone conversion issues.
            date_str = datetime.utcfromtimestamp(ms / 1000).strftime('%Y-%m-%d')
            if date_str >= start_date_filter:
                if live_baseline is None: live_baseline = value
                
                if date_str not in combined_performance:
                    combined_performance[date_str] = {"Live": None, "Backtest": None}
                
                if live_baseline > 0:
                    combined_performance[date_str]["Live"] = (value / live_baseline) - 1

    # 2. Process Backtest Data
    if backtest_data and 'dvm_capital' in backtest_data and symphony_id in backtest_data['dvm_capital']:
        timeseries = backtest_data['dvm_capital'][symphony_id]
        sorted_keys = sorted(timeseries.keys(), key=int)
        backtest_baseline = None
        for day_key in sorted_keys:
            date_obj = datetime(1970, 1, 1) + timedelta(days=int(day_key))
            date_str = date_obj.strftime('%Y-%m-%d')
            
            if date_str >= start_date_filter:
                if backtest_baseline is None: backtest_baseline = timeseries[day_key]
                
                if date_str not in combined_performance:
                    combined_performance[date_str] = {"Live": None, "Backtest": None}

                if backtest_baseline > 0:
                    combined_performance[date_str]["Backtest"] = (timeseries[day_key] / backtest_baseline) - 1
    
    # 3. Convert the combined dictionary to a sorted list for final output
    final_data = []
    for date_str, values in sorted(combined_performance.items()):
        final_data.append({
            "Date": date_str,
            "Live": values["Live"],
            "Backtest": values["Backtest"]
        })
        
    return final_data

def run_main_logic(secret_key, account_id, api_key, start_date):
    """Main logic to fetch, process, and print data for the configured symphonies."""
    all_rows = []
    
    for symphony_name, symphony_id in SYMPHONIES.items():
        print(f"\n{'='*20} Processing: {symphony_name} ({symphony_id}) {'='*20}")
        
        live_data = fetch_live_data(api_key, secret_key, account_id, symphony_id)
        backtest_data = fetch_backtest_data(api_key, secret_key, symphony_id, start_date)
        
        if live_data or backtest_data:
            processed_data = process_and_merge_data(live_data, backtest_data, symphony_id, start_date)
            for row_data in processed_data:
                row_data["Symphony"] = symphony_name
                all_rows.append(row_data)
        else:
            print(f"--> Could not fetch any data for {symphony_name}. Skipping.")
        time.sleep(1) # Be respectful to the API

    if all_rows:
        print("\n\n--- Copy the data below and paste it into Google Sheets ---")
        print("Date,Symphony Name,Live Performance (%),Backtest Performance (%)")
        for row in sorted(all_rows, key=lambda x: (x['Symphony'], x['Date'])):
            live_str = f"{row['Live']:.4f}" if row['Live'] is not None else ''
            backtest_str = f"{row['Backtest']:.4f}" if row['Backtest'] is not None else ''
            print(f"{row['Date']},{row['Symphony']},{live_str},{backtest_str}")
    else:
        print("\nNo data was processed for any symphony.")


if __name__ == "__main__":
    if len(sys.argv) > 4:
        secret_key_from_master = sys.argv[1]
        account_id_from_master = sys.argv[2]
        api_key_from_master = sys.argv[3]
        start_date_from_master = sys.argv[4]
        run_main_logic(secret_key_from_master, account_id_from_master, api_key_from_master, start_date_from_master)
    else:
        print("ERROR: This script is designed to be run by 'monthly_master_runner.py'.")
        print("Please run the master script, and it will call this one automatically.")

    print("\n--- Script finished ---")
