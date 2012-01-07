#!/usr/bin/env python
# --*-- encoding:utf-8 --*-- 

'''
Created on 2011-12-31
@author: fredzhu.com
'''

u'''
    程序基于https://webim.feixin.10086.cn/login.aspx发送消息.不记录密码
'''

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from fetion.models import FetionStatus,FETION_STATUS_ENUM,SMSQueue,TaskCron
from fetion.webim import FetionWebIM

import logging,random

logger = logging.getLogger('fetion')

FETION_URL = u"https://webim.feixin.10086.cn/WebIM/Login.aspx"

def login(request):
    u'''
    引导用户完成飞信登录
    '''
    webim = FetionWebIM(logger,request)
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        vcode = request.POST.get('vcode')
        if phone and password and vcode:
            #检查是否历史登陆用户
            status = FetionStatus.objects.filter(phone=phone)
            if status and len(status)>0 and status[0].status==FETION_STATUS_ENUM[0][0]:
                logger.info(u"已经登录,跳转查询界面:%s"%phone)
            code = webim.login(phone, password, vcode)
            if code == 200:
                if status and len(status)>0:
                    fs = status[0]
                    fs.status = FETION_STATUS_ENUM[0][0]
                    fs.save()
                else:
                    fs = FetionStatus()
                    fs.phone = phone
                    fs.status = FETION_STATUS_ENUM[0][0]
                    fs.security = "".join(random.sample(['1','2','3','4','5','6','7','8','9','0','a','b','c','d','e','f','g','h','i','j','k','l','m'],15))
                    fs.login_ip = request.META['REMOTE_ADDR']
                    fs.save()
                return HttpResponseRedirect('/query')
            elif code == 301:
                return HttpResponseRedirect('/query')
            elif code == 312:
                return HttpResponseRedirect('/error?error=验证码输入错误!')
            elif code == 321:
                return HttpResponseRedirect('/error?error=密码输入错误!')
            else:
                return HttpResponseRedirect('/error?error=未知错误!')
        else:
            return error(request,u"请完成填写登录数据")
    else:
        img_url = webim.get_vcode_img()#读验证码
    return render_to_response('fetion/login.html',{'img_url':img_url},context_instance=RequestContext(request))
        
        
def query(request):
    u'''
    查询费心状态
    '''
    data = {}
    if request.method == 'POST':
        phone = request.POST.get('phone')
        security = request.POST.get('security')
        if phone and security:
            st = FetionStatus.objects.filter(phone=phone,security=security)
            if st and len(st)>0:
                data.update({'status':st[0]})
            else:
                data.update({'error':u'未找到相关记录'})
        else:
            data.update({'error':u'请填写完整的字段'})
            
    return render_to_response('fetion/query.html',data,context_instance=RequestContext(request))

def stop(request):
    u'''下线
    '''
    pass

def error(request,error=u"出错啦!"):
    u'''
    出错给个提示
    '''
    error = request.GET.get('error',error)
    return render_to_response('fetion/error.html',{'error':error},context_instance=RequestContext(request))


##########队列

def list_queue(request):
    list = SMSQueue.objects.all()
    return render_to_response('fetion/queue_list.html',{'list':list},context_instance=RequestContext(request))


def add_queue(request):
    if request.method == "POST":
        receiver = request.POST.get('receiver',None)
        msg = request.POST.get('msg',None)
        if receiver and msg:
            queue = SMSQueue()
            queue.receiver = receiver
            queue.msg = msg
            queue.save()
    return HttpResponseRedirect('/queue/list')
    

def del_queue(request,id):
    queue = SMSQueue.objects.get(pk=id)
    if queue:
        queue.delete()
    return HttpResponseRedirect('/queue/list')

#任务
def list_task(request):
    list = TaskCron.objects.all()
    return render_to_response('fetion/task_list.html',{'list':list},context_instance=RequestContext(request))


def add_task(request):
    if request.method == "POST":
        phone = request.POST.get('phone',None)
        cron = request.POST.get('cron',None)
        receiver = request.POST.get('receiver',None)
        task_type = request.POST.get('task_type',None)
        if phone and cron and receiver and task_type:
            task = TaskCron()
            task.phone = phone
            task.cron = cron
            task.receiver = receiver
            task.task_type = task_type
            task.save()
    return HttpResponseRedirect('/task/list')


def del_task(request,id):
    task = TaskCron.objects.get(pk=id)
    if task:
        task.delete()
    return HttpResponseRedirect('/task/list')




