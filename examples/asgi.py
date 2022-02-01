import logging

from fastapi import FastAPI
from gke_logging import GKELoggingFormatter
from gke_logging.asgi import GKELoggingMiddleware

app = FastAPI()
app.add_middleware(GKELoggingMiddleware)


LOGGER = logging.getLogger()
h = logging.StreamHandler()
h.setFormatter(GKELoggingFormatter())
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(h)


@app.get("/")
def get_it() -> str:
    LOGGER.info("Got a request")
    LOGGER.warning("OH NO")
    return "OK"
