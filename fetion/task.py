#!/usr/bin/env python
# --*-- encoding:utf-8 --*-- 



CITY_LIST = (
    ('101210301',u'嘉兴'),
    ('101020100',u'上海')
)
def weather(city):
    u'''天气预报
    '''
    import urllib2,json
    
    API = u'http://m.weather.com.cn/data/%s.html'%city
    resp = urllib2.urlopen(API)
    if resp.getcode()!=200:
        return
    rc = json.loads(resp.read())
    
    info = rc['weatherinfo']
    msg = u'%s,今天天气%s,温度%s,明天天气%s,温度%s'%(info['city'],info['weather1'],info['temp1'],info['weather2'],info['temp2'])
    
    return msg

if __name__=="__main__":
    print weather(CITY_LIST[0][0])





