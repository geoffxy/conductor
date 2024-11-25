import importlib.resources as pkg_resources

from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import conductor.explorer.static as explorer_app

app = FastAPI()


class Simple(BaseModel):
    message: str


@app.get("/api/1/hello")
def hello_world() -> Simple:
    return Simple(message="Hello, World!")


# Serve the static pages.
# Note that this should go last as a "catch all" route.
static_files = pkg_resources.files(explorer_app)
with pkg_resources.as_file(static_files) as static_dir:
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
