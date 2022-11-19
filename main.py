from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from diffusers import StableDiffusionPipeline
from dotenv import dotenv_values
from typing import List
from uuid import uuid4

import torch

from generator import generate_username

env = dotenv_values(".env")
TOKEN = env.get('TOKEN')

pipeline = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", revision="fp16", torch_dtype=torch.float16, use_auth_token=TOKEN)
pipeline.to("cuda")
pipeline.safety_checker = lambda images, **kwargs: (images, [False] * len(images))

app: FastAPI = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

onlineCount: int = 0

class SocketManager:
    def __init__(self):
        self.active_connections: List[tuple[WebSocket, str]] = []

    async def connect(self, websocket: WebSocket, user: str):
        await websocket.accept()
        self.active_connections.append((websocket, user))

    def disconnect(self, websocket: WebSocket, user: str):
        self.active_connections.remove((websocket, user))

    async def broadcast(self, data):
        for connection in self.active_connections:
            await connection[0].send_json(data)    

manager = SocketManager()

@app.websocket("/api/chat")
async def chat(websocket: WebSocket):
    global onlineCount
    sender = websocket.cookies.get("X-Authorization")
    if sender:
        await manager.connect(websocket, sender)
        response = {
            "sender": sender,
            "message": "connected"
        }
        onlineCount += 1
        await manager.broadcast(response)
        await manager.broadcast({"online": onlineCount})
        try:
            while True:
                data = await websocket.receive_json()
                await manager.broadcast({"lock" : True})
                filename = str(uuid4())
                image = pipeline(data.get('message')).get("images")[0]
                image.save(f"./static/images/{filename}.png")
                await manager.broadcast({"unlock" : True})
                await manager.broadcast({
                    "sender": sender,
                    "image": filename,
                    "prompt": data.get('message')
                })
        except WebSocketDisconnect:
            manager.disconnect(websocket, sender)
            onlineCount -= 1
            response['message'] = "left"
            await manager.broadcast(response)
            await manager.broadcast({"online": onlineCount})

@app.get("/api/user")
def get_user(request: Request):
    return request.cookies.get("X-Authorization")

@app.post("/api/register")
def register_user(response: Response):
    response.set_cookie(key="X-Authorization", value=generate_username(), httponly=True)

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
