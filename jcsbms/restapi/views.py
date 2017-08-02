# coding:utf-8
import hashlib
import json
from datetime import datetime, time

import logging

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from analyst.models import Analyst, AnalystPriceRange, AnalystChannelRelation, Analystreflect
from article.models import Article, signer, merge_portaltags, add_articlekey, redis_article_post, ArticleLotteries, \
    ArticlePortalTags, redis_article_remove, Article_Examine
from jauth.models import create_user
from jcsbms.utils import push_article_from_service
from lottery.models import Match, Lotteryentry, CupLeague
from mobileapp.models import Portal, Play, Playdetail
from restapi.serializer import ArticleSerializer, MatchSerializer, PortalSerializer, AnalystSerializer, PlaySerializer, \
    PlaydetailSerializer

logger = logging.getLogger("django")

'''文章表'''
@api_view(['GET','POST'])
def article_list(request):
    if request.method == 'GET':
        articles = Article.objects.all()[1:5]
        serializer = ArticleSerializer(articles,many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data=request.data  # json.loads(request.body)
        article = Article()
        article.id = data['id']
        if len(data['text']) < 16:
            return Response({'message':'内容不得小于16个字符'},status=status.HTTP_400_BAD_REQUEST)
        else:
            article.text_origin = data['text']
        article.date_added = datetime.now()
        article.last_modified = datetime.now()
        # if data['author'] in Analyst.objects.all().values_list('id',flat=True):
        analystreflect= Analystreflect.objects.get(teacher_jcs_id=data['author'])
        analystreflectid=analystreflect.teacher_thai_id
        article.author_id = analystreflectid
        # else:
        #     return Response({'message': '讲师不存在'}, status=status.HTTP_400_BAD_REQUEST)
        article.invisible = True
        article.chargeable = data['chargeable']
        article.price = data['price']
        article.digest_origin = data['digest']
        article.istop = data['istop']
        article.top_time = data['top_time']
        article.end_time = data['end_time']
        article.is_toppage = data['is_toppage']
        if data['language'] in ['M','C']:
            article.language = data['language']
        else:
            return Response({'message':'暂时只支持国语和粤语'}, status=status.HTTP_400_BAD_REQUEST)
        article.sport_type = data['sport_type']
        article.type = data['type']
        article.status=0
        article.save()
        # 生成sign_key
        value = signer.sign(str(article.id))
        sign_value = value[value.find(":") + 1:]
        article.sign_key = sign_value
        article.save()
        # 文章对应赛事表
        lotteries = data["lotteries"]
        if lotteries != "":

            for lottery in lotteries:
                articlelottery = ArticleLotteries()
                articlelottery.article_id = article.id
                scout_match_id=Match.objects.get(lottery_entry_id=lottery).scout_match_id
                match=Match.objects.get(scout_match_id=scout_match_id,project='E')
                articlelottery.lottery_id = match.lottery_entry_id
                articlelottery.date_added = datetime.now()
                articlelottery.save()
        # 文章对应标签表
        # portal_tags = data["portal_tags"]
        # if portal_tags != "":
        #     for portal_tag in portal_tags:
        #         articleportaltag = ArticlePortalTags()
        #         articleportaltag.article_id = article.id
        #         articleportaltag.portal_id = portal_tag
        #         articleportaltag.date_added = datetime.now()
        #         articleportaltag.save()
        # 推redis
        portal_ids = [p.portal_id for p in article.articleportaltags_set.all()]
        lid_list = [lottery["id"] for lottery in article.lotteries.values()]
        matches = Match.objects.filter(lottery_entry__in=lid_list)
        match_list = []
        if matches != None:
            match_list = [x.getDictForCache() for x in matches]
        merge_portaltags(portal_ids, article, match_list)
        add_articlekey(article)
        # redis_article_post(article, match_list)
        # article_add_post(article)
        # 推消息提醒
        return Response({'message': 'success'}, status=status.HTTP_200_OK)

@api_view(['GET','DELETE'])
def article_detail(request,pk):
    try:
        article = Article.objects.get(pk=pk)
    except Article.DoesNotExist:
        return Response({'message': '文章不存在'},status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    if request.method == "DELETE":
        article.invisible = True
        article.save()
        redis_article_remove(article)
        merge_portaltags([], article, [])
        return Response({'message': 'success'}, status=status.HTTP_200_OK)

'''赛事表'''
@api_view(['GET','POST'])
@parser_classes((JSONParser,))
def match_list(request):
    if request.method == 'GET':
        print 'in get'
        matches = Match.objects.all()[1:5]
        serializer = MatchSerializer(matches,many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data
        print data
        # cupleague=CupLeague()
        # cupleague.name=data['cup_name']
        # cupleague.type=0
        # cupleague.status=0
        # cupleague.create_time=datetime.now()
        # cupleague.update_time=datetime.now()
        # cupleague.op_id=0
        # # cupleague.sport_type=data.get('sport_type',None)
        # cupleague.project=data['project']
        # cupleague.save()


        # scout_match_id=data.get('scout_match_id', '')
        #
        # if scout_match_id !=None and Match.objects.filter(scout_match_id=scout_match_id,project=data['project']).count()>0:
        #     return Response({'message':'数据重复拥有'}, status=status.HTTP_404_NOT_FOUND)

        match = Match()
        match.id = data['id']
        match.cup_name = data['cup_name']
        match.home_team = data['home_team']
        match.away_team = data['away_team']
        match.project = data['project']
        match.start_time = data['start_time']
        match.match_id = data['match_id']
        match.scout_match_id=data.get('scout_match_id','')
        match.sport_type=data['sport_type']
        match.syn_date=datetime.now()
        # 伪造一个lotteryentry对象
        m = hashlib.md5()
        m.update(str(datetime.now()))
        taskid = m.hexdigest()
        entry = Lotteryentry(taskid=taskid, type_id=data['lotterytypes'][0])
        entry.id = data['lottery_entry']
        entry.save()
        match.lottery_entry = entry
        match.save()
        return Response({'message':'success'}, status=status.HTTP_200_OK)

'''赛事更新'''
@api_view(['POST'])
def match_update(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        match = Match.objects.get(id=int(data['id']))
        match.cup_name = data['cup_name']
        match.home_team = data['home_team']
        match.away_team = data['away_team']
        match.project = data['project']
        match.start_time = data['start_time']
        match.match_id = data['match_id']
        match.save()
        return Response({'message': 'success'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def match_detail(request,pk):
    try:
        match = Match.objects.get(pk=pk)
    except Match.DoesNotExist:
        return Response({'message': '赛事不存在'},status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = MatchSerializer(match)
        return Response(serializer.data)

'''标签表'''
@api_view(['GET','POST'])
def portal_list(request):
    if request.method == 'GET':
        protals = Portal.objects.all()[1:5]
        serializer = PortalSerializer(protals,many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data=request.data  # json.loads(request.body)
        portal = Portal()
        if data['id'] in Portal.objects.all().values_list('id', flat=True):
            return Response({'message':'Portal projetct is exist'},status=status.HTTP_400_BAD_REQUEST)
        else:
            portal.id = data['id']
        portal.is_online = data['is_online']
        portal.can_selected = data['can_selected']
        portal.name = data['name']
        portal.img_url = data['img_url']
        portal.date_added = datetime.now()
        portal.last_modified = datetime.now()
        portal.target_url = data['target_url']
        portal.rank = data['rank']
        if data['project'] in ['M','C']:
            portal.project = data['project']
        else:
            return Response({'message':'暂时只支持国语和粤语'}, status=status.HTTP_400_BAD_REQUEST)
        portal.show_user_flag = data['show_user_flag']
        portal.show_user_value = data['show_user_value']
        portal.show_channel_flag = data['show_channel_flag']
        portal.show_channel_value = data['show_channel_value']
        portal.save()
        return Response({'message':'success'}, status=status.HTTP_200_OK)

'''讲师表'''
@api_view(['GET','POST'])
def analyst_list(request):
    # if request.method == 'GET':
    #     analysts = Analyst.objects.all()[1:5]
    #     serializer = AnalystSerializer(analysts,many=True)
    #     return Response(serializer.data)
    # elif request.method == 'POST':
    #     data=request.data  # json.loads(request.body)
    #     analyst = Analyst()
    #     analyst.id = data['id']
    #     analyst.analyst_type = data['analyst_type']
    #     analyst.nick_name = data['nick_name']
    #     analyst.brief = data['brief']
    #     analyst.real_name = data['real_name']
    #     analyst.id_number = data['id_number']
    #     analyst.bank_branch = data['bank_branch']
    #     analyst.card_number = data['card_number']
    #     user = create_user(data['username'],data['email'])
    #     analyst.user_id = user.id
    #     analyst.address = data['address']
    #     analyst.date_added = datetime.now()
    #     analyst.last_modified = datetime.now()
    #     analyst.lottery_type_id = data['lottery_type']
    #     analyst.mobile = data['mobile']
    #     analyst.post_code = data['post_code']
    #     analyst.weichat = data['weichat']
    #     analyst.level_id = data['level']
    #     analyst.invisible = data['invisible']
    #     analyst.answer_level_id = data['answer_level']
    #     analyst.analyst_group_id = data['analyst_group']
    #     analyst.ban_chargeable = data['ban_chargeable']
    #     analyst.ban_free = data['ban_free']
    #     analyst.ban_letter = data['ban_letter']
    #     analyst.is_cantonese_perm = data['is_cantonese_perm']
    #     analyst.ban_chargeable_cantonese = data['ban_chargeable_cantonese']
    #     analyst.ban_free_cantonese = data['ban_free_cantonese']
    #     analyst.save()
    #
    #     if 'low_price' in data:
    #         analystpricerange = AnalystPriceRange()
    #         analystpricerange.analyst_id = data['id']
    #         analystpricerange.low_price = data['low_price']
    #         analystpricerange.high_price = data['high_price']
    #         analystpricerange.default_price = data['default_price']
    #         analystpricerange.status = data['price_status']
    #         analystpricerange.create_time = datetime.now()
    #         analystpricerange.update_time = datetime.now()
    #         analystpricerange.op_id = data['price_op_id']
    #         analystpricerange.save()
    #
    #     if 'channel_id' in data:
    #         analystchannelrelation = AnalystChannelRelation()
    #         analystchannelrelation.analyst_id = data['id']
    #         analystchannelrelation.channel_id = data['channel_id']
    #         analystchannelrelation.status = data['channel_status']
    #         analystchannelrelation.create_time = datetime.now()
    #         analystchannelrelation.update_time = datetime.now()
    #         analystchannelrelation.op_id = data['channel_price_op_id']
    #         analystchannelrelation.save()

    return Response({'message': 'success'}, status=status.HTTP_200_OK)


'''play表'''
@api_view(['GET','POST'])
@parser_classes((JSONParser,))
def play_list(request):
    if request.method == 'GET':
        print 'in get'
        play = Play.objects.all()[1:5]
        serializer = PlaySerializer(play,many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data
        play=Play()
        play.id=data["id"]
        play.article_id=int(data["article"])
        play.match_id=int(data["match"])
        play.language=data["language"]
        # play.last_update_time=data["last_update_time"]
        # play.create_time=datetime.now()
        play.recommend_reason=data["recommend_reason"]
        play.type=int(data["type"])
        play.major_flag=data["major_flag"]
        play.scout_odds_flag=data["scout_odds_flag"]
        play.save()
        return Response({'message':'success'}, status=status.HTTP_200_OK)
'''playdetail表'''
@api_view(['GET','POST'])
@parser_classes((JSONParser,))
def playdetail_list(request):
    if request.method == 'GET':
        print 'in get'
        playdetail = Playdetail.objects.all()[1:5]
        serializer = PlaydetailSerializer(playdetail,many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data
        playdetail=Playdetail()
        playdetail.play_id=int(data["play"])
        playdetail.key=data["key"]
        playdetail.value = data["value"]
        playdetail.major_flag=data["major_flag"]
        playdetail.select_flag=data["select_flag"]
        playdetail.save()
        return Response({'message':'success'}, status=status.HTTP_200_OK)
