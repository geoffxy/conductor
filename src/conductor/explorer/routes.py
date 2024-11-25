from pydantic import BaseModel
from fastapi import FastAPI

app = FastAPI()


class Simple(BaseModel):
    message: str


@app.get("/api/1/hello")
def hello_world() -> Simple:
    return Simple(message="Hello, World!")
