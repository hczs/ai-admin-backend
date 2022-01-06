from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    # 测试
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django',  # 指定的数据库名
        'USER': 'root',  # 数据库登录的用户名
        'PASSWORD': 'toor',  # 登录数据库的密码
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

# 数据集文件上传路径
DATASET_PATH = 'D:\\upload\\raw_data\\'
# 任务参数json文件上传路径
TASK_PARAM_PATH = 'D:\\upload\\param\\'
# run_model.py脚本文件位置
RUN_MODEL_PATH = 'D:\\PycharmProjects\\Bigscity-LibCity\\run_model.py'
# 监控任务执行的线程，多长时间获取一次任务执行线程的状态（秒）暂时不用
MONITORING_FREQUENCY = 1

# 样例文件相关
# 数据集样例文件
DATASET_EXAMPLE_PATH = 'D:\\upload\\raw_data\\METR_LA.zip'
TASK_PARAM_EXAMPLE_PATH = 'D:\\upload\\param\\config.json'
ADMIN_FRONT_HTML_PATH = "D:/vs_project/ai_front/ai-admin-front/public/"
# ADMIN_FRONT_HTML_PATH = "/usr/local/nginx/html/ai-admin/dist/"
