# A ={1:'X',2:'B',3:'Z'}
# B ={1:'X',2:'B',3:'Z'}
# a = 1
# b = 2
# Keys =  A.keys()
# if a in Keys:
#     ppp = A[a]
# if b in Keys:
#     ggg = A[b]
# print ppp + gggi
#

# a = '1'
# gg = a.zfill(5)
# print gg
# a = 'AB22
# 017050001'
# print a[0:2].isalpha()
# get_numbr = input('>>>')
# def num(n):
#     if n == 0:
#         return 0
#     elif n == 1:
#         return 1
#     else:
#         result = num(n-1) + num(n-2)
# #         return result
# # for i in range(get_numbr):
# #     print num(i)
#
#
#

# import os
# path="/Users/myair/Desktop/hrp/trytond/modules/hrp_shipment"
# global totalcount
# totalcount =0
# def cfile (path):
#    allfiles = os.listdir(path)
#    for file in allfiles:
#        child = os.path.join(path,file)
#        if os.path.isdir(child):
#            cfile(child)
#        else:
#            filename,fileext= os.path.splitext(child)
#            print(fileext)
#            #file type need to calculate
#            if fileext in ['cfg','.conf','.out','.java', '.jsp', '.html', '.htm', '.xml', '.sql', '.js', '.ftl', '.css','.groovy','.py'] :
#                countf = len(open(child,'rU').readlines())
#                global totalcount
#                totalcount=totalcount+countf;
#                print(child)
#                print(countf)
# cfile(path)
# print(totalcount)

# import time
# timeStamp = 1381419600
# timeArray = time.localtime(timeStamp)
# otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
# date = time.strftime('%m%d', time.localtime())
# print date

# A =  [{'return_quantity': 5.0, 'product': 2,'number':2}, {'return_quantity': 20.0, 'product': 2,'number':''}, {'return_quantity': 44.0, 'product': 3,'number':''}, {'return_quantity': 180.0, 'product': 6,'number':''}, {'return_quantity': 9.0, 'product': 7,'number':''}, {'return_quantity': 280.0, 'product': 10,'number':''}, {'return_quantity': 0.2, 'product': 10,'number':''}, {'return_quantity': 18.0, 'product': 11,'number':''}]
# B = sorted(A ,key = lambda x:(x['number']),reverse=False)
# print B


# for i in range(3):
#     print i
# a = [1,2,3]
# b = [1,2,3,4]
#
# if set(a).issubset(set(b)):
#     print True
# else:
#     print False

# li = [1,2,3,4]
# print reduce(lambda x, y: x * y, li)
# print filter(lambda x: x % 2 == 0, li)
#
#
#
# from Tkinter import *
# import tkMessageBox
#
# class Application(Frame):
#     def __init__(self, master=None):
#         Frame.__init__(self, master)
#         self.pack()
#         self.createWidgets()
#
#     def createWidgets(self):
#         self.nameInput = Entry(self)
#         self.nameInput.pack()
#         self.alertButton = Button(self, text='Hello', command=self.hello)
#         self.alertButton.pack()
#
#     def hello(self):
#         name = self.nameInput.get() or 'world'
#         tkMessageBox.showinfo('Message', 'Hello, %s' % name)
#
# app = Application()
#
# app.master.title('Hello World')
#
# app.mainloop()
#coding:utf-8

# class FooParent(object):
#     def __init__(self):
#         self.parent = 'I\'m the parent.'
#         print 'Parent'
#
#     def bar(self, message):
#         print message, 'from Parent'
#
#
# class FooChild(FooParent):
#     def __init__(self):
#         super(FooChild, self).__init__()
#         print 'Child'
#
#     def bar(self, message):
#         super(FooChild, self).bar(message)
#         print 'Child bar fuction'
#         print self.parent
#
#
# if __name__ == '__main__':
#     fooChild = FooChild()
#     fooChild.bar('HelloWorld')

