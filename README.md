# gke-logging

[![PyPI version](https://badge.fury.io/py/gke-logging.svg)](https://badge.fury.io/py/gke-logging)

Utilities for interacting with logging facilities in GKE workloads

## Installation

### Requirements

- Python 3.7+
- [Poetry](https://python-poetry.org/) (for development only)

### Install from PyPI (recommended)

```
pip install gke-logging
```

### Installing from Github

```
pip install git+https://github.com/StationA/gke-logging.git#egg=gke-logging
```

### Installing from source

```
git clone https://github.com/StationA/gke-logging.git
cd gke-logging
poetry install
```

## Usage

### `gke_logging.GKELoggingFormatter`

One of the core components is the `GKELoggingFormatter`, which is an implementation of the built-in
`logging.Formatter` protocol that translates a `logging.LogRecord` into a JSON format that GKE's
logging infrastructure can understand. At a minimum, this enables any software running on GKE to
integrate structured logging simply by applying this formatter for your loggers, e.g.:

```python
import logging

from gke_logging import GKELoggingFormatter


LOGGER = logging.getLogger(__name__)
h = logging.StreamHandler()
h.setFormatter(GKELoggingFormatter())
LOGGER.addHandler(h)
LOGGER.setLevel(logging.INFO)


# ...

LOGGER.info("Look at me! I can haz GKE structured logging!")
# Prints out: {"time": "2022-01-13T23:22:26.336686+00:00", "severity": "INFO", "message": "Look at me! I can haz GKE structured logging!", "logging.googleapis.com/sourceLocation": {"file": "test_log.py", "line": "14", "function": "<module>"}, "logging.googleapis.com/labels": {}}
```

Furthermore, this formatter allows you to set app-level metadata to be sent along with each log
message, which is useful in order to better organize collected log data:

```python
# ...
h.setFormatter(
    GKELoggingFormatter(default_labels=dict(app_id="my-cool-app", version="0.1.0"))
)
# ...
```

Also the formatter also allows you to add HTTP metadata to any logs that occur during the course of
a request. This enhances logs that are emitted during request-handling logic in APIs with additional
data. This functionality is primarily utilized in the included `GKELoggingMiddleware` in order to
provide basic access logs.

### `gke_logging.asgi.GKELoggingMiddleware`

`gke_logging.asgi.GKELoggingMiddleware` is an ASGI middleware that emits basic access logs in
"common log format", with a default behavior that integrates with the `GKELoggingFormatter` to write
the access logs in a format that GKE's logging infrastructure better understands. By implementing
per the ASGI spec, this means it can work with any ASGI-compatible server, including FastAPI,
starlette, and ASGI implementations:

```python
from fastapi import FastAPI
from gke_logging.asgi import GKELoggingMiddleware

app = FastAPI()
app.add_middleware(GKELoggingMiddleware)

@app.get("/")
def get_it() -> str:
    return "OK"
```

Additionally, because this middleware integrates with `gke_logging.context` bindings, it enables any
logger used during the course of handling a request to emit logs that also contain request-time
data, e.g. request URL, user-agent, response latency, etc.

```python
import logging

from fastapi import FastAPI
from gke_logging import GKELoggingFormatter
from gke_logging.asgi import GKELoggingMiddleware

app = FastAPI()
app.add_middleware(GKELoggingMiddleware)


root_logger = logging.getLogger()
h = logging.StreamHandler()
h.setFormatter(GKELoggingFormatter())
root_logger.setLevel(logging.INFO)
root_logger.addHandler(h)


@app.get("/")
def get_it() -> str:
    # Any log records created during request-handling will be enriched with other HTTP request data
    root_logger.info("TEST")
    return "OK"
```

### `gke_logging.context`

In order to control additional metadata labels for log records that correspond to one logical
operation, e.g. an HTTP request, a batch job operation, etc., you should use the helper functions
exported in `gke_logging.context`:

```python
import logging

from contextvars import copy_context

from gke_logging import GKELoggingFormatter
from gke_logging.context import set_labels


LOGGER = logging.getLogger(__name__)
h = logging.StreamHandler()
h.setFormatter(GKELoggingFormatter())
LOGGER.addHandler(h)
LOGGER.setLevel(logging.INFO)

# ...


def run_job(job_id: str):
    set_labels(job_id=job_id)
    LOGGER.info("TEST")


ctx = copy_context()
for i in range(10):
    ctx.run(run_job, f"{i + 1}")
```

Because `ContextVar`s bind natively to Python's `asyncio`, you can use these same helper
functions within asynchronous tasks in a similar fashion.

### Additional examples

Additional usage examples can be found in [examples/](examples/)

## Contributing

When contributing to this repository, please follow the steps below:

1. Fork the repository
1. Submit your patch in one commit, or a series of well-defined commits
1. Submit your pull request and make sure you reference the issue you are addressing
