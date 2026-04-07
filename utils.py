import logging

def setup_logger():
    logging.basicConfig(
        filename="audit.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

def log(msg):
    logging.info(msg)
