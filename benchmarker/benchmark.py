import subprocess
import json
import os
import time
from pymongo import MongoClient
from datetime import datetime, timezone
from zoneinfo import ZoneInfo 
from helper import check_vllm_ready, extract_streaming_stats_from_file 
from dotenv import load_dotenv
load_dotenv()

NODE_NAME         = os.getenv("NODE_NAME", "test") # DOKS WOKER NAME
CLIENT_NUMBER     = int(os.getenv("CLIENT_NUMBER","1")) 

CONCURRENCY       = int(os.getenv("CONCURRENCY", 8))
MEMORY_LIMIT      = int(os.getenv("MEMORY_LIMIT", 2684354560))  # 2.5 GiB
MODEL             = os.getenv("MODEL", "Llama-3.1-70B-Instruct")
SERVED_MODEL_NAME = os.getenv("SERVED_MODEL_NAME", "meta-llama/Llama-3.1-70B-Instruct")

BUCKET            = os.getenv("BUCKET", "rs-high-perf-bucket")  # your S3 bucket name
FOLDER            = os.getenv("FOLDER", "models")

username     = os.getenv("MDB_USERNAME", "")
password     = os.getenv("MDB_PASSWORD", "")
host         = os.getenv("MDB_HOST", "")
database     = os.getenv("MDB_DATABASE", "")      # The database that stores the user credentials
benchmark_db = os.getenv("MDB_BENCHMARK_DB", "")  # The database that stores the benchmark results

task_id      = os.getenv("TASK_ID", "")
others       = os.getenv("OTHERS", "")


# Build connection URI and Connect to MongoDB
uri = f"mongodb+srv://{username}:{password}@{host}/?tls=true&authSource={database}&retryWrites=true&w=majority"
mongo_db_client = MongoClient(uri)

try:
    db = mongo_db_client[benchmark_db]
    temp = db.command("ping") # should return {'ok': 1.0} if successful
    print("\nConnected to MongoDB successfully!", flush=True)
except Exception as e:
    print(f"\nError connecting to MongoDB: {e}", flush=True)
    time.sleep(999999) # Need troubleshooting
    

result_data = {}

result_data["node_name"]         = NODE_NAME
result_data["client_number"]     = CLIENT_NUMBER

result_data["concurrency"]       = CONCURRENCY
result_data["memory_limit"]      = MEMORY_LIMIT
result_data["model"]             = MODEL
result_data["served_model_name"] = SERVED_MODEL_NAME

result_data["bucket"]            = BUCKET
result_data["folder"]            = FOLDER

result_data["task_id"]       = task_id
result_data["others"]        = others
result_data["timestamp"]     = datetime.now(timezone.utc)     
result_data["date"]          = str(datetime.now(ZoneInfo("America/Los_Angeles")).date())

START = time.perf_counter()


# Environment variables
env = os.environ.copy()
env.update({
    "RUNAI_STREAMER_S3_USE_VIRTUAL_ADDRESSING": "0",
    "AWS_EC2_METADATA_DISABLED": "true"
})

# Model loader extra config
model_loader_config = {
    "concurrency": CONCURRENCY,
    "memory_limit": MEMORY_LIMIT
}

# Command
command = [
    "vllm", "serve", f"s3://{BUCKET}/{FOLDER}/{MODEL}",
    "--load-format", "runai_streamer",
    "--model-loader-extra-config", json.dumps(model_loader_config),
    "--served-model-name", SERVED_MODEL_NAME
]

# Open log file
with open("vllm_server.log", "w") as log_file:
    # Start the server and redirect output to the log file
    process = subprocess.Popen(command, env=env, stdout=log_file, stderr=log_file, text=True)
    print(f"vllm server started with PID {process.pid}, logging to vllm_server.log")

if not check_vllm_ready():
    result_data['state'] = "failed" 
    result_data['message'] = "!!!!!! Cannot start in the specified time" 
    result_data['startup time_s'] = 999999999

    result_data['model_GiB'] = 999999999
    result_data['time_s'] = 999999999
    result_data['throughput_GiB_s'] = 999999999


else:
    END = time.perf_counter()
    result_data['state'] = "success"
    result_data['message'] = "Started successfully"
    result_data['startup time_s'] = round(END - START,3)

    try:
        model_GiB, time_s, throughput_GiB_s = extract_streaming_stats_from_file("vllm_server.log")
    except Exception as e:
        print(f"!!!!!! Error extracting streaming stats: {e}", flush=True)
        model_GiB, time_s, throughput_GiB_s = 999999999, 999999999, 999999999
        result_data['state']   = "no_stats"
        result_data['message'] = "!!!!!! Started successfully, but failed to extract streaming stats"

    result_data['model_GiB']        = model_GiB
    result_data['time_s']           = time_s
    result_data['throughput_GiB_s'] = throughput_GiB_s

result_data["timestamp_end"]     = datetime.now(timezone.utc)     

print(result_data, flush=True)

db = mongo_db_client[benchmark_db]
results = db["results"]
result = results.insert_one(result_data)
print("Inserted document ID:", result.inserted_id, flush=True)

print("\n" + "-" * 40 + "> Test completed", flush=True)
time.sleep(999999) # Completed
