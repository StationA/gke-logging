import logging

from gke_logging.pylogging import GKELoggingFormatter

def test_simple():
    test_formatter = GKELoggingFormatter()

    # Instantiate a LogRecord using the test fields below
    name = "my_logger"
    level = logging.INFO
    pathname = __file__
    lineno = 10
    msg = "This is a test log message"
    args = ()
    exc_info = None
    func = "my_function"
    sinfo = None

    record = logging.LogRecord(
        name,
        level,
        pathname,
        lineno,
        msg,
        args,
        exc_info,
        func,
        sinfo
    )

    formatted = test_formatter.format(record)
    assert formatted
