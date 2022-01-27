# coding=utf-8
import math

__all__ = ['pybyte']

import os
import subprocess

from django.http import FileResponse
import random
from loguru import logger


def pybyte(size, dot=2):
    size = float(size)
    # 位 比特 bit
    if 0 <= size < 1:
        human_size = str(round(size / 0.125, dot)) + 'b'
    # 字节 字节 Byte
    elif 1 <= size < 1024:
        human_size = str(round(size, dot)) + 'B'
    # 千字节 千字节 Kilo Byte
    elif math.pow(1024, 1) <= size < math.pow(1024, 2):
        human_size = str(round(size / math.pow(1024, 1), dot)) + 'KB'
    # 兆字节 兆 Mega Byte
    elif math.pow(1024, 2) <= size < math.pow(1024, 3):
        human_size = str(round(size / math.pow(1024, 2), dot)) + 'MB'
    # 吉字节 吉 Giga Byte
    elif math.pow(1024, 3) <= size < math.pow(1024, 4):
        human_size = str(round(size / math.pow(1024, 3), dot)) + 'GB'
    # 太字节 太 Tera Byte
    elif math.pow(1024, 4) <= size < math.pow(1024, 5):
        human_size = str(round(size / math.pow(1024, 4), dot)) + 'TB'
    # 拍字节 拍 Peta Byte
    elif math.pow(1024, 5) <= size < math.pow(1024, 6):
        human_size = str(round(size / math.pow(1024, 5), dot)) + 'PB'
    # 艾字节 艾 Exa Byte
    elif math.pow(1024, 6) <= size < math.pow(1024, 7):
        human_size = str(round(size / math.pow(1024, 6), dot)) + 'EB'
    # 泽它字节 泽 Zetta Byte
    elif math.pow(1024, 7) <= size < math.pow(1024, 8):
        human_size = str(round(size / math.pow(1024, 7), dot)) + 'ZB'
    # 尧它字节 尧 Yotta Byte
    elif math.pow(1024, 8) <= size < math.pow(1024, 9):
        human_size = str(round(size / math.pow(1024, 8), dot)) + 'YB'
    # 千亿亿亿字节 Bront Byte
    elif math.pow(1024, 9) <= size < math.pow(1024, 10):
        human_size = str(round(size / math.pow(1024, 9), dot)) + 'BB'
    # 百万亿亿亿字节 Dogga Byte
    elif math.pow(1024, 10) <= size < math.pow(1024, 11):
        human_size = str(round(size / math.pow(1024, 10), dot)) + 'NB'
    # 十亿亿亿亿字节 Dogga Byte
    elif math.pow(1024, 11) <= size < math.pow(1024, 12):
        human_size = str(round(size / math.pow(1024, 11), dot)) + 'DB'
    # 万亿亿亿亿字节 Corydon Byte
    elif math.pow(1024, 12) <= size:
        human_size = str(round(size / math.pow(1024, 12), dot)) + 'CB'
    # 负数
    else:
        raise ValueError('{}() takes number than or equal to 0, but less than 0 given.'.format(pybyte.__name__))
    return human_size


def execute_cmd(cmd):
    """
    执行命令行命令

    :param cmd: 命令内容
    :return: (status, output) status: 1 失败，0 成功
    """
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    # 判断命令是否执行成功
    status = p.returncode
    if status == 0:
        logger.info('[SUCCESS] %s' % cmd)
    else:
        logger.error('[ERROR] command: %s; message: %s' % (cmd, err))
        return status, err
    return status, output


def read_file_str(file_path):
    """
    将一个文件内容读取到字符串中，仅适用于小文件读取，编码格式：utf-8
    :param file_path: 文件具体路径
    :return: 文件内容字符串
    """
    # 判断路径文件存在
    if not os.path.isfile(file_path):
        raise TypeError(file_path + " does not exist")
    # 读取
    content = ''
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


def generate_download_file(file_path):
    """
    通用生成下载文件的方法
    仅限于下载文件接口，接口方法需要用 @renderer_classes((PassthroughRenderer,))

    :param file_path: 文件路径
    :return: 响应的response
    """
    response_file = FileResponse(open(file_path, 'rb'))
    response_file['content_type'] = "application/octet-stream"
    response_file['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
    return response_file


def get_code():
    """
    随机生成六位字符串
    """
    code = ''
    for _ in range(6):
        add = random.choice([random.randrange(10), chr(random.randrange(65, 91)), chr(random.randrange(97, 123))])
        code += str(add)
    return code


def parentheses_escape(raw_string):
    """
    对字符串中的圆括号 '(' ')' 进行转义替换，替换为：'\\(' '\\)'
    :param raw_string: 原始字符串
    :return: 转义后字符串
    """
    return raw_string.replace('(', '\\(').replace(')', '\\)')


def str_is_empty(raw_string):
    """
    判断字符串是否为空
    :param raw_string: 字符串
    :return: 是否为空
    """
    return raw_string is None or raw_string == ''


def query_type(data):
    for ch in data:
        if ch == '{':
            return "dict"
        if ch == '[':
            return "list"
    return "value"


feature_list = []  # 这里要保证有序，可以用有序字典，映射的时候可以用dict


def get_json_features(json_path):
    del feature_list[:]
    # 这里要保证有序，可以用有序字典，映射的时候可以用dict
    with open(json_path, 'r', encoding='UTF-8') as file_in:
        data_str = file_in.read()
    get_json_head(data_str)
    return feature_list


def get_json_head(data, loc=""):
    data = str(data)  # 将数据转换成字符串
    data_type = query_type(data)
    if data_type == "value":  # 如果是元素
        if loc[1:] not in feature_list:
            feature_list.append(loc[1:])
        return
    if data_type == "dict":  # 如果是字典
        data_dict = eval(data)
        for key in data_dict:
            get_json_head(data_dict[key], loc + "_" + key)
        return
    if data_type == "list":  # 如果是列表
        data_list = list(eval(data))
        for item in data_list:
            get_json_head(item, loc)
        return
