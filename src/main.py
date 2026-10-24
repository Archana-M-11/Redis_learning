
import time
import redis
from fastapi import FastAPI, HTTPException
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError
from redis.exceptions import RedisError

app = FastAPI(title="Redis and MongoDB Learning")

# Redis connection: FastAPI runs directly on your computer.
r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
    socket_connect_timeout=3,
)

# MongoDB connection
mongo_client = AsyncMongoClient(
    "mongodb://localhost:27017"
)
mongo_db = mongo_client["chai_redis"]
collection = mongo_db["messages"]


@app.get("/")
def home():
    return {"message": "FastAPI is running"}


@app.get("/redis")
def test_redis():
    try:
        start = time.perf_counter()

        r.set("message", "Hello from Redis")
        message = r.get("message")

        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "database": "Redis",
            "message": message,
            "elapsed_ms": round(elapsed_ms, 3),
        }
    except RedisError as exc:
        raise HTTPException(
            status_code=503,
            detail="Redis is unavailable",
        ) from exc


@app.get("/mongo")
async def test_mongo():
    try:
        start = time.perf_counter()
        await collection.update_one(
            {"_id": "greeting"},
            {"$set": {"message": "Hello from MongoDB"}},
            upsert=True,
        )
        document = await collection.find_one(
            {"_id": "greeting"}
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "database": "MongoDB",
            "message": document["message"],
            "elapsed_ms": round(elapsed_ms, 3),
        }
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable",
        ) from exc


@app.get("/health/redis")
def redis_health():
    try:
        return {"redis": "connected" if r.ping() else "disconnected"}
    except RedisError as exc:
        raise HTTPException(
            status_code=503,
            detail="Redis is unavailable",
        ) from exc


@app.get("/health/mongo")
async def mongo_health():
    try:
        await mongo_client.admin.command("ping")
        return {"mongo": "connected"}
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable",
        ) from exc


@app.on_event("shutdown")
async def close_mongo():
    await mongo_client.close()
