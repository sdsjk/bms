# coding:utf-8
'''
Created by dengel on 15/12/10.

@author: stone

'''

import time
def intercept_save(self1, project, taskid, url, result):
    collection_name = self1._collection_name(project)
    if collection_name.find("match") < 0:
        obj2 = {
            'taskid': taskid,
            'url': url,
            'result': result,
            'title':result["title"],
            'author':result["author"],
            'project':collection_name,
            'updatetime': time.time(),
        }
        self1.database["all_results"].update(
            {'taskid': taskid}, {"$set": self1._stringify(obj2)}, upsert=True
        )
    '''
    elif collection_name.find("ssq_dlt")<0:
        obj2 = {

            'taskid': taskid,
            'url': url,
            'result': result,
            #'author':result["author"],
            'project':collection_name,
            'updatetime': time.time(),
        }
        self.database["all_matchs"].update(
            {'taskid': taskid}, {"$set": self._stringify(obj2)}, upsert=True
        )
    else:
        obj2 = {

            'taskid': taskid,
            'url': url,
            'result': result,
            #'author':result["author"],
            'project':collection_name,
            'updatetime': time.time(),
        }
        self.database["all_lottoes"].update(
            {'taskid': taskid}, {"$set": self._stringify(obj2)}, upsert=True
        )
    '''