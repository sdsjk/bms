# coding:utf-8
"""
Django settings for jcsbms project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '65=g@5r_(m442vjexd!^ji5+oa1njke7-x3sy-hzkr77v6ubw7'

# SECURITY WARNING: don't run with debug turned on in production!

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jcs',
    'DjangoUeditor',
    'jauth',
    'analyst',
    'article',
    'lottery',
    'mobileapp',
    'ask',
    'measured',
    'rest_framework',
    'restapi',
    'thiredparty',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',

)

ROOT_URLCONF = 'jcsbms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'jcs.context_processors.Site_Constants',
                'django.core.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'jcsbms.wsgi.application'




#Session Cache:
#redis session key pattern: ":1:django.contrib.sessions.cache*"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', 'English'),
    ('zh', '简体中文'),
)


TIME_ZONE = 'Asia/Bangkok'
LOCALE_PATHS = (
os.path.join(BASE_DIR, 'locale'),
)
#TIME_ZONE = "GMT+8"
# LOCALE_PATHS = [BASE_DIR]

USE_I18N = True

USE_L10N = True



USE_TZ = True 

DATE_FORMAT = 'Y-m-d H:i'

#URL fro Login
LOGIN_URL = '/yonghu/denglu/'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR,"static")

MEDIA_ROOT = os.path.join(BASE_DIR,"upload")
# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR,"assets"),
    os.path.join(BASE_DIR,"upload"),
)

# email settings

EMAIL_HOST = 'smtp.mxhichina.com'
EMAIL_PORT = '25'
EMAIL_HOST_USER = 'no-reply@xycentury.com'
EMAIL_HOST_PASSWORD = 'CEh!#sd^2Oib'
EMAIL_USE_TLS = False

SERVER_EMAIL = "no-reply@xycentury.com"
ADMINS = [('zhuertao', 'zhuertao@xycentury.com'), ('niumengxin', 'niumengxin@xycentury.com')]
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s [%(filename)s %(funcName)s] %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'console':{
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file':{
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename':'/tmp/django.log',
            'when': 'D',
            'backupCount':7,
            'formatter': 'simple'

        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console','mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

ALIDAYU_APPKEY = "23573860"
ALIDAYU_SECRET = "ce141578392fe85017eba63ba8e7ce9c"
#wangfenchao, zhuertao, niumengxin
ALARM_CELLPHONES = ["15321375192"]

#jpush settings:

jmessage_admin = {"username": "jcs_bms_admin_dev", "password": "jcsadmin"}

ALS_DATA_APIS = {
    "user_last_active_time": "http://als.winwin.in.th/data_api/user_last_active_time",
    "cheat_monitor_data": "http://als.winwin.in.th/data_api/common/?reportId=cheat_monitor_data"
}


EDITORS_CONTACT_INFO = [
    {"email":"zhangqi@heiniulicai.com",      "phone":"13810611905"},
    {"email":"yangdongrong@heiniulicai.com", "phone":"13311484859"},
    {"email":"zhaoshijie@xycentury.com",   "phone":"13651280204"},
    {"email":"zhangqian@xycentury.com",    "phone":"18500225095"},
    {"email":"makun@xycentury.com",        "phone":"13810215783"},
    {"email":"houquanyu@xycentury.com",    "phone":"18345184725"}
]

import socket
if socket.gethostname() == 'Cloud-jcs-bms-01':
    #PRODUCT
    DEBUG = False
    ALLOWED_HOSTS = ["bms.jingcaishuo.net","www.jingcaishuo.com","10.141.117.180","10.141.90.214", "123.207.169.19"]

    # Database
    # https://docs.djangoproject.com/en/1.8/ref/settings/#databases
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'jbmsdb',  # Or path to database file if using sqlite3.
            'USER': 'jbmsuser',  # Not used with sqlite3
            'PASSWORD': 'jb765321',  # Not used with sqlite3
            'HOST': '10.141.109.230',  # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '5432',  # Set to empty string for default. Not used with sqlite3.
        }
    }

    # Cache
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://:UYS8wDysc9FC3hJWZJbsU3XE98Jj@10.141.90.1:6379/0",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }

    REDIS_HOST = '10.141.90.1'
    REDIS_PASSOWRD = 'UYS8wDysc9FC3hJWZJbsU3XE98Jj'

    jmessage_admin = {"username": "jcs_bms_admin", "password": "jcsadmin"}
    # 小秘书的django帐号id
    XIAOMISHU_AUTH_USER_IDS = [251, 8928, 8929, 8930, 8931, 8932, 9104, 9220]
    YUEYU_XIAOMISHU_AUTH_USER_IDS = [9104]
    YQY_XIAOMISHU_AUTH_USER_IDS = [9220]

    YUEYU_JPUSH_KEY = '3fe7080207d0740b03e00c70'
    YUEYU_JPUSH_MASTER = '5cb53d7c4c6050cab00fafc0'  
    PUSH_SERVICE_URL = 'http://10.141.70.77:8078/sendMessage'
    PUSH_SERVICE_URL_QM = 'http://10.141.70.77:8079/sendMessage'
    SERVER_HOST = 'http://bms.winwin.in.th'
    jpush_app_key = "c2f3adaeced410ee9cf8feca"
    jpush_master_secret = "e8aaa4505b45fb7a97cf1408"
    jpush_app_key_qiumi = "1aed88a774ceb7f871a92e69"
    jpush_master_secret_qiumi = "7c234c455a59ac9ca8c88265"
    jpush_app_key_yiqiying = '37c02e503629307b64e2ad71'
    jpush_master_secret_yiqiying = '8d44b56052882df96cc1be29'
    hpush_appid_yiqiying = '10879841'
    hpush_master_secret_yiqiying = '1db24174830a3946b887216054f60e86'
    xpush_master_secret_yiqiying = 'Ft952fgONu1MCBa4w8v/Zg=='
    AUTHOR_JPUSH_KEY = 'c464bcc7d386324e1efb5096'
    AUTHOR_JPUSH_MASTER = 'd54d84cbcc38eaab8fc9ee6c'
    #合作专区文章寄存老师账号
    ZHUANQU_AUTHOR_ID = 414
    #能够发合作专区文章的老师账号
    ZHUANQU_AUTH_EDITOR_IDS = [15, 417]
    #走地标签id
    ZOUDI_ID = 25
    #网球标签id
    TENNIS_ID = 32
    #文章消息监控国语app的token(android,ios)
    TOKEN_M = ['170976fa8a825f90e0e','1517bfd3f7cab6a34d0']
    #退出时调用的url
    LOGIN_OUT_URL = 'http://houtai.jingcaishuo.net/selfLogOut/logOutAjax'

else:
    #DEV
    DEBUG = True
    ALLOWED_HOSTS = ['*']

    # Database
    # https://docs.djangoproject.com/en/1.8/ref/settings/#databases
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'jbmsdb',  # Or path to database file if using sqlite3.
            'USER': 'jbmsuser',  # Not used with sqlite3
            'PASSWORD': 'jb765321',  # Not used with sqlite3
            'HOST': '192.168.88.66',  # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '5432',  # Set to empty string for default. Not used with sqlite3.
        }
    }
    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.postgresql_psycopg2',
    #         'NAME': 'jbmsdb',  # Or path to database file if using sqlite3.
    #         'USER': 'jbmsuser',  # Not used with sqlite3
    #         'PASSWORD': 'jbu5421',  # Not used with sqlite3
    #         'HOST': '123.57.59.76',  # Set to empty string for localhost. Not used with sqlite3.
    #         'PORT': '5432',  # Set to empty string for default. Not used with sqlite3.
    #     }
    # }

    # Cache
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://:UYS8wDysc9FC3hJWZJbsU3XE98Jj@192.168.88.77:6379/0",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }

    REDIS_HOST = '192.168.88.77'
    REDIS_PASSOWRD = 'UYS8wDysc9FC3hJWZJbsU3XE98Jj'
    # CACHES = {
    #     "default": {
    #         "BACKEND": "django_redis.cache.RedisCache",
    #         "LOCATION": "redis://:UYS8wDysc9FC3hJWZJbsU3XE98Jj@123.57.59.76:6379/0",
    #         "OPTIONS": {
    #             "CLIENT_CLASS": "django_redis.client.DefaultClient",
    #         }
    #     }
    # }
    # REDIS_HOST = '123.57.59.76'
    # REDIS_PASSOWRD = 'UYS8wDysc9FC3hJWZJbsU3XE98Jj'

    jmessage_admin = {"username": "jcs_bms_admin_dev", "password": "jcsadmin"}
    # 小秘书的django帐号id
    XIAOMISHU_AUTH_USER_IDS = [251, 8928, 8929, 8930, 8931, 8932, 9008, 9397, 9393]
    YUEYU_XIAOMISHU_AUTH_USER_IDS = [9008]
    YQY_XIAOMISHU_AUTH_USER_IDS = [9397, 9393]

    YUEYU_JPUSH_KEY = '9e025be787a5ed2f2317096a'
    YUEYU_JPUSH_MASTER = 'd16d342f7191b3197141cf58'
    PUSH_SERVICE_URL = 'http://192.168.88.95:8078/sendMessage'
    PUSH_SERVICE_URL_QM = 'http://60.205.151.90:8078/sendMessage'
    SERVER_HOST = 'http://bms.winwin.in.th'
    jpush_app_key = "6f6ce659f9f3a165a6ae88a4"
    jpush_master_secret = "e0253e6dd25ab296e034a821"
    jpush_app_key_qiumi = "1aed88a774ceb7f871a92e69"
    jpush_master_secret_qiumi = "7c234c455a59ac9ca8c88265"
    jpush_app_key_yiqiying = '37c02e503629307b64e2ad71'
    jpush_master_secret_yiqiying = '8d44b56052882df96cc1be29'
    hpush_appid_yiqiying = '10879841'
    hpush_master_secret_yiqiying = '1db24174830a3946b887216054f60e86'
    xpush_master_secret_yiqiying = 'Ft952fgONu1MCBa4w8v/Zg=='
    AUTHOR_JPUSH_KEY = 'c464bcc7d386324e1efb5096'
    AUTHOR_JPUSH_MASTER = 'd54d84cbcc38eaab8fc9ee6c'

    #合作专区文章寄存老师账号
    ZHUANQU_AUTHOR_ID = 419
    #能够发合作专区文章的老师账号,analyst_id
    ZHUANQU_AUTH_EDITOR_IDS = [15,]
    # 走地标签id
    ZOUDI_ID = 61
    #网球标签id
    TENNIS_ID = 65
    #文章消息监控国语app的token(android,ios)
    TOKEN_M = ['160a3797c8090e5e789','171976fa8a8ce755875']
    #退出时调用的url
    LOGIN_OUT_URL = 'http://qa-houtai.jingcaishuo.com:9080/selfLogOut/logOutAjax'

