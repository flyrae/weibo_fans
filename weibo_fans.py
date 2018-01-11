# -*- coding: UTF-8 -*-

import os
import re
import requests
import sys
import traceback
from datetime import datetime
from datetime import timedelta
from lxml import etree
import jieba
import pyprind
import base64
import random
from bs4 import BeautifulSoup

from jieba import analyse
# 引入TextRank关键词抽取接口
textrank = analyse.textrank
import time
import math

import matplotlib.pyplot as plt
import networkx as nx
import pylab as pl

jieba.load_userdict("user_dict.txt")
td_idf=jieba.analyse.extract_tags

cookie ={}  # 将your cookie替换成自己的cookie  https://www.cnblogs.com/EmilySun/p/6158147.html
proxy = {'http':'http://61.135.217.7:80',
        'http':'http://123.152.76.119:8118'}
def get_fans_uids(user_id):
    # proxy = {'http':'106.46.136.112:808'}
    uids=[]
    url = 'https://weibo.cn/' + str(user_id) + '/fans'
    print url
    try:
        html = requests.get(url, cookies=cookie,proxies=proxy).content
        #print html
        soup = BeautifulSoup(html, 'html.parser')
        num_page = soup.find('input', {'name': 'mp'})['value']
        print num_page
        fans_uids = []
    except TypeError as e:
        return ['0']

    pbar = pyprind.ProgBar(
        int(num_page),
        title='开始下载%s的粉丝uid' % str(user_id),
        bar_char='█'
    )
    #num_page=2
    for i in range(int(num_page)):
        time.sleep(1)
        page_url = 'https://weibo.cn/' + str(user_id) + '/fans?page=' + str(i + 1)
        print page_url
        html = requests.get(page_url, cookies=cookie,proxies=proxy).content
        soup = BeautifulSoup(html, 'html.parser')
        try:
            datas = soup.find('input', {'name': 'uidList'})['value']
            print datas
            fans_uids.extend(datas.split(','))
        except TypeError as e:
            pass
        pbar.update()
    print len(fans_uids)
    return fans_uids

def get_username(user_id): 
    user_id = int(user_id)
    username=""
    try:
        url = "https://weibo.cn/%d/info" % (user_id)
        print url
        html = requests.get(url, cookies=cookie,proxies=proxy).content
        selector = etree.HTML(html)
        username = selector.xpath("//title/text()")[0]
        username = username[:-3]
        print u"用户名: " + username
    except Exception, e:
        print "Error: ", e
        traceback.print_exc()
    return username

def get_usernames(ids):
    uid_names=[]
    for i in ids:
        uid_names.append([i,get_username(int(i))])
    return uid_names


def get_weibo_info(uid,filter_=0):
    u_weibocontent=[]
    contents=""
    try:
        url = "https://weibo.cn/u/%d?filter=%d&page=1" % (
            uid, filter_)
        html = requests.get(url, cookies=cookie).content
        selector = etree.HTML(html)
        if selector.xpath("//input[@name='mp']") == []:
            page_num = 1
        else:
            page_num = (int)(selector.xpath(
                "//input[@name='mp']")[0].attrib["value"])
        pattern = r"\d+\.?\d*"
        if page_num >10:
            page_num=10
        for page in range(1, page_num + 1):
            print page
            time_ = random.random()*10
            time_ = time_%3
            time.sleep(time_)
            url2 = "https://weibo.cn/u/%d?filter=%d&page=%d" % (
                uid, filter_, page)
            html2 = requests.get(url2, cookies=cookie).content
            selector2 = etree.HTML(html2)
            info = selector2.xpath("//div[@class='c']")
            if len(info) > 3:
                for i in range(0, len(info) - 2):
                    # 微博内容
                    str_t = info[i].xpath("div/span[@class='ctt']")
                    weibo_content = str_t[0].xpath("string(.)").encode(
                        sys.stdout.encoding, "ignore").decode(
                        sys.stdout.encoding)
                    u_weibocontent.append(weibo_content)
                    # contents = contents + weibo_content
#                     print weibo_content
    except Exception, e:
        print "Error: ", e
        traceback.print_exc()
    return u_weibocontent

def get_data(file_path):
    data=""
    with open(file_path,'r') as f:
        data = f.read()
    return data

def get_key_list(uid,w_ids):
    key_list=[]
    stop_words=[u'微博',u'doge',u'全文',u'大家',u'我们',u'感谢',u'粉丝',u'转发',u'微博',u'这条',u'关注',u'10',u'##','cn','cc','...','http','......','video','flag',u'哈哈哈',u'允悲',u'每天',u'一个',u'但是',u'拜拜',u'棒棒',u'二哈',u'哈哈哈哈',u'2017',u'2018',u'1246', u'年度', u'加油' ,u'生日快乐']
    for i in w_ids:
        print i
        tmp=[]
        tmp.append(i)
        content =get_data('weibo_data\\'+str(i)+".txt")
        es=td_idf(content,topK=30)
        for e in es:
            if e not in stop_words:
                tmp.append(e)
        key_list.append(tmp)
    tmp=[]
    i=uid
    tmp.append(i)
    content =get_data('weibo_data\\'+str(i)+".txt")
    es=td_idf(content,topK=30)
    for e in es:
        if e not in stop_words:
            tmp.append(e)    
    key_list.append(tmp)
    return key_list


