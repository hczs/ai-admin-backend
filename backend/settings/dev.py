import os

from .base import *



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []
# ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

DATABASES = {
    # 测试
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django',  # 指定的数据库名
        'USER': 'root',  # 数据库登录的用户名
        'HOST': '127.0.0.1',
        'PASSWORD': '123456',
        'PORT': '3366',
    }
}

# 跨域设置
# 单个配置
CORS_ORIGIN_WHITELIST = (
    'http://127.0.0.1:9528',
    'http://localhost:9528',
)

# 允许携带cookie
CORS_ALLOW_CREDENTIALS = True

# libcity库程序相关
# libcity程序目录
# LIBCITY_PATH = 'E:\\工作内容\\python\\项目\\Bigscity-LibCity-master\\Bigscity-LibCity-master'
LIBCITY_PATH = 'D:\\pyproject\\bushu\\Bigscity-LibCity'
# 指标文件目录
EVALUATE_PATH_PREFIX = LIBCITY_PATH + os.sep + 'libcity\\cache\\'
EVALUATE_PATH_SUFFIX = '\\evaluate_cache\\'
# run_model.py脚本文件名称
RUN_MODEL_PATH = 'run_model.py'
# 激活libcity库虚拟环境命令
# ACTIVE_VENV = 'E:\\工作内容\\python\\项目\\Bigscity-LibCity-master\\Bigscity-LibCity-master\\venv\\Scripts\\activate.bat'
ACTIVE_VENV = 'D:\\pyproject\\bushu\\Bigscity-LibCity\\venv\\Scripts\\activate.bat'
# libcity的log目录
LOG_PATH = LIBCITY_PATH + os.sep + 'libcity' + os.sep + 'log' + os.sep
# libcity的 任务-模型 对应关系配置信息目录
TASK_MODEL_PATH = LIBCITY_PATH + os.sep + 'libcity' + os.sep + 'config' + os.sep + 'model'

# 数据集文件上传路径
DATASET_PATH = LIBCITY_PATH + os.sep + 'raw_data' + os.sep
# 任务参数json文件上传路径
TASK_PARAM_PATH = LIBCITY_PATH + os.sep

# 样例文件相关
# 数据集样例文件
DATASET_EXAMPLE_PATH = 'D:\\upload\\raw_data\\METR_LA.zip'
TASK_PARAM_EXAMPLE_PATH = 'D:\\upload\\param\\config.json'
ADMIN_FRONT_HTML_PATH = "D:\\vscodework\\bushu\\vue-admin-template-permission-control\\public\\"
