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

debug = False;

class Connection:
    def __init__(self, socket: WebSocket, username: str):
        self.socket = socket
        self.username = username

    def __eq__(self, other) -> bool:
        return self.username == other.username

    async def send_json(self, data):
        await self.socket.send_json(data)

class ConnectionManager:
    def __init__(self):
        self.connections: List[Connection] = []

    async def connect(self, socket: WebSocket, user: str):
        await socket.accept()
        self.connections.append(Connection(socket, user))

    def disconnect(self, socket: WebSocket, user: str):
        self.connections.remove(Connection(socket, user))

    def onlineCount(self) -> int:
        return len(self.connections)

    async def broadcast(self, data):
        [await connection.send_json(data) for connection in self.connections] 
    
    async def send(self, data, user):
        [await connection.send_json(data) for connection in [i for i in self.connections if i.username == user]]


connectionManager = ConnectionManager()

@app.websocket("/api/chat")
async def chat(socket: WebSocket):
    sender = generate_username()
    if sender:
        await connectionManager.connect(socket, sender)
        response = {
            "sender": sender,
            "message": "connected"
        }
        await connectionManager.send({"update": sender}, sender)
        await connectionManager.broadcast(response)
        await connectionManager.broadcast({"online": connectionManager.onlineCount()})
        try:
            while True:
                data = await socket.receive_json()
                await connectionManager.broadcast({"lock" : True})
                filename = str(uuid4())
                image = pipeline(data.get('message')).get("images")[0]
                image.save(f"./static/images/{filename}.png")
                await connectionManager.broadcast({"unlock" : True})
                await connectionManager.broadcast({
                    "sender": sender,
                    "image": filename,
                    "prompt": data.get('message') if debug else ""
                })
        except WebSocketDisconnect:
            connectionManager.disconnect(socket, sender)
            response['message'] = "left"
            await connectionManager.broadcast(response)
            await connectionManager.broadcast({"online": connectionManager.onlineCount()})

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
