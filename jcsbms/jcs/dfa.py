# coding:utf-8
#!/usr/bin/python2.7
'''
Created by dengel on 16/4/25.

@author: stone

'''


import os
import time
import codecs

class Node(object):
    def __init__(self):
        self.children = None

def add_word(root,word):
    node = root
    for i in range(len(word)):
        if node.children == None:
            node.children = {}
            node.children[word[i]] = Node()
        elif word[i] not in node.children:
            node.children[word[i]] = Node()
        node = node.children[word[i]]
class DFASearch():
    root = Node()
    parent_path = os.path.dirname(os.path.abspath(__file__))
    path= os.path.join(parent_path,'banned_words')
    fp = codecs.open(path, 'r', "utf-8")
    for line in fp:
        line = line[0:-1]
        add_word(root, line)
    fp.close()
    @staticmethod
    def has_banned(message):
        for i in range(len(message)):
            p = DFASearch.root
            j = i
            word = ""
            while (j < len(message) and p.children != None and message[j] in p.children):
                word = word + message[j]
                p = p.children[message[j]]
                j = j + 1

            if p.children == None:
                return word

        return ""


'''


def init(path):

    return root
'''




def dfa_test():
    print '----------------dfa-----------'
    #root = init('./banned_words')

    message = u"俄罗斯轮盘".encode("utf-8")
    #print chardet.detect(message)
    #message = '不顾'
    print '***message***',len(message)
    start_time = time.time()

    res = DFASearch.has_banned(message)
    print res
    end_time = time.time()
    print (end_time - start_time)

'''
def is_contain2(message,word_list):
    for item in word_list:
        print chardet.detect(item)
        if message.find(item)!=-1:
            return True
    return False

def normal():
    print '------------normal--------------'
    path = './banned_words'
    fp = open(path,'r')
    word_list = []
    message = u"四大舰队"
    print '***message***',len(message)
    for line in fp:
        line = line[0:-1]
        word_list.append(line)
    fp.close()
    print 'The count of word:',len(word_list)
    start_time = time.time()
    for i in range(1000):
        res = is_contain2(message,word_list)
        #print res
    end_time = time.time()
    print (end_time - start_time)
'''

if __name__ == '__main__':
    dfa_test()
