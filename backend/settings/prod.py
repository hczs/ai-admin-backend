import os

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['49.233.159.81']

# 数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django',  # 指定的数据库名
        'USER': 'root',  # 数据库登录的用户名
        'PASSWORD': 'Boco.123',  # 登录数据库的密码
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# 跨域设置
# 单个配置
CORS_ORIGIN_WHITELIST = (
    'http://49.233.159.81:26352',
)

# 允许携带cookie
CORS_ALLOW_CREDENTIALS = True

# 允许所有主机跨域
# CORS_ORIGIN_ALLOW_ALL = True

# libcity库程序相关
# libcity程序目录
LIBCITY_PATH = '/root/Bigscity-LibCity'
# 指标文件目录
EVALUATE_PATH_PREFIX = LIBCITY_PATH + os.sep + 'libcity' + os.sep + 'cache'
EVALUATE_PATH_SUFFIX = os.sep + 'evaluate_cache' + os.sep
# run_model.py脚本文件位置
RUN_MODEL_PATH = 'run_model.py'
# 激活libcity库虚拟环境命令
ACTIVE_VENV = 'source /root/Bigscity-LibCity/libcity_venv/bin/activate'
# libcity的log目录
LOG_PATH = LIBCITY_PATH + os.sep + 'libcity' + os.sep + 'log' + os.sep

# 数据集文件上传路径
DATASET_PATH = LIBCITY_PATH + os.sep + 'raw_data' + os.sep
# 任务参数json文件上传路径
TASK_PARAM_PATH = LIBCITY_PATH + os.sep

# 样例文件相关
# 数据集样例文件
DATASET_EXAMPLE_PATH = '/usr/local/ai/sample/METR_LA.zip'
TASK_PARAM_EXAMPLE_PATH = '/usr/local/ai/sample/config.json'
ADMIN_FRONT_HTML_PATH = "/usr/local/nginx/html/ai-admin/dist/"
