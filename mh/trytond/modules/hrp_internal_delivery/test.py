# import cx_Oracle
#
# username = 'asdb5'
#
# userpwd = "asdb5"
#
# host = "172.18.45.166"
#
# port = 1521
#
# dbname = u"orcl"
#
# dsn = cx_Oracle.makedsn(host, port, service_name = dbname)
#
# print dsn
#
# try:
#
#     connection = cx_Oracle.connect(username, userpwd, dsn)
#
# except Exception,e:
#
#     print 'connection error:'+str(e.message).decode('gbk')
#
#     exit()
#
# cursor = connection.cursor()
#
#
#
#
#
#
#
#
# def test_func(*args):
#
#     try:
#
#         cursor.execute('select * from IR_TRANSLATION')
#
#         cursor.fetchall()
#
#         print cursor.rowcount
#
#     except Exception, e:
#
#         print str(e.message).decode('gbk')
#
#     print bool(cursor.rowcount)
#
#
#
# test_func(())
#
# connection.commit()
#
# connection.close()


from suds.client import Client

user_url = "http://hiep.heliteq.com:8082/WebService/SwapData/Purchase/PurchaseWebService.asmx" #这里是你的webservice访问地址
client = Client(user_url)#Client里面直接放访问的URL，可以生成一个w
print client
