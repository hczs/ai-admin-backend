import os

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    # 测试
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test',  # 指定的数据库名
        'USER': 'root',  # 数据库登录的用户名
        # 'PASSWORD': 'Boco.123',  # 登录数据库的密码
        'PASSWORD': 'toor',  # 登录数据库的密码
        # 'HOST': '10.12.1.50',
        'HOST': '127.0.0.1',
        'PORT': '3306',
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
LIBCITY_PATH = 'D:\\PycharmProjects\\Bigscity-LibCity-master'
# 指标文件目录
EVALUATE_PATH_PREFIX = LIBCITY_PATH + os.sep + 'libcity\\cache\\'
EVALUATE_PATH_SUFFIX = '\\evaluate_cache\\'
# run_model.py脚本文件位置
RUN_MODEL_PATH = 'run_model.py'
# 激活libcity库虚拟环境命令
ACTIVE_VENV = 'D:\\PycharmProjects\\Bigscity-LibCity-master\\venv\\Scripts\\activate.bat'
# libcity的log目录
LOG_PATH = LIBCITY_PATH + os.sep + 'libcity' + os.sep + 'log' + os.sep

# 数据集文件上传路径
DATASET_PATH = LIBCITY_PATH + os.sep + 'raw_data\\'
# 任务参数json文件上传路径
TASK_PARAM_PATH = LIBCITY_PATH + os.sep

# 样例文件相关
# 数据集样例文件
DATASET_EXAMPLE_PATH = 'D:\\upload\\raw_data\\METR_LA.zip'
TASK_PARAM_EXAMPLE_PATH = 'D:\\upload\\param\\config.json'
# ADMIN_FRONT_HTML_PATH = "D:\\vscodework\\vue-admin-template-permission-control\\public\\"
ADMIN_FRONT_HTML_PATH = "D:\\vs_project\\ai_front\\ai-admin-front\\public\\"
# ADMIN_FRONT_HTML_PATH = "/usr/local/nginx/html/ai-admin/dist/"

