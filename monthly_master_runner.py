import subprocess
import sys
import os
from datetime import datetime
import time
from auth import get_auth_details # <-- Import the new authentication function

# --- Configuration ---
# Add the filenames of all your symphony scripts that you want to run
# with a custom start date.
MONTHLY_SCRIPT_FILES = [
    "all_symphs_monthly.py",
]

def is_valid_date(date_string):
    """Helper function to validate the date format."""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def run_monthly_scripts(api_key, secret_key, account_id, start_date):
    """
    Loops through the list of script files and runs each one,
    passing the provided credentials and start date as arguments.
    """
    print(f"\nFound {len(MONTHLY_SCRIPT_FILES)} scripts to run.")
    
    for script_file in MONTHLY_SCRIPT_FILES:
        if not os.path.exists(script_file):
            print(f"\n{'='*20} WARNING: Skipping {script_file} (File not found) {'='*20}")
            continue
            
        print(f"\n{'='*20} Running: {script_file} for start date {start_date} {'='*20}")
        
        try:
            # Pass all three credentials plus the start date to the child script.
            result = subprocess.run(
                [sys.executable, script_file, secret_key, account_id, api_key, start_date],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            print(f"--- ERROR running {script_file} ---")
            print("--- Script Output (stdout): ---")
            print(e.stdout)
            print("--- Script Error (stderr): ---")
            print(e.stderr)
        except FileNotFoundError:
             print(f"ERROR: Could not find the Python interpreter at '{sys.executable}'")
             break
        
        time.sleep(1)


if __name__ == "__main__":
    print("--- Composer Monthly Metrics Script Runner ---")
    
    # Get the API Key, Secret, and Account ID using the automated method.
    api_key, secret_key, account_id = get_auth_details()

    if api_key and secret_key and account_id:
        # If authentication was successful, now only ask for the Start Date.
        start_date = input("Enter the Start Date for your analysis (YYYY-MM-DD) and press Enter: ")
        
        if not start_date.strip():
            print("\nERROR: Start Date cannot be empty.")
        elif not is_valid_date(start_date):
            print("\nERROR: Invalid date format. Please use YYYY-MM-DD.")
        else:
            run_monthly_scripts(api_key, secret_key, account_id, start_date)
    else:
        print("\nAuthentication failed. Cannot proceed.")
        
    print("\n--- Master script has finished. ---")
