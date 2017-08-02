# coding:utf-8
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
from django_redis import get_redis_connection

from analyst.models import Analyst
from mobileapp.models import AppUser



class ActionLog(models.Model):
    user = models.ForeignKey(User,blank=True, null=True)
    action = models.CharField(max_length=50)
    target_model = models.CharField(max_length=50,default="")
    target_id = models.IntegerField(default=0, null=False)
    description = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)
    memo = models.CharField(max_length=100, default="")

class JcsAction(object):
    action = ""
    target_model = None
    description = ""

    def makeLog(self, user, targetId, memo=""):
        log = ActionLog()
        log.user = user
        log.action = self.action
        # if it's model type, use __name__ attribute directly
        log.target_model = self.target_model.__name__ if hasattr(self.target_model, "__name__") else self.target_model.__class__.__name__
        log.target_id = targetId
        log.description = self.description
        log.memo = memo
        log.save()

class Bulletin(models.Model):
    poster = models.ForeignKey(User)
    title = models.CharField(max_length=60)
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

class Letter(models.Model):
    PROJECT_CNAME = {
        'M' : u'国语',
        'C' : u'粤语',
        'Z' : u'球秘',
        'J' : u'一起赢',
    }
    from_user = models.ForeignKey(User, related_name="fromuser_letter",null=True,blank=True)
    from_auser = models.ForeignKey(AppUser, related_name="fromauser_letter",null=True,blank=True)
    to_user = models.ForeignKey(User, related_name="touser_letter",null=True,blank=True)
    to_auser = models.ForeignKey(AppUser, related_name="toauser_letter",null=True,blank=True)
    to_analyst = models.ForeignKey(Analyst,null=True,blank=True,)
    unread = models.BooleanField(default=True)
    content = models.CharField(max_length=1018)
    invisible = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    project = models.CharField(max_length=32, default='M')

class BannedLettor(models.Model):
    auser = models.ForeignKey(AppUser,db_index=True,null=True)
    analyst = models.ForeignKey(Analyst,db_index=True,null=True)

    class Meta:
        unique_together = ("auser", "analyst")

class LetterHide(models.Model):
    user = models.ForeignKey(AppUser, db_column='userid')
    author = models.ForeignKey(Analyst, db_column='authorid')

    class Meta:
        db_table = 'letter_hide'

def make_actionlog(user,acton_name,target,descripton):
    log = ActionLog()
    log.user = user
    log.action = acton_name
    log.target= target
    log.description = descripton
    log.save()

def letter_post(letter):
    con = get_redis_connection("default")
    topic_name = 'letter_post' if letter.project == 'M' else 'letter_post_cantonese'
    con.publish(topic_name, str(letter.from_user.analyst.id)+"_"+str(letter.to_auser.userid))

class SystemConfig(models.Model):
    config_type = models.CharField(max_length=20, help_text=u'玩法分类 [61足球竞彩 62足球外盘 63足球滚球 66篮球竞彩 67篮球外盘 68篮球滚球]')
    config_key = models.CharField(max_length=255, help_text=u'玩法标识 [10-20]竞彩足球 [20-60]外盘足球 [60-100]滚球足球 [110-120]竞彩篮球 [120-160]外盘篮球 [160-200]滚球篮球')
    config_value = models.CharField(max_length=2000)
    create_time = models.DateTimeField(auto_now_add=True)
    create_by_id = models.IntegerField(default=1)
    last_update_time = models.DateTimeField(auto_now=True)
    out_id = models.CharField(null = True, blank= True, max_length=255 )

    class Meta:
        db_table = 'system_config'

class PushTaskResult(models.Model):
    push_article_id = models.IntegerField()
    user_id = models.IntegerField()
    token = models.CharField(max_length=128)
    cdate = models.DateTimeField(auto_now_add=True)
    push_type = models.IntegerField()
    author_id = models.IntegerField()

    class Meta:
        db_table = 'jcs_push_task_result'
        managed = True

class BmsLog(models.Model):
    # operator_id = models.IntegerField()
    operator = models.ForeignKey(User, related_name="operator_id",null=True,blank=True)
    even_name = models.CharField(max_length=255)
    even_message = models.CharField(max_length=255)
    cdate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bms_log'
        managed = True

def get_system_config(config_key, config_type='system_config'):
    configs = SystemConfig.objects.filter(config_type=config_type, config_key=config_key)
    if configs.count() > 0:
        return configs.values_list('config_value', flat=True)[0] or ''
    return ''