#
# def f(x):
#     return x*x
# print map(f,[1,2,3])

#
# def fn(x,y):
#     return x * 10 + y
# print reduce(fn,[1,2,3,4])
#
#
# def num(x):
#     return x.title()
# a = ['adam', 'LISA', 'barT']
# print map(num,a)
#
#
#
# def now_time():
#     return '2017-5-22'
# now = now_time
# print now()
# print now.__name__
#coding:utf-8





# dict_list = [
#         {'return_quantity':1.0, 'product':3},
#         {'return_quantity':10.0, 'product':10},
#         {'return_quantity':240.0, 'product':10},
#         {'return_quantity':1.0, 'product':11},
#         {'return_quantity':1.0, 'product':30},
#         {'return_quantity':1.0, 'product':30},
#         {'return_quantity':1.0, 'product':144},
#         {'return_quantity':1.0, 'product':152},
# ]
#
# product_id = []
# for each in dict_list:
#     product_id.append(each['product'])
# a = {}
# for i in product_id:
#      if product_id.count(i)>1:
#          a[i] = product_id.count(i)
# key_value = a.keys()
#
# productid = []
# ggg = []
# for each_ in dict_list:
#     if each_['product'] in key_value:
#         dict = {}
#         dict[each_['product']] = each_['return_quantity']
#         productid.append(dict)
#         ggg.append(each_)
#
# expected = [ l for l in dict_list if l not in ggg ]
#
# for pro in key_value:
#     number = 0
#     dict_ = {}
#     for i in productid:
#         try:
#             number += i[pro]
#         except:
#             pass
#     dict_['product'] = pro
#     dict_['return_quantity'] = number
#     expected.append(dict_)
# print expected

# strf = u'X2017070034'
# print strf[0:2].isalpha()

# A0 = dict(zip(('a','b','c','d','e'),(1,2,3,4,5)))
# print A0
# for i in A0:
#     print i

# num = [1,2,3]
# max = [2,4]
# lists = []
# for i in max:
#     nums = 0
#     for e in num:
#         if e <= i:
#             nums += 1
#     lists.append(nums)
# print lists


# hhh = '12345678'
# ggg = len(hhh)
# kkk = ggg % 2
# if kkk == 0:
#     print hhh[(ggg/2)-1],hhh[ggg/2]
# else:
#     print hhh[(ggg/2)]
#
# a = 'abcdcbahhhh'
# for i in range(len(a)):
#     if i == 0 and i == len(a)-1:
#         pass
#     else:
#         num = 0
#         for e in range(1,len(a)/2):
#             if a[i-e] == a[i+e]:
#                 num += 1
#             else:
#                 pass
#         print num
#
#
# lis = [1, 2, 3, 4,8,9,10]
# a = 8
# num = 0
# for i in lis:
#     num += 1
#     if i == a:
#         break
# print num
#

# -*- coding: utf-8 -*-


# -*- coding: utf-8 -*-

