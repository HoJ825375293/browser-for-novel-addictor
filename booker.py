from flask import Flask, make_response, render_template, request
import numpy as np
import pandas as pd
import math
import jieba
from operator import itemgetter

app = Flask(__name__)
app.config.from_object('config')


@app.route('/book/search', methods=['GET'])
def form():
    return render_template('book.html')


@app.route('/book/search', methods=['POST'])
def search():
    #文档管理器
    key = request.form
    search_key = key['keyword']
    df = pd.read_csv(r'book.csv', encoding='gbk')


    #索引构建器
    search_words = []   #词典
    search_filed = {}   #词记录映射
    count_filed = {}    #方便计算相关
    W2 = {}             #影响力W2
    sequence = {}       #相关度词典
    #初始化
    for i in df.index:
        search_filed[i] = []
        sequence[i] = {}
        count_filed[i] = ''

    for i in df.index:
        count_filed[i] += df.loc[i, '书名']
        count_filed[i] += df.loc[i, '介绍']
        seg_words = jieba.cut_for_search(df.loc[i, '介绍'])
        seg_titile = jieba.cut_for_search(df.loc[i, '书名'])
        search_filed[i].extend(list(seg_titile))
        search_filed[i].extend(list(seg_words))
        search_words.extend(search_filed[i])

    '''
    #垃圾词去除，但考虑到搜索引擎效率，不做保留
    filterWords = ['的', '是']
    filteredSearchWords = []
    for seg in search_words:
        if seg not in stopWords:
            filteredSearchWords += seg
    print(filteredSearchWords)
    '''
    #异常处理
    if search_key not in search_words:
        return render_template('book.html', nums=[{'name': "找不到结果"}])

    #构建倒排索引
    invertIndex = dict()
    for word in search_words:
        dictRecord = []
        for ind in df.index:
            if word in search_filed[ind]:
                dictRecord.append(ind)
        invertIndex[word] = dictRecord

    # 计算W2
    lenth = len(search_filed)
    for word in search_words:
        df_ = 0
        for i in count_filed.keys():
            df_ += count_filed[i].count(word)
        W2[word] = math.log10(lenth / df_)  # W2

    # 计算每本book内检索词的相关度
    for i in search_filed.keys():
        for word in search_filed[i]:
            tf = count_filed[i].count(word)
            W1 = math.log10(tf + 1)
            sequence[i][word] = W1 * W2[word]

    # 索引检索
    L = []
    for i in invertIndex[search_key]:
        book = {}
        book['name'] = df.loc[i, '书名']
        book['auth'] = df.loc[i, '作者']
        book['time'] = df.loc[i, '时间']
        book['rar'] = df.loc[i, 'rar下载']
        book['txt'] = df.loc[i, 'txt下载']
        book['per'] = sequence[i][search_key]
        book['intro'] = df.loc[i, '介绍']
        L.append(book)
    L = sorted(L, reverse=True, key=itemgetter('per'))
    return render_template('book.html', nums=L)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=8000)
