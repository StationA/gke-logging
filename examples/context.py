import logging

from contextvars import copy_context

from gke_logging import GKELoggingFormatter
from gke_logging.context import set_labels


LOGGER = logging.getLogger(__name__)
h = logging.StreamHandler()
h.setFormatter(GKELoggingFormatter())
LOGGER.addHandler(h)
LOGGER.setLevel(logging.INFO)


def run_job(job_id: str):
    set_labels(job_id=job_id)
    LOGGER.info("Started job")
    # ... do some more work ...
    LOGGER.info("Job finished!")


ctx = copy_context()
for i in range(10):
    ctx.run(run_job, f"{i + 1}")
