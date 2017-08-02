# coding=utf-8
'''序列化,将对象转化为json格式'''
from rest_framework import serializers

from analyst.models import Analyst
from article.models import Article
from lottery.models import Match
from mobileapp.models import Portal, Play, Playdetail


class ArticleSerializer(serializers.ModelSerializer):
    chargeable = serializers.BooleanField()
    istop = serializers.BooleanField()
    is_toppage = serializers.BooleanField()
    class Meta:
        model = Article
        # fields = ('id',) #只显示id字段
        # exclude = ('users',) #除了users字段不显示，其他字段都显示
        fields = '__all__' #显示所有字段

class MatchSerializer(serializers.ModelSerializer):
    match_id = serializers.CharField(required=False, max_length=32)
    class Meta:
        model = Match
        fields = '__all__'

class PortalSerializer(serializers.ModelSerializer):
    is_online = serializers.BooleanField()
    can_selected = serializers.BooleanField()
    show_user_flag = serializers.BooleanField()
    show_channel_flag = serializers.BooleanField()
    class Meta:
        model = Portal
        fields = '__all__'

class AnalystSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analyst
        fields = '__all__'

class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = '__all__'

class PlaydetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playdetail
        fields = '__all__'