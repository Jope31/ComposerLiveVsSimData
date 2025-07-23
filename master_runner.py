import subprocess
import sys
import os
import time
from auth import get_auth_details # <-- Import the new authentication function

# --- Configuration ---
# Add the filenames of all your symphony scripts to this list.
SYMPHONY_SCRIPT_FILES = [
    "530symphs.py",
]

def run_symphony_scripts(api_key, secret_key, account_id):
    """
    Loops through the list of script files and runs each one,
    passing the provided credentials as arguments.
    """
    print(f"\nFound {len(SYMPHONY_SCRIPT_FILES)} scripts to run.")
    
    for script_file in SYMPHONY_SCRIPT_FILES:
        if not os.path.exists(script_file):
            print(f"\n{'='*20} WARNING: Skipping {script_file} (File not found) {'='*20}")
            continue
            
        print(f"\n{'='*20} Running: {script_file} {'='*20}")
        
        try:
            # Pass all three credentials to the child script.
            result = subprocess.run(
                [sys.executable, script_file, secret_key, account_id, api_key],
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
    print("--- Composer Master Script Runner ---")
    
    # Get the API Key, Secret, and Account ID using the new automated method.
    api_key, secret_key, account_id = get_auth_details()
    
    if api_key and secret_key and account_id:
        run_symphony_scripts(api_key, secret_key, account_id)
    else:
        print("\nAuthentication failed. Cannot proceed.")
        
    print("\n--- Master script has finished. ---")
