from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uvicorn
from humanfriendly import parse_size
import os
import asyncio
import json

app = FastAPI()

BACKUP_DIR = "./limits"
BACKUP_FILE = os.path.join(BACKUP_DIR, "limits_backup.json")

# Default values
DEFAULT_FILE_LIMIT = parse_size("512MB")
DEFAULT_USER_LIMIT_SIZE = parse_size("1G")
DEFAULT_FOLDER_LIMIT = parse_size("10G")

# User-specific folder limits
USER_LIMIT_SIZE = {}

# Models for request bodies
class LimitSetRequest(BaseModel):
    value: int

def save_limits():
    """Save current limits to a backup file."""
    data = {
        "DEFAULT_FILE_LIMIT": DEFAULT_FILE_LIMIT,
        "DEFAULT_USER_LIMIT_SIZE": DEFAULT_USER_LIMIT_SIZE,
        "DEFAULT_FOLDER_LIMIT": DEFAULT_FOLDER_LIMIT,
        "USER_LIMIT_SIZE": USER_LIMIT_SIZE
    }

    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(BACKUP_FILE, "w") as f:
        json.dump(data, f)

def load_limits():
    """Load limits from a backup file."""
    global DEFAULT_FILE_LIMIT, DEFAULT_USER_LIMIT_SIZE, DEFAULT_FOLDER_LIMIT, USER_LIMIT_SIZE
    try:
        if os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, "r") as f:
                data = json.load(f)
                DEFAULT_FILE_LIMIT = data.get("DEFAULT_FILE_LIMIT", DEFAULT_FILE_LIMIT)
                DEFAULT_USER_LIMIT_SIZE = data.get("DEFAULT_USER_LIMIT_SIZE", DEFAULT_USER_LIMIT_SIZE)
                DEFAULT_FOLDER_LIMIT = data.get("DEFAULT_FOLDER_LIMIT", DEFAULT_FOLDER_LIMIT)
                USER_LIMIT_SIZE = data.get("USER_LIMIT_SIZE", USER_LIMIT_SIZE)
    except json.JSONDecodeError:
            print("JSONDecodeError: Unable to decode backup file. Starting with default values.")

async def periodic_backup():
    while True:
        save_limits()
        await asyncio.sleep(60)  # Wait 60 seconds before saving again

@app.on_event("startup")
async def load_and_start_backup():
    load_limits()
    asyncio.create_task(periodic_backup())

# Routes for DEFAULT_FILE_LIMIT
@app.get("/default_file_limit")
async def get_default_file_limit():
    return {"value": DEFAULT_FILE_LIMIT}

@app.post("/default_file_limit")
async def set_default_file_limit(request: LimitSetRequest):
    global DEFAULT_FILE_LIMIT
    DEFAULT_FILE_LIMIT = request.value
    return Response(status_code=status.HTTP_200_OK)

# Routes for DEFAULT_USER_LIMIT_SIZE
@app.get("/default_user_limit_size")
async def get_default_user_limit_size():
    return {"value": DEFAULT_USER_LIMIT_SIZE}

@app.post("/default_user_limit_size")
async def set_default_user_limit_size(request: LimitSetRequest):
    global DEFAULT_USER_LIMIT_SIZE
    DEFAULT_USER_LIMIT_SIZE = request.value
    return Response(status_code=status.HTTP_200_OK)

# Routes for DEFAULT_FOLDER_LIMIT
@app.get("/default_folder_limit")
async def get_default_folder_limit():
    return {"value": DEFAULT_FOLDER_LIMIT}

@app.post("/default_folder_limit")
async def set_default_folder_limit(request: LimitSetRequest):
    global DEFAULT_FOLDER_LIMIT
    DEFAULT_FOLDER_LIMIT = request.value
    return Response(status_code=status.HTTP_200_OK)

# Routes for USER_LIMIT_SIZE
@app.get("/user_limit/{username}")
async def get_user_limit(username: str):
    limit = USER_LIMIT_SIZE.get(username, DEFAULT_USER_LIMIT_SIZE)
    return {"value": limit}

@app.post("/user_limit/{username}")
async def set_user_limit(username: str, request: LimitSetRequest):
    USER_LIMIT_SIZE[username] = request.value
    return Response(status_code=status.HTTP_200_OK)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5577)