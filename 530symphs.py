import requests
import os
from datetime import datetime, date, timedelta
import json
import time
import sys # <-- Required to read arguments from the master script

# --- Configuration ---
# You only need to edit the values in this section for each file.

# 1. Your Symphonies for THIS file
# For '530symphs.py', this would contain symphonies starting on May 30.
SYMPHONIES = {
    "Black Swan Catcher (SPY)": "OLmQh1J0ePZof2F2nEn9",
    "EZ Win": "RFgmUeWk5UgRLVb6s0tQ",
    # "Another Symphony Name": "ANOTHER_SYMPHONY_ID_HERE",
}

# 2. Backtest Start Date for THIS file
START_DATE = "2025-05-30"


# --- API Endpoints ---
BACKTEST_API_BASE = "https://backtest-api.composer.trade/api/v2"
LIVE_API_BASE = "https://stagehand-api.composer.trade/api/v1"


def fetch_backtest_data(bearer_token, symphony_id, start_date):
    """Fetches historical backtest data for a single symphony."""
    url = f"{BACKTEST_API_BASE}/public/symphonies/{symphony_id}/backtest"
    print(f"Fetching Backtest Data from: {url}")
    
    headers = {"Authorization": f"Bearer {bearer_token}"}
    payload = {
        "capital": 10000,
        "start_date": start_date,
        "end_date": date.today().isoformat(),
        "broker": "apex",
        "slippage_percent": 0.0005,
        "backtest_version": "v2",
        "apply_reg_fee": True,
        "apply_taf_fee": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"-> Successfully fetched backtest data for {symphony_id}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"--> ERROR fetching backtest data for {symphony_id}: {e}")
        return None

def fetch_live_data(bearer_token, account_id, symphony_id):
    """Fetches live portfolio history for a single symphony."""
    url = f"{LIVE_API_BASE}/portfolio/accounts/{account_id}/symphonies/{symphony_id}"
    print(f"Fetching Live Data from: {url}")
    
    headers = {"Authorization": f"Bearer {bearer_token}"}
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
    Merges live and backtest data for a single symphony and calculates percentage returns.
    Returns a dictionary of the processed data.
    """
    merged_data = {}
    
    # --- Process Live Data ---
    if live_data and 'epoch_ms' in live_data and 'deposit_adjusted_series' in live_data:
        live_points = sorted(zip(live_data['epoch_ms'], live_data['deposit_adjusted_series']))
        live_baseline = None
        for ms_timestamp, value in live_points:
            date_str = datetime.fromtimestamp(ms_timestamp / 1000).strftime('%Y-%m-%d')
            if date_str >= start_date_filter:
                if live_baseline is None:
                    live_baseline = value
                
                if date_str not in merged_data:
                    merged_data[date_str] = {}
                
                if live_baseline > 0:
                    merged_data[date_str]['live_pct'] = (value / live_baseline) - 1

    # --- Process Backtest Data ---
    if backtest_data and 'dvm_capital' in backtest_data:
        if symphony_id in backtest_data['dvm_capital']:
            symphony_timeseries = backtest_data['dvm_capital'][symphony_id]
            backtest_baseline = 10000

            for day_key, value in symphony_timeseries.items():
                date_obj = date(1970, 1, 1) + timedelta(days=int(day_key))
                date_str = date_obj.isoformat()
                
                if date_str >= start_date_filter:
                    if date_str not in merged_data:
                        merged_data[date_str] = {}
                    merged_data[date_str]['backtest_pct'] = (value / backtest_baseline) - 1
            
    return merged_data

def run_main_logic(bearer_token, account_id):
    """Main logic to fetch, process, and print data for the configured symphonies."""
    all_rows = []
    
    for symphony_name, symphony_id in SYMPHONIES.items():
        print(f"\n{'='*20} Processing: {symphony_name} ({symphony_id}) {'='*20}")
        
        live_data = fetch_live_data(bearer_token, account_id, symphony_id)
        backtest_data = fetch_backtest_data(bearer_token, symphony_id, START_DATE)
        
        if live_data or backtest_data:
            processed_data = process_and_merge_data(live_data, backtest_data, symphony_id, START_DATE)
            
            for date_str, returns in processed_data.items():
                all_rows.append({
                    "Date": date_str, "Symphony": symphony_name,
                    "Live": returns.get('live_pct', ''), "Backtest": returns.get('backtest_pct', '')
                })
        else:
            print(f"--> Could not fetch any data for {symphony_name}. Skipping.")
        time.sleep(1) 

    if all_rows:
        print("\n\n--- Copy the data below and paste it into Google Sheets ---")
        print("Date,Symphony Name,Live Performance (%),Backtest Performance (%)")
        
        for row in sorted(all_rows, key=lambda x: (x['Symphony'], x['Date'])):
            live_str = f"{row['Live']:.4f}" if isinstance(row['Live'], float) else ''
            backtest_str = f"{row['Backtest']:.4f}" if isinstance(row['Backtest'], float) else ''
            print(f"{row['Date']},{row['Symphony']},{live_str},{backtest_str}")
    else:
        print("\nNo data was processed for any symphony.")


if __name__ == "__main__":
    # This block checks if the script was run with arguments from the master script.
    if len(sys.argv) > 2:
        # The token is the first argument, account ID is the second.
        token_from_master = sys.argv[1]
        account_id_from_master = sys.argv[2]
        run_main_logic(token_from_master, account_id_from_master)
    else:
        # If run directly, print an error.
        print("ERROR: This script is designed to be run by 'master_runner.py'.")
        print("Please run the master script, and it will call this one automatically.")
