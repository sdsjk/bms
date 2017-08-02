# coding:utf-8
'''
Created by dengel on 16/4/8.

@author: stone

'''
from django.utils import timezone

from ask.models import Question
from mobileapp.models import Banner


def Site_Constants(request):
    return {
        "now":timezone.now(),
        "QUESTION_STATUS_SUBMITED":Question.STATUS_SUBMITED,
        "QUESTION_STATUS_CLOSED": Question.STATUS_CLOSED,
        "QUESTION_STATUS_COMPLETED": Question.STATUS_COMPLETED,
        "BANNER_TARGET_TYPE_ANALYST":Banner.TARGET_TYPE_ANALYST,
        "BANNER_TARGET_TYPE_ARTICLE": Banner.TARGET_TYPE_ARTICLE,
        "BANNER_TARGET_TYPE_LOTTERY": Banner.TARGET_TYPE_LOTTERY,
        "BANNER_TARGET_TYPE_H5": Banner.TARGET_TYPE_H5,

    }