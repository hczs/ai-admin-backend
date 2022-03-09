import queue
from time import sleep
import os
from loguru import logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from django.test import TestCase


class logCreateHandler(FileSystemEventHandler):

    def on_created(self, event):
        logger.info('创建了新文件：{}', event.src_path)


# Create your tests here.
if __name__ == '__main__':
    file = 'd:\\hello\\text.txt'
    print(os.path.splitext(file))