#
# from time import strftime, localtime
# from datetime import timedelta, date
# import calendar
#
# year = strftime("%Y", localtime())
# mon = strftime("%m", localtime())
# day = strftime("%d", localtime())
# hour = strftime("%H", localtime())
# min = strftime("%M", localtime())
# sec = strftime("%S", localtime())
#
#
# def today():
#
#     return date.today()
#
#
# def todaystr():
#
#     return year + mon + day
#
#
# def datetime():
#
#     return strftime("%Y-%m-%d %H:%M:%S", localtime())
#
#
# def datetimestr():
#
#     return year + mon + day + hour + min + sec
#
#
# def get_day_of_day(n=0):
#
#     if (n < 0):
#         n = abs(n)
#         return date.today() - timedelta(days=n)
#     else:
#         return date.today() + timedelta(days=n)
#
#
# def get_days_of_month(year, mon):
#
#     return calendar.monthrange(year, mon)[1]
#
#
# def get_firstday_of_month(year, mon):
#
#     days = "01"
#     if (int(mon) < 10):
#         mon = "0" + str(int(mon))
#     arr = (year, mon, days)
#     return "-".join("%s" % i for i in arr)
#
#
# def get_lastday_of_month(year, mon):
#
#     days = calendar.monthrange(year, mon)[1]
#     mon = addzero(mon)
#     arr = (year, mon, days)
#     return "-".join("%s" % i for i in arr)
#
#
# def get_firstday_month(n=0):
#
#     (y, m, d) = getyearandmonth(n)
#     d = "01"
#     arr = (y, m, d)
#     return "-".join("%s" % i for i in arr)
#
#
# def get_lastday_month(n=0):
#
#     return "-".join("%s" % i for i in getyearandmonth(n))
#
#
# def getyearandmonth(n=0):
#
#     thisyear = int(year)
#     thismon = int(mon)
#     totalmon = thismon + n
#     if (n >= 0):
#         if (totalmon <= 12):
#             days = str(get_days_of_month(thisyear, totalmon))
#             totalmon = addzero(totalmon)
#             return (year, totalmon, days)
#         else:
#             i = totalmon / 12
#             j = totalmon % 12
#             if (j == 0):
#                 i -= 1
#                 j = 12
#             thisyear += i
#             days = str(get_days_of_month(thisyear, j))
#             j = addzero(j)
#             return (str(thisyear), str(j), days)
#     else:
#         if ((totalmon > 0) and (totalmon < 12)):
#             days = str(get_days_of_month(thisyear, totalmon))
#             totalmon = addzero(totalmon)
#             return (year, totalmon, days)
#         else:
#             i = totalmon / 12
#             j = totalmon % 12
#             if (j == 0):
#                 i -= 1
#                 j = 12
#             thisyear += i
#             days = str(get_days_of_month(thisyear, j))
#             j = addzero(j)
#             return (str(thisyear), str(j), days)
#
#
# def addzero(n):
#
#     nabs = abs(int(n))
#     if (nabs < 10):
#         return "0" + str(nabs)
#     else:
#         return nabs
#
#
# def get_today_month(n=0):
#
#     (y, m, d) = getyearandmonth(n)
#     arr = (y, m, d)
#     if (int(day) < int(d)):
#         arr = (y, m, day)
#     return "-".join("%s" % i for i in arr)
#
#
# if __name__ == "__main__":
#     print today()
#     print todaystr()
#     print datetime()
#     print datetimestr()
#     print get_day_of_day(20)
#     print get_day_of_day(-3)
#     print get_today_month(-3)
#     print get_today_month(3)
#




#
# import time
# nowtime = time.time()
# date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
#
# date = date.split(' ')
# day = date[0]
# Array = time.strptime(day, "%Y-%m-%d")
# daytime = int(time.mktime(Array))
# dayhours = nowtime-daytime
# print dayhours
# print daytime
#
# timeStamp = 1381419600
# timeArray = time.localtime(timeStamp)
# otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
# print timeArray
# print otherStyleTime
# print otherStyleTime
# import time
# nowtime = time.time()
# print nowtime
# date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
# date = date.split(' ')
# day = date[0]
# Array = time.strptime(day, "%Y-%m-%d")
# print date
# print Array
# daytime = int(time.mktime(Array))
# dayhours = nowtime-daytime
# print dayhours
# import time
# a = "2013-10-10"
# b = "2013-10-11"
#
# timeStamp = int(time.mktime(time.strptime(a, "%Y-%m-%d")))
#
# fff = time.strftime("%Y-%m-%d", time.localtime(timeStamp))
# print type(fff)


# import datetime
# timeStamp = 1381419600
# dateArray = datetime.datetime.utcfromtimestamp(timeStamp)
# ggg = dateArray.date()
# print type(ggg)
# print type(dateArray)
# jjj = datetime.datetime.now()
# print jjj.date()
# dateaa = datetime.date.today()
# print dateaa
# print type(dateaa)




