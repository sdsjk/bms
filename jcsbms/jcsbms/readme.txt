-1: 安装aptitude
sudo apt-get install aptitude
0、 安装pip，并升级到最新版
sudo aptitude install python-pip
sudo pip install --upgrade pip
1、Django setup :https://www.djangoproject.com/download/----pip安装:
sudo pip install --upgrade Django==1.9.5
2、psycopg2-2.5 :
sudo aptitude install libpq-dev
sudo aptitude install python-dev
sudo pip install psycopg2
#http://initd.org/psycopg/download/----aptitude
#如果按照失败，可以用
apt-get install python-psycopg2
3、Ubuntu本地uwsgi需要Python plugin：
sudo apt-get install uwsgi uwsgi-plugin-python
4、Pytyon的lib管理优点：系统级管理，可以自动升级，缺点：有些库的安装很麻烦，特别涉及到C编译的---所以涉及C编译的最好直接用windows安装包
5、Django-Ueditor：https://github.com/zhangfisher/DjangoUeditor/ 开源+自定制，无需安装
6、Pillow：http://effbot.org/downloads/#Imaging ----先下载,编译安装需要先装python-dev和gcc,
#如果需要jpeg support,方法-1：http://blog.csdn.net/dipolar/article/details/20059357 |||| http://jj.isgeek.net/2011/09/install-pil-with-jpeg-support-on-ubuntu-oneiric-64bits/
#    jpeg support解决方法：
#https://github.com/thumbor/thumbor/issues/226
#-----------------------------------------------------
#The reason of this error were missing dependencies.
#I'm using Ubuntu 14.04 x64, but it should also work with 12.04. Try:

sudo apt-get install python-dev libjpeg-dev libfreetype6-dev zlib1g-dev

#Once you install these packages, you have to symlink the three image libraries into /usr/lib with:

sudo ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/
sudo ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/
sudo ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/
sudo ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/

#Now you are able to install pillow:
sudo pip install pillow
--------------------------------------------------------
7、lXMl for htmlfilter :http://lxml.de/index.html ----aptitude/pip安装需要
sudo pip install libxslt-dev libxml2-dev
8、 安装mongoengine
sudo pip install mongoengine
9、 安装django-redis
sudo pip install django-redis
10、chown 项目目录 user to 给uwsgi或者nginx，或者加上全访问权限
11、安装jpush
sudo pip install jpush
12、安装日期
sudo pip install python-dateutil
13、安装pyquery
sudo pip install pyquery
14、安装blinker----Signals机制的依赖项
sudo pip install blinker
15、安装csselect
sudo pip install cssselect
16、安装python-lxml
sudo apt-get install python-lxml
17、安装rest
sudo pip install djangorestframework
18、安装xlrd
sudo pip install xlrd
19、安装定时任务
sudo pip install apscheduler
============================================
上线计划大概:
1、安装新的依赖
2、修改配置
3



