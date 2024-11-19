# app/configuration/logger.py

import os
import logging
from logging.handlers import RotatingFileHandler
import uuid
from .config import Config

class WorkerIdFilter(logging.Filter):
    def __init__(self, worker_id):
        super().__init__()
        self.worker_id = worker_id

    def filter(self, record):
        record.worker_id = self.worker_id
        return True

def setup_logger(worker_id=None):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [WorkerID: %(worker_id)s] - %(message)s')

    logs_dir = './logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    if Config.LOG_TO_FILE:
        file_handler = RotatingFileHandler(os.path.join(logs_dir, 'app.log'), maxBytes=5*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if Config.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if worker_id:
        logger.addFilter(WorkerIdFilter(worker_id))

    return logger


def get_logger(worker_id):    
    if worker_id:
        logger = setup_logger(worker_id)
    else:
        logger=setup_logger(str(uuid.uuid4()))
    return logger

