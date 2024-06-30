import subprocess
import sys
import time

def run_script(script_path, max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            print(f"Running script: {script_path}")
            result = subprocess.run([sys.executable, script_path], check=True, capture_output=True, text=True)
            print(f"Script output:\n{result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running script {script_path}. Attempt {attempt + 1} of {max_retries}")
            print(f"Error output:\n{e.stderr}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Max retries reached for {script_path}. Moving to next script.")
                return False

def main():
    scripts_to_run = [
        "transcribe.py",
        "translate.py",
        "extract.py",
        "catch_context.py",
]    

    for script in scripts_to_run:
        success = run_script(script)
        if not success:
            print(f"Script {script} failed after max retries. Continuing with next script.")
        print("-----------------------------------")

if __name__ == "__main__":
    main()