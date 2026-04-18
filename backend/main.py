import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, posts, volunteers, matching, relay, chatbot, notifications, shelter, admin
from app.websocket import router as ws_router

app = FastAPI(title="PawRelay API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(posts.router, prefix="/posts", tags=["posts"])
app.include_router(volunteers.router, prefix="/volunteers", tags=["volunteers"])
app.include_router(matching.router, prefix="/matching", tags=["matching"])
app.include_router(relay.router, prefix="/relay", tags=["relay"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(shelter.router, prefix="/shelter", tags=["shelter"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(ws_router.router, tags=["websocket"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
