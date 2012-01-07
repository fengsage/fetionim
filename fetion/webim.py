#!/usr/bin/env python
# --*-- encoding:utf-8 --*-- 


'''
Created on 2011-12-31
@author: fredzhu.com
'''
import threading,urllib,urllib2,time,datetime
import json,os,random

from fetion.cron import cron_check
from fetion.models import FetionStatus,FETION_STATUS_ENUM,SMSQueue,TaskCron

DOWNLOAD_ABST_DIR = u'static/code_imgs/%s'%(time.strftime('%Y/%m', time.localtime(time.time())))


class FetionWebIM():
    u'''飞信IM协议
    '''
    
    def __init__(self,logger,request):
        self.logger = logger
        self.request = request
        
    def login(self,phone,password,vcode):
        u'''登陆飞信
        '''
        POST = {
            "UserName":phone,
            "Pwd":password,
            "OnlineStatus":0,
            "Ccp":vcode
        }
        HEAD = {  
            'Host':'webim.feixin.10086.cn',
            'Cookie':self.request.session['ccpsession'],  
            'Referer':'https://webim.feixin.10086.cn/login.aspx',  
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
        }  
        req = urllib2.Request(u"https://webim.feixin.10086.cn/WebIM/Login.aspx", urllib.urlencode(POST), HEAD)
        resp = urllib2.urlopen(req)
        if resp.getcode()!=200:
            return
        rc = json.loads(resp.read())
        if rc['rc'] == 200:
            self.logger.info(u"%s 登录成功!"%phone)
            #登录成功,读取cookie信息
            info = resp.info()
            webim_sessionid = info['set-cookie'].split('webim_sessionid=')[1].split(';')[0]
            self.request.session['webim_sessionid'] = webim_sessionid
            self.request.session['phone'] = phone
            self.logger.info(u"获取会话ID:%s"%webim_sessionid)
            #开启心跳线程,保持会话...
            h_thread = FetionHeartThread(self.logger,self.request)
            h_thread.start()
            #轮循短信队列
            q_thread = FetionQueueThread(self.logger,self.request)
            q_thread.start()
            #开启任务线程,定时执行任务
            t_thread = FetionTaskThread(self.logger,self.request)
            t_thread.start()
            return 200
            
        elif rc['rc'] == 312:
            self.logger.warn(u"%s 验证码输入错误!"%phone)
            return 312
        elif rc['rc'] == 321:
            self.logger.warn(u"%s 密码输入错误!"%phone)
            return 321
        else:
            self.logger.warn(u"%s 未知错误!"%phone)  
            return 400
        

    def send_msg(self,to,msg,session_id):
        u'''发送短信
        '''
        HEAD = {  
            'Host':'webim.feixin.10086.cn',
            'Referer':'https://webim.feixin.10086.cn/login.aspx',  
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        POST = {
            "Message":msg.encode('utf-8'),
            "Receivers":to,
            "UserName":"1045701458",
            "ssid":session_id
        }
        
        req = urllib2.Request(u"http://webim.feixin.10086.cn/content/WebIM/SendSMS.aspx?Version=9", urllib.urlencode(POST) ,HEAD)
        resp = urllib2.urlopen(req)
        #返回信息
        rc = json.loads(resp.read())
        
        if rc['rc'] == 200:
            #发送成功
            self.logger.info(u"发给[%s]发送成功!"%to)
            return True
        return False

    def get_vcode_img(self,down_path=DOWNLOAD_ABST_DIR):
        u'''获取图片验证码
        '''
        u = urllib2.urlopen("https://webim.feixin.10086.cn/WebIM/GetPicCode.aspx?Type=ccpsession")
        #读取cookie
        if u.getcode()==200:
            #先读取头信息
            header = u.info()
            #读取cookie
            cookie = header['set-cookie'].split(';')[0]  
            self.request.session['ccpsession'] = cookie
            #下载图片
            if os.path.isdir(down_path) == False:
                os.makedirs(down_path)
            file_path = u'%s/vcode_%s.jpeg'%(down_path,"".join(random.sample(['1','2','3','4','5','6','7','8','9','0'], 5)))
            downloaded_image = file(file_path.encode('utf-8'), "wb")
            try:
                while True:
                    buf = u.read(65536)
                    if len(buf) == 0:
                        break
                    downloaded_image.write(buf)
                downloaded_image.close()
                u.close()
                self.logger.debug('download webim vcode image success')
                return file_path
            except:
                self.logger.debug('download webim vcode image failture')
            #返回图片路径
            return "/"+downloaded_image

    def get_contact_list(self,request):
        u'''获取用户联系人列表
        '''
        POST = {
            'ssid':request.session['webim_sessionid']
        }
        if len(self.user_list)==0:
            req = urllib2.Request(u"http://webim.feixin.10086.cn/WebIM/GetContactList.aspx?Version=1",urllib.urlencode(POST))
            resp = urllib2.urlopen(req)
            if resp.getcode()==200:
                return
            data = json.loads(resp.read())
            if data and data['rc'] == 200:
                #TODO 
                pass
            resp.close()

class FetionTaskThread(threading.Thread):
    u'''飞信任务线程
    负责定时把Task的任务放入短信队列里
    '''
    def __init__(self,logger,request):
        threading.Thread.__init__(self) 
        self.logger = logger
        self.phone = request.session['phone']
        self.webim_sessionid = request.session['webim_sessionid']
    
    def run(self):
        run = True
        while run:
            self.logger.debug('轮循task......')
            list = TaskCron.objects.filter(phone=self.phone)
            for task in list:
                cron = task.cron
                if self.__check(cron):
                    self.logger.debug(u"cron[%s]符合条件......"%cron)
                    SMSQueue.addQueue(task)
            time.sleep(59)#略大约55秒,防止1分钟内存在2次触发
    
    def __check(self,cron):
        u'''检测cron是否可以运行
        '''
        return cron_check(datetime.datetime.now(), cron)
        
class FetionQueueThread(threading.Thread):
    u'''短信队列线程
    '''
    def __init__(self,logger,request):
        threading.Thread.__init__(self) 
        self.logger = logger
        self.phone = request.session['phone']
        self.webim_sessionid = request.session['webim_sessionid']
        self.webim = FetionWebIM(logger,request)

    def run(self):
        run = True
        while run:
            run = self.__roll_queue()#轮循队列
            time.sleep(10)        

    def __roll_queue(self):
        u'''轮循队列
        '''
        self.logger.debug(u'轮循短信队列......')
        queues = SMSQueue.objects.all()
        if queues and len(queues)>0:
            for q in queues:
                receiver = q.receiver
                msg = q.msg
                try:
                    flag = self.webim.send_msg(receiver,msg, self.webim_sessionid)
                    if flag:
                        q.delete()#完成删除
                    self.logger.info(u'发送短信成功 to=%s'%receiver)
                except:
                    self.logger.error(u'发送短信失败! to=%s'%receiver)
        return True
    
class FetionHeartThread(threading.Thread):
    u'''保持飞信年轻健康的心跳
    '''
    
    def __init__(self,logger,request):
        threading.Thread.__init__(self) 
        self.logger = logger
        self.phone = request.session['phone']
        self.webim_sessionid = request.session['webim_sessionid']

    def run(self):
        run = True
        index = 0
        while run:
            run = self.__jump(index)#心跳
            index = index + 1
            time.sleep(1)


    def __jump(self,index=0):
        u'''一次心跳
        '''
        POST = {
            'ssid':self.webim_sessionid
        }
        req = urllib2.Request(u"http://webim.feixin.10086.cn/WebIM/GetConnect.aspx?Version=%s"%index,urllib.urlencode(POST))
        resp = urllib2.urlopen(req)
        data = json.loads(resp.read())
        self.logger.debug(u"心跳线程:%s"%data)
        #出状况了
        if resp.getcode()!=200:
            return False
        if data['rc'] == 200:
            self.logger.debug(data)
            for d in data['rv']:
                if d['DataType'] == 4:
                    #中断线程
                    self.logger.error(u"别处用户登录!心跳停止")
                    FetionStatus.objects.filter(phone=self.phone).update(status=FETION_STATUS_ENUM[1][0])
                    return False
        resp.close()
        #设计有点问题
        return True
    

