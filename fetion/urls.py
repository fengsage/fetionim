#!/usr/bin/env python
# --*-- encoding:utf-8 --*-- 


from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('fetion.views',
     url(r'^login$', 'login'),
     url(r'^query$', 'query'),
     url(r'^error$', 'error'),
     url(r'^stop$', 'stop'),
     
     url(r'^queue/list$', 'list_queue'),
     url(r'^queue/add$', 'add_queue'),
     url(r'^queue/del/(\d+)$', 'del_queue'),
     
     url(r'^task/list$', 'list_task'),
     url(r'^task/add$', 'add_task'),
     url(r'^task/del/(\d+)$', 'del_task'),
)

from fetion.models import FetionStatus,FETION_STATUS_ENUM
print u'init fetion status'
FetionStatus.objects.all().update(status=FETION_STATUS_ENUM[1][0])