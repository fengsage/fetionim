#!/usr/bin/env python
# --*-- encoding:utf-8 --*-- 

from django.db import models

FETION_STATUS_ENUM = (
    ("ONLINE",u"正常"),
    ("OFF",u"关闭"),
)

class FetionStatus(models.Model):
    u'''
    维护飞信程序状态
    '''
    phone = models.CharField(u'手机号码(飞信登录账户)',max_length=20)
    security = models.CharField(u'安全码',max_length=50) #不会记录飞信密码,但登录成功后,会给用户一个安全码,以便随时查询飞信状态
    status = models.CharField(u'飞信状态',max_length=5,choices=FETION_STATUS_ENUM)
    login_ip = models.CharField(u'登录IP',max_length=20,blank=True, null=True)
    login_time = models.DateTimeField(u'登录时间',blank=True, null=True,auto_now_add=True)
    fail_time = models.DateTimeField(u'失效时间',blank=True, null=True,auto_now_add=True)
    remark = models.TextField(u'备注',blank=True, null=True)
    
class SMSQueue(models.Model):
    u'''短信队列
    '''
    msg = models.CharField(u'消息',max_length=350)
    receiver = models.CharField(u'接收人fetion id',max_length=20)
    add_time = models.DateTimeField(u'生成时间',blank=True, null=True,auto_now_add=True)

    class Meta:
        ordering = ['-add_time']
        
    @classmethod
    def addQueue(cls,task):
        queue = SMSQueue()
        queue.receiver = task.receiver
        queue.msg = task.get_msg()
        queue.save()    
    

TASK_ENUM = (
    ('weather',u'天气预报服务'),
)

from fetion.task import weather,CITY_LIST

class TaskCron(models.Model):
    u'''定时任务
    '''
    phone = models.CharField(u'手机号码(飞信登录账户)',max_length=20)
    cron = models.CharField(u'定时表达式',max_length=20)#简单的cron 只包含 [时 分]
    receiver = models.CharField(u'接收人fetion id',max_length=20)
    task_type = models.CharField(u'定时任务类型',max_length=20,choices=TASK_ENUM)
    
    def get_msg(self):
        if self.task_type == TASK_ENUM[0][0]:
            return weather(CITY_LIST[0][0])

