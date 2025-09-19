import logging

class Logger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('notion.log', mode='w')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)