import requests
import time
import re


# Health Check
HEALTH_ENDPOINT = f"http://0.0.0.0:8000/health"  # some vLLM endpoints may have /health
RETRY_INTERVAL = 5  # seconds
MAX_RETRIES = 120   # try for up to 10 minutes


def check_vllm_ready():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass  # server not ready yet

        print(f"\n!!!!!! Attempt {attempt}: vLLM server not ready, retrying in {RETRY_INTERVAL}s...", flush=True)
        time.sleep(RETRY_INTERVAL)
    return False


def extract_streaming_stats_from_file(file_path: str):
    """
    Extract total GiB, time in seconds, and throughput GiB/s from a log file.
    Returns a tuple: (model_GiB, time_s, throughput_GiB_s)
    """
    with open(file_path, "r") as f:
        log_text = f.read()
    
    # Regex pattern to match the summary line
    pattern = r"Overall time to stream ([\d.]+) GiB .*: ([\d.]+)s, ([\d.]+) GiB/s"
    
    match = re.search(pattern, log_text)
    if match:
        model_GiB = float(match.group(1))
        time_s = float(match.group(2))
        throughput_GiB_s = float(match.group(3))
        return model_GiB, time_s, throughput_GiB_s
    else:
        raise ValueError("No streaming stats found in the file")


