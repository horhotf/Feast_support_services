from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi import status
from fastapi.responses import JSONResponse, Response
import uvicorn
from cachetools import TTLCache


app = FastAPI()

# Simple in-memory cache dictionary
cache = TTLCache(maxsize=1000, ttl=600)

# Model for POST request data
class CacheItem(BaseModel):
    key: str
    data: dict

# Async POST method to store a JSON object in the cache
@app.post("/cache")
async def store_in_cache(item: CacheItem):
    cache[item.key] = item.data
    return 0

# Async GET method to retrieve a JSON object from the cache by key
@app.get("/cache")
async def retrieve_from_cache(key: Optional[str] = None):
    value = cache.get(key)
    if value is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    
    return value

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5566)