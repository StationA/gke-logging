import json
import logging

from gke_logging.pylogging import GKELoggingFormatter


def test_simple(caplog):
    caplog.set_level(logging.INFO)
    caplog.handler.setFormatter(GKELoggingFormatter(default_labels={"test": "test"}))
    logging.info("This is a test log message")
    assert caplog.record_tuples == [
        ("root", logging.INFO, "This is a test log message")
    ]
    # also check the default labels are set from the instantiation of the formatter
    labels = json.loads(caplog.text)["logging.googleapis.com/labels"]
    assert labels["test"] == "test"
