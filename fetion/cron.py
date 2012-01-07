#!/usr/bin/env python
# --*-- encoding:utf-8 --*-- 

import datetime

def cron_check(datetime,cron):
    u'''cron表达式
    语法：
        m[1-24] s[0-59]
    参数:
        *    通配任意
    '''
    def _validate(c,s,type):
        u'''验证下
        '''
        if c == "*":
            return True
        
        c = int(c)
        s = int(s)
        
        return {
            's':lambda : (c==s and c>=0 and c<=23),
            'm':lambda : (c==s and c>=0 and c<=59)
        }[type]()
        
    hour,minute = cron.split(" ")
    
    return _validate(hour,datetime.hour,"s") & _validate(minute,datetime.minute,"m")


if __name__=="__main__":
    print cron_check(datetime.datetime.now(),"17 09")