def get_weights_edge(key_list):
    yt_key = key_list[len(key_list)-1]
    yt_id = yt_key[0]
    yt_keys=yt_key[1:]
    weights=[]
    yt_set = set(yt_keys)
    for k in key_list:
        i_id = k[0]
        i_keys = k[1:]
        comms = list(yt_set.intersection(set(i_keys)))
        tmp=[yt_id,i_id]
        tmp.append(len(comms))
        tmp.extend(comms)
        weights.append(tmp)
    return weights

def get_pdicts(uid):
    with open(r'fans_names_'+str(uid)+'.txt','r') as f:
        persons=f.read()
    pdict = persons.split('\n')
    pdicts={}
    for pd in pdict:
        t = pd.split('\t')
        pdicts[t[0]] = t[1]
    return pdicts

def get_valid_edges_nodes(weights,pdicts):
    w2=[]
    for w in weights:
        if w[2] > 0:
            tmp=[]
            #print w
            tmp.append(pdicts[str(w[1])])
            tmp.extend(w[3:])
            w2.append(tmp)
    p_w=[]
    for w in w2:
        for j in w[1:]:
            p_w.append([w[0],j])
    person_nodes=[]
    word_nodes=[]
    for p in p_w:
        person_nodes.append(p[0].decode('utf-8'))
        word_nodes.append(p[1])
    edges=[]
    for i in p_w:
        edges.append((i[0].decode('utf-8'),i[1]))
    return person_nodes,word_nodes,edges

def save_fans2txt(uid,fans_uids):
    with open('fans_'+str(uid)+'.txt','w') as f:
        f.write(str(uid))
        f.write(u'\n')
        for i in fans_uids[:-1]:
            f.write(i)
            f.write(u'\n')
        f.write(fans_uids[-1])

def save_fans_names2txt(uid,uid_ns):
    with open('fans_names_'+str(uid)+'.txt','w') as f:
        f.write(str(uid))
        f.write(u'\t')
        f.write(get_username(uid).encode('utf-8'))
        f.write(u'\n')
        for i in uid_ns[:-1]:
            f.write(i[0])
            f.write(u'\t')
            f.write(i[1].encode('utf-8'))
            f.write(u'\n')
        f.write(uid_ns[-1][0])
        f.write(u'\t')
        f.write(uid_ns[-1][1].encode('utf-8'))

def save_fans_names2txt(uid,uid_ns):
    with open('fans_names_'+str(uid)+'.txt','w') as f:
        f.write(str(uid))
        f.write(u'\t')
        f.write(get_username(uid).encode('utf-8'))
        f.write(u'\n')
        for i in uid_ns[:-1]:
            f.write(i[0])
            f.write(u'\t')
            f.write(i[1].encode('utf-8'))
            f.write(u'\n')
        f.write(uid_ns[-1][0])
        f.write(u'\t')
        f.write(uid_ns[-1][1].encode('utf-8'))

def save_weibo2txt(uid,w_ids):
    for i in w_ids:
        print i
        content =get_weibo_info(int(i))
        with open('weibo_data\\'+str(i)+".txt",'w') as f:
            for d in content:
                f.write(d.encode('utf-8'))
                f.write('\n')
    i=uid
    content =get_weibo_info(int(i))
    with open('weibo_data\\'+str(i)+".txt",'w') as f:
        for d in content:
            f.write(d.encode('utf-8'))
            f.write('\n')


def draw_pics(person_nodes,word_nodes,edges,uid):

    pl.mpl.rcParams['font.sans-serif'] = ['SimHei'] 
    
    G = nx.Graph(edges)
    G.add_nodes_from(person_nodes,color='green')

    G.add_nodes_from(word_nodes,color='yellow')
    pos=nx.spring_layout(G)
    pos2=nx.shell_layout(G)
    plt.figure(figsize=(50,50))
    node_colors=[G.node[v]['color'] for v in G]
    nx.draw_spring(G,with_labels=True,node_color=node_colors,font_color='blue', edge_color='red',font_size=35,node_size=40000)
    # nx.draw_networkx_nodes(G,pos2,node_size=10000,node_color='gray',with_labels=True)
    # edges
    # nx.draw_networkx_edges(G,pos2,edgelist=yt_edgs,width=6, edge_color='red')
    # nx.draw_networkx_edges(G,pos2,edgelist=other_edges,width=6, edge_color='red')
    # nx.draw_networkx_edges(G,pos,edgelist=edges,width=6, edge_color='red')
    # nx.draw_networkx_labels(G,pos2,font_size=20,font_family='sans-serif')

    plt.savefig(str(uid)+'.png')


def main(uid):
    w_ids = get_fans_uids(uid)
    save_fans2txt(uid,w_ids)
    uid_ns = get_usernames(w_ids)
    save_fans_names2txt(uid,uid_ns)
    save_weibo2txt(uid,w_ids)
    key_list=get_key_list(uid,w_ids)
    weights=get_weights_edge(key_list)
    pdicts=get_pdicts(uid)
    person_nodes,word_nodes,edges=get_valid_edges_nodes(weights,pdicts)



if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print 'Usage python spiderpy <uid>'
    
    uid = sys.argv[1]
    main(uid)