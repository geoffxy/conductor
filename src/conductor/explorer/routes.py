import importlib.resources as pkg_resources

from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import conductor.explorer as explorer_module

app = FastAPI()


class Simple(BaseModel):
    message: str


@app.get("/api/1/hello")
def hello_world() -> Simple:
    return Simple(message="Hello, World!")


# Serve the static pages.
# Note that this should go last as a "catch all" route.
explorer_module_pkg = pkg_resources.files(explorer_module)
with pkg_resources.as_file(explorer_module_pkg) as explorer_module_path:
    app.mount(
        "/",
        StaticFiles(directory=explorer_module_path / "static", html=True),
        name="static",
    )
