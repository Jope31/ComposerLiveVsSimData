import numpy as np
import requests
import os
import sys
from datetime import datetime, date, timedelta
import importlib.util

# --- Step 1: Import Authentication and Utility Functions ---
try:
    from auth import get_auth_details
except ImportError:
    print("Error: Could not find 'auth.py'.")
    print("Please ensure it is in the same directory.")
    sys.exit(1)

# --- Configuration ---
# API endpoints from your scripts
BACKTEST_API_BASE = "https://backtest-api.composer.trade/api/v2"
LIVE_API_BASE = "https://stagehand-api.composer.trade/api/v1"

# --- Step 2: Discover Symphonies and their Start Dates from Master Runner ---
def get_symphony_list_from_scripts():
    """
    Dynamically loads symphony configurations from the script files
    listed in master_runner.py. It now captures the specific START_DATE
    from each file.
    """
    symphonies = {}
    try:
        # Dynamically import the list of scripts from master_runner.py
        spec = importlib.util.spec_from_file_location("master_runner", "master_runner.py")
        master_runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(master_runner)
        symphony_script_files = master_runner.SYMPHONY_SCRIPT_FILES
        
        print(f"Found {len(symphony_script_files)} script files listed in master_runner.py.")

        for script_file in set(symphony_script_files): # Use set to avoid duplicates
            if not os.path.exists(script_file):
                print(f"Warning: Skipping {script_file} (File not found).")
                continue
            
            # Dynamically import the SYMPHONIES dictionary and START_DATE from each script
            spec = importlib.util.spec_from_file_location(script_file, script_file)
            symph_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(symph_module)
            
            start_date_for_script = symph_module.START_DATE
            
            for name, sym_id in symph_module.SYMPHONIES.items():
                if sym_id not in [s['id'] for s in symphonies.values()]:
                     symphonies[name] = {'id': sym_id, 'start_date': start_date_for_script}

    except (ImportError, AttributeError, FileNotFoundError) as e:
        print(f"Error reading symphony configurations: {e}")
        print("Falling back to placeholder data. Please check your file structure.")
        return {"Anansi Portfolio | 2025-06-05": {'id': "FTZP9wjzjvnIw21KQtIL", 'start_date': '2025-01-01'}}

    print(f"Discovered a total of {len(symphonies)} unique symphonies to analyze.")
    return symphonies


# --- Step 3: Real Data Pulling Functions ---
def get_backtest_pnl_series(api_key, secret_key, symphony_id, start_date):
    """
    Pulls backtest data using the full, detailed payload that is confirmed
    to work for all symphonies.
    """
    url = f"{BACKTEST_API_BASE}/public/symphonies/{symphony_id}/backtest"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "x-api-key-id": api_key,
        "x-origin": "public-api"
    }
    
    # Use the full payload directly as it's been confirmed to work universally.
    full_payload = {
        "capital": 10000, "start_date": start_date, "end_date": date.today().isoformat(),
        "broker": "apex", "slippage_percent": 0.0005, "backtest_version": "v2",
        "apply_reg_fee": True, "apply_taf_fee": True
    }
    
    print(f"  Fetching backtest from {start_date}...")
    try:
        response = requests.post(url, headers=headers, json=full_payload, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  --> ERROR fetching backtest data: {e}")
        return None

    # Process the successful response
    data = response.json()
    if symphony_id in data.get('dvm_capital', {}):
        symphony_timeseries = data['dvm_capital'][symphony_id]
        capital_values = list(symphony_timeseries.values())
        pnl_series = np.diff(capital_values)
        if len(pnl_series) > 0:
            print(f"  -> Successfully processed backtest data for {symphony_id}.")
            return pnl_series
        else:
            print(f"  --> Warning: Backtest for {symphony_id} had values but no P&L changes.")
            return []
    else:
        print(f"  --> ERROR: Symphony ID {symphony_id} not found in backtest response.")
        return []

def get_live_pnl(api_key, secret_key, account_id, symphony_id):
    """Pulls the most recent live P&L data for a given symphony."""
    url = f"{LIVE_API_BASE}/portfolio/accounts/{account_id}/symphonies/{symphony_id}"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "x-api-key-id": api_key,
        "x-origin": "public-api"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'deposit_adjusted_series' in data and len(data['deposit_adjusted_series']) >= 2:
            live_points = sorted(data['deposit_adjusted_series'])
            last_pnl = live_points[-1] - live_points[-2]
            print(f"  -> Successfully fetched live P&L for {symphony_id}.")
            return last_pnl
        else:
            print(f"  --> Warning: Not enough live data points for {symphony_id} to calculate P&L.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"  --> ERROR fetching live data for {symphony_id}: {e}")
        return None

# --- Step 4: Z-Score Calculation Logic ---
def calculate_z_score(live_value, mean, std_dev):
    """Calculates the Z-score."""
    if std_dev == 0:
        return float('inf') if live_value != mean else 0.0
    return (live_value - mean) / std_dev

# --- Step 5: Main Analysis Execution ---
def main():
    """Main function to run the analysis for all symphonies."""
    print("--- Starting Automated Symphony Z-Score Analysis ---")
    
    api_key, secret_key, account_id = get_auth_details()
    if not all([api_key, secret_key, account_id]):
        print("\nAuthentication failed. Cannot proceed.")
        return

    symphonies_to_run = get_symphony_list_from_scripts()
    if not symphonies_to_run:
        print("No symphonies found to analyze. Exiting.")
        return

    results = []
    for name, details in symphonies_to_run.items():
        sym_id = details['id']
        start_date = details['start_date']
        print(f"\n--- Processing: {name} ({sym_id}) ---")

        backtest_pnl_series = get_backtest_pnl_series(api_key, secret_key, sym_id, start_date)
        live_value = get_live_pnl(api_key, secret_key, account_id, sym_id)

        if backtest_pnl_series is None or live_value is None or len(backtest_pnl_series) == 0:
            print(f"Warning: Could not retrieve complete data for '{name}'. Skipping.")
            continue

        mean_pnl = np.mean(backtest_pnl_series)
        std_dev_pnl = np.std(backtest_pnl_series)
        z_score = calculate_z_score(live_value, mean_pnl, std_dev_pnl)
        
        results.append({
            "name": name, "z_score": z_score, "live_pnl": live_value,
            "mean_pnl": mean_pnl, "std_dev_pnl": std_dev_pnl
        })

        print(f"  Live P&L (Last Period): ${live_value:,.2f}")
        print(f"  Backtest Mean Daily P&L: ${mean_pnl:,.2f}")
        print(f"  Backtest Std Dev of Daily P&L: ${std_dev_pnl:,.2f}")
        print(f"  => Calculated Z-Score: {z_score:.2f}")

    if results:
        most_deviant_symphs = sorted(results, key=lambda x: abs(x['z_score']), reverse=True)
        
        print("\n\n--- Analysis Complete: Deviation Ranking ---")
        print("(Ranked from most to least deviant from historical performance)\n")
        for i, res in enumerate(most_deviant_symphs):
            print(f"{i+1}. {res['name']} (Z-Score: {res['z_score']:.2f})")

if __name__ == "__main__":
    main()
