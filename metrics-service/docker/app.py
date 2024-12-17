from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
import uvicorn
import os
import json
import asyncio

app = FastAPI()

METRICS_BACKUP_DIR = "/metrics"
os.makedirs(METRICS_BACKUP_DIR, exist_ok=True)
METRICS_BACKUP_FILE = os.path.join(METRICS_BACKUP_DIR, "metrics_backup.json")

def load_metrics_from_backup():
    """Load metrics from the backup file on initialization."""
    if os.path.exists(METRICS_BACKUP_FILE):
        try:
            with open(METRICS_BACKUP_FILE, "r") as f:
                data = json.load(f)
                total_requests_counter.inc(data.get("total_requests", 0))
                total_recived_historical_data_counter.inc(data.get("total_recived_historical_data", 0))
                total_recived_online_data_counter.inc(data.get("total_recived_online_data", 0))
                total_caching_data_counter.inc(data.get("total_caching_data", 0))
                active_requests_gauge.set(data.get("active_requests", 0))
        except Exception as e:
            print(f"Failed to load metrics from backup: {e}")

async def metrics_backup_task():
    """Background task to periodically save metrics to a file."""
    while True:
        try:
            metrics_data = {
                "total_requests": total_requests_counter._value.get(),
                "total_recived_historical_data": total_recived_historical_data_counter._value.get(),
                "total_recived_online_data": total_recived_online_data_counter._value.get(),
                "total_caching_data": total_caching_data_counter._value.get(),
                "active_requests": active_requests_gauge._value.get(),
            }
            with open(METRICS_BACKUP_FILE, "w") as f:
                json.dump(metrics_data, f)
        except Exception as e:
            print(f"Failed to backup metrics: {e}")
        await asyncio.sleep(60)  # Run every minute

# Define metrics
# cpu_usage_gauge = Gauge("feast_feature_server_cpu_usage", "CPU usage of the Feast feature server")
# memory_usage_gauge = Gauge("feast_feature_server_memory_usage", "Memory usage of the Feast feature server")
total_requests_counter = Counter('total_requests', 'Total number of requests received')
total_recived_historical_data_counter = Counter('total_recived_historical_data', 'Total size of received historical data')
total_recived_online_data_counter = Counter('total_recived_online_data', 'Total size of received online data')
active_requests_gauge = Gauge('active_requests', 'Current number of active requests')
total_caching_data_counter = Counter('total_caching_data', 'Total size of caching data')

active_users = {}

# @app.post("/metrics/cpu_usage")
# async def update_cpu_usage(request: Request):
#     data = await request.json()
#     cpu_usage = data.get("value")
#     if cpu_usage is not None:
#         cpu_usage_gauge.set(cpu_usage)
#     return {"status": "success"}

# @app.post("/metrics/memory_usage")
# async def update_memory_usage(request: Request):
#     data = await request.json()
#     memory_usage = data.get("value")
#     if memory_usage is not None:
#         memory_usage_gauge.set(memory_usage)
#     return {"status": "success"}

@app.post("/metrics/total_requests")
async def update_total_requests(request: Request):
    data = await request.json()
    total_requests = data.get("value")
    if total_requests is not None:
        total_requests_counter.inc(total_requests)
    return Response(status_code=status.HTTP_200_OK)

@app.post("/metrics/received_historical_data")
async def update_received_historical_data(request: Request):
    data = await request.json()
    received_data = data.get("value")
    if received_data is not None:
        total_recived_historical_data_counter.inc(received_data)
    return Response(status_code=status.HTTP_200_OK)

@app.post("/metrics/received_online_data")
async def update_received_online_data(request: Request):
    data = await request.json()
    received_data = data.get("value")
    if received_data is not None:
        total_recived_online_data_counter.inc(received_data)
    return Response(status_code=status.HTTP_200_OK)

@app.post("/metrics/caching_data")
async def update_caching_data(request: Request):
    data = await request.json()
    received_data = data.get("value")
    if received_data is not None:
        total_caching_data_counter.inc(received_data)
    return Response(status_code=status.HTTP_200_OK)

@app.post("/metrics/active_requests")
async def update_active_requests(request: Request):
    data = await request.json()

    active_requests = data.get("value")
    if active_requests is not None:
        if active_requests < 0:
            active_requests_gauge.dec()
        else:
            active_requests_gauge.inc()
    return Response(status_code=status.HTTP_200_OK)

@app.post("/metrics/active_users")
async def update_active_users(request: Request):
    global active_users
    data = await request.json()
    username = data.get("value")
    if username is not None:
        try:
            active_users[username] = active_users[username] + 1
        except KeyError:
            active_users[username] = 1
    return Response(status_code=status.HTTP_200_OK)

@app.delete("/metrics/active_users")
async def update_active_users(request: Request):
    global active_users
    data = await request.json()
    username = data.get("value")
    if username is not None:
        try:
            if active_users[username] > 1:
                active_users[username] = active_users[username] - 1
            elif active_users[username] == 1:
                del active_users[username]
        except KeyError:
            print(f"user {username} not found")
    return Response(status_code=status.HTTP_200_OK)

@app.get("/metrics/active_users")
async def get_active_users(request: Request):
    global active_users
    
    return JSONResponse(
        content={
            "active_users": active_users
        },
        status_code=status.HTTP_200_OK
    )

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.on_event("startup")
async def startup_event():
    # Load metrics from the backup
    load_metrics_from_backup()
    # Start the metrics backup task
    asyncio.create_task(metrics_backup_task())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5555)