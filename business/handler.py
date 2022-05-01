import os

from loguru import logger
from watchdog.events import FileSystemEventHandler
from django.conf import settings


class logCreateHandler(FileSystemEventHandler):

    def on_created(self, event):
        logger.info('创建了新文件：{}', event.src_path)
        file_name_and_ext = os.path.split(event.src_path)[1]
        ext = os.path.splitext(file_name_and_ext)[1]
        if ext == '.log':
            settings.LOG_QUEUE.put(event.src_path)
        else:
            logger.info('不是日志文件：{}', event.src_path)
        logger.info('已将新文件放入日志队列：{}', settings.LOG_QUEUE)
