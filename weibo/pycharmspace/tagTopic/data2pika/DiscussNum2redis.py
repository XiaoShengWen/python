#-*- coding:utf-8 _*-  
""" 
--------------------------------------------------------------------
@function: 将话题讨论数写入pika
@time: 2017-12-12
author:baoquan3 
@version: 
@modify: 
--------------------------------------------------------------------
"""
import sys
import redis
import hashlib
import time

defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

port = 25153
# client = redis.Redis(host = "pkm25153.eos.grid.sina.com.cn", port = port)

pool = redis.ConnectionPool(host = "pkm25153.eos.grid.sina.com.cn", port=port ,db = 0, decode_responses=True)
r = redis.Redis(connection_pool=pool)
pipe = r.pipeline(transaction=False) # 创建一个管道
name = "mention"


def file2redis2():
    totalNum, errNum = 0, 0
    maxTopic, maxNum = None, 0
    topicList = []

    # for line in open("D://data//topicNum.dat"):
    for line in sys.stdin:
        totalNum += 1
        #每缓冲 n 次向数据库中写一次
        if totalNum % 1000 == 0:
            updatePika(topicList)
            currentTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            print currentTime, "----",totalNum,"-----",line.strip()
        lineArr = line.strip().split("\t")
        if len(lineArr) == 2:
            key = getKey(lineArr[0])
            val = int(lineArr[1])
            pipe.hget(name = name, key = key)
            topicList.append((key, val))
            tmpNum = int(val)
            if tmpNum > maxNum:
                maxNum = tmpNum
                maxTopic = lineArr[0]
                print "{0}\t{1}".format(maxTopic, maxNum)
        else:
            errNum += 1
            print totalNum ,errNum, " : ", line.strip()
    # 将缓存数据，写入数据库
    if topicList:
        updatePika(topicList)

    print "totalNum:{0},errNum:{1}".format(totalNum, errNum)
    print "maxTopic, maxNum", maxTopic, maxNum
    print "sucess !"

def updatePika(topicList):
    getList = pipe.execute()
    getSet = set(getList)
    # 与pika数据库中原有值相加
    if len(getSet) == 1 and None in getSet:     # 数据中没有返回值
        for key, val in topicList:
            pipe.hset(name=name, key=key,value=val)
    else:                                       # 有话题讨论数=需要相加的情况
        for i in range(0, len(getList)):
            realtimeDiscussNum = getList[i]
            key, val = topicList[i]
            if realtimeDiscussNum:
                val += int(realtimeDiscussNum)
            pipe.hset(name=name, key=key, value=val)
    # 将修改值写入pika
    result = pipe.execute()

    # 查看是否写成功
    # print getList
    # for key, val in topicList:
    #     pipe.hget(name=name,key=key)
    # result = pipe.execute()
    # print result

def strQ2B(ustring):
    """全角转半角"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 12288:                              #全角空格直接转换
            inside_code = 32
        elif (inside_code >= 65281 and inside_code <= 65374): #全角字符（除空格）根据关系转化
            inside_code -= 65248
        rstring += unichr(inside_code)
    return rstring


def getKey(topic):
    topicNew = strQ2B(unicode(topic.lower()))
    md5=hashlib.md5(topicNew.encode('utf-8')).hexdigest()
    key = "c_" + md5
    return key


def writeSuccessTest():
    name = "mention"
    topic = "西语新闻"
    key = getKey(topic)
    print key

    pool = redis.ConnectionPool(host = "pkm25153.eos.grid.sina.com.cn", port=port ,db = 0, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    pipe = r.pipeline(transaction=False) # 创建一个管道

    key = getKey("1004小编刷新闻")
    pipe.hget(name = name, key = key)
    # key = getKey("测试话题2")
    # pipe.hget(name = name, key = key)
    # result = pipe.execute()
    # print result
    # key = getKey("测试话题1")
    # pipe.hset(name=name,key=key, value=2)
    # key = getKey("测试话题2")
    # pipe.hset(name=name,key=key, value=3)
    result = pipe.execute()
    print result


if __name__ == "__main__":
    writeSuccessTest()
    # file2redis2()