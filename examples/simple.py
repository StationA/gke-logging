import logging

from gke_logging import GKELoggingFormatter


LOGGER = logging.getLogger(__name__)
h = logging.StreamHandler()
h.setFormatter(GKELoggingFormatter())
LOGGER.addHandler(h)
LOGGER.setLevel(logging.INFO)

LOGGER.info("Look at me! I can haz GKE structured logging!")
