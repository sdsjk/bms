# coding:utf-8
from datetime import timedelta, datetime

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase


# Create your tests here.
from django.utils import timezone
from selenium.webdriver.chrome.webdriver import WebDriver

from analyst.models import Analyst
from article.models import Article, ArticlePortalTags
from ask.models import Question
from jcs.models import Letter
from mobileapp.models import Purchase

import os
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8082'


class AnalystTestCase(TestCase):
    fixtures = ['permissions.json','groups.json','users.json','lotterytypes.json',
                'analystlevels.json','answerlevels.json','analystgroups.json','analysts.json',"artilces.json",
                'lottery.json','matchs.json','questions.json','replies.json','portals.json']



    def setUp(self):
        self.client.login(username='uvw123', password='163a163a')

    def test_analystindex(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response,u'<li><a title="已爬取的文章" href="/wenzhang/authorsearch/">编辑工作台</a></li>')

        self.assertContains(response,u'<li><a title="已爬取的文章" href="/laoshi/wodewenzhang/">老师工作台</a></li>')

    def test_my_articles(self):
        response = self.client.get('/laoshi/wodewenzhang/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response,u'<button class="btn btn-primary dropdown-toggle" data-toggle="dropdown">操作<span class="caret"></span></button>',10)
    def test_analyst_post_article(self):
        response = self.client.get('/laoshi/fabu/')
        self.assertContains(response,u'<input class="form-control" ng-model="lottery.teamword" id="inputTypeWord" name="typeword" placeholder="请输入队名关键字">')

        response = self.client.post('/laoshi/fabu/',{"text":u"<p>###免费不上首页测试文字##</p>","portaltags":[1,2,3]})
        self.assertEqual(response.json()['result'], True)
        article = Article.objects.filter(text=u"<p>###免费不上首页测试文字##</p>").order_by("-id")[0]

        self.assertEqual(article.portal_tags.all().count(),2)

        response = self.client.get('/laoshi/fabu/?id='+str(article.id))
        self.assertTemplateUsed(response,'analyst/article_info.html')

        response = self.client.post('/laoshi/fabu/', {"text": u"<p>###免费不上首页测试文字##</p>"})
        self.assertEqual(response.json()['result'], False)

        response = self.client.post('/laoshi/fabu/', {"text": u"<p>###免费上首页测试文字###1</p>","is_toppage":"on"})
        self.assertEqual(response.json()['result'], True)
        response = self.client.post('/laoshi/fabu/', {"text": u"<p>###免费上首页测试文字###2</p>","is_toppage":"on"})
        self.assertEqual(response.json()['result'], True)
        response = self.client.post('/laoshi/fabu/', {"text": u"<p>###免费上首页测试文字###3</p>","is_toppage":"on"})
        self.assertEqual(response.json()['result'], True)
        response = self.client.post('/laoshi/fabu/', {"text": u"<p>###免费上首页测试文字###4</p>","is_toppage":"on"})
        self.assertEqual(response.json()['result'], True)
        response = self.client.post('/laoshi/fabu/', {"text": u"<p>###免费上首页测试文字###5</p>","is_toppage":"on"})
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(Article.objects.filter(text__contains=u"<p>###免费上首页测试文字###",is_toppage=True).count(),5)
        response = self.client.post('/laoshi/fabu/', {"text": u"<p>###免费上首页--6--测试文字###</p>", "is_toppage": "on"})
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(Article.objects.get(text=u"<p>###免费上首页--6--测试文字###</p>").is_toppage,False)

        response = self.client.post('/laoshi/fabu/',
                                    {"text": u"<p>###收费上首页测试文字###1</p>", "digest":"收费文章摘要","is_toppage": "on","chargeable":"on"})
        self.assertEqual(response.json()['result'], True)
        response = self.client.post('/laoshi/fabu/',
                                    {"text": u"<p>###收费上首页测试文字###2/p>",  "digest":u"收费文章摘要","is_toppage": "on", "chargeable": "on"})
        self.assertEqual(response.json()['result'], True)

        self.assertEqual(Article.objects.filter(text__contains=u"<p>###收费上首页测试文字###", is_toppage=True).count(), 2)

        response = self.client.post('/laoshi/fabu/',
                                    {"text": u"<p>###收费上首页--3--测试文字###</p>", "digest":u"收费文章摘要", u"is_toppage": "on", "chargeable": "on"})

        self.assertEqual(response.json()['result'], True)

        article = Article.objects.get(text=u"<p>###收费上首页--3--测试文字###</p>")
        self.assertEqual(article.is_toppage, False)
        response = self.client.get('/laoshi/fabu/?id=' + str(article.id))
        self.assertTemplateUsed(response, 'analyst/article_info.html')

        response = self.client.post('/laoshi/fabu/', {"text": u"<p>###免费有相关过期赛事文章测试文字---1---###</p>", "is_toppage": "on","relLottery":["14665"]})
        self.assertEqual(response.json()['result'], True)
        article = Article.objects.get(text=u"<p>###免费有相关过期赛事文章测试文字---1---###</p>")
        response = self.client.get('/laoshi/fabu/?id=' + str(article.id))
        self.assertTemplateUsed(response, 'analyst/article_info.html')

        response = self.client.post('/laoshi/fabu/',
                                    {"text": u"<p>###免费有相关未过期赛事文章测试文字---2---###</p>", "is_toppage": "on",
                                     "relLottery": ["14669"]})
        self.assertEqual(response.json()['result'], True)
        article = Article.objects.get(text=u"<p>###免费有相关未过期赛事文章测试文字---2---###</p>")
        response = self.client.get('/laoshi/fabu/?id=' + str(article.id))
        self.assertTemplateUsed(response, "analyst/article_info.html")
        response = self.client.post('/laoshi/fabu/',
                                    {"text": u"<p>###免费有相关未过期赛事文章测试文字---3---###</p>", "is_toppage": "on",
                                     "relLottery": ["14665","14669"]})

        self.assertEqual(response.json()['result'], True)
        article = Article.objects.get(text=u"<p>###免费有相关未过期赛事文章测试文字---3---###</p>")
        response = self.client.get('/laoshi/fabu/?id=' + str(article.id))
        self.assertTemplateUsed(response, "analyst/article_info.html")

        analyst = Analyst.objects.get(user__username="uvw123")
        analyst.ban_chargeable=True
        analyst.banchargeable_time = timezone.now()+timedelta(days=1)
        analyst.save()
        response = self.client.post('/laoshi/fabu/',
                                    {"text": u"<p>###收费不可发测试文字###</p>", "digest": u"收费文章摘要",
                                     "chargeable": "on"})
        self.assertEqual(response.json()['result'], False)

        analyst = Analyst.objects.get(user__username="uvw123")
        analyst.ban_free= True
        analyst.banfree_time = timezone.now() + timedelta(days=1)
        analyst.save()
        response = self.client.post('/laoshi/fabu/',
                                    {"text": u"<p>###免费不可发测试文字###</p>", "digest": u"收费文章摘要",
                                     "chargeable": "on"})
        self.assertEqual(response.json()['result'], False)


    def test_analyst_info(self):
        response = self.client.get('/laoshi/xinxi/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/laoshi/xinxi/',{
            "real_name": u"张磊",
            "id_number": "450302198310211532",
            "card_number": "1111111111111111111",
            "bank_branch": u"中信银行北京上地支行",
            "email": "uvw173@163.com",
            "weichat":"George173",
            "mobile":"18611557199",
            "address":u"尚都soho南塔",
            "post_code":"100000",
            "brief":u"足彩职业玩家。精通五大联赛，非常了解竞彩及外围玩法。尤其擅长2串1。文章主要展示实单，免费为主！菠菜为娱乐，跟单需谨慎!"
        })
        self.assertEqual(response.json()['result'], True)

    def test_question(self):
        response = self.client.get('/wenda/wode/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,u'<div class="col-sm-6">来自*******5078的问题</div>',3)
        self.assertContains(response, u'有新消息', 1)


        response = self.client.get("/wenda/chahuifu/",{"qid":"24"})
        self.assertEqual(len(response.json()),11)

        response = self.client.get("/wenda/wenti/", {"id": "24"})
        self.assertContains(response,u"此问答已被关闭,无需回复.")

        question = Question()
        question.content=u"新问题测试文本"
        question.from_user_id = 224
        question.from_auser_id = 755
        question.to_analyst_id= 147
        question.expire_date=timezone.now()+timedelta(hours=24)
        question.save()



        purchase = Purchase()
        purchase.user_id =755
        purchase.author_id = 147
        purchase.purchasetype = Purchase.PURCHASE_TYPE_ASK
        purchase.target = question.id
        purchase.price = 8
        purchase.status = 0
        purchase.paytype = Purchase.PAY_TYPE_GOLD
        purchase.paymentid =2
        purchase.save()

        response = self.client.get('/wenda/wode/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u'收费问答<span class="badge">')
        self.assertContains(response, u'有新消息', 2)

        response = self.client.get("/wenda/wenti/", {"id": str(question.id)})

        self.assertContains(response, u"此问答已被关闭,无需回复.",0)

        '''
        此功能下线了
        pub_date = (datetime.now()+timedelta(hours=12)).strftime("%Y-%m-%d %H:%M")
        response = self.client.post("/wenda/set_pubdate/",{"question_id":str(question.id),"pub_date":pub_date})
        self.assertEqual(response.json()['result'], True)

        pub_date = (datetime.now() + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M")
        response = self.client.post("/wenda/set_pubdate/", {"question_id": str(question.id), "pub_date": pub_date})
        self.assertEqual(response.json()['result'], False)
        '''
        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母1"})
        self.assertEqual(response.json()['result'], True)
        question2 = Question.objects.get(id= question.id)
        self.assertNotEqual(question.expire_date,question2.expire_date)

        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母1"})
        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母1"})
        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母1"})
        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母1"})
        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母1"})
        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母1"})
        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母1"})
        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母1"})
        response = self.client.post("/wenda/huifu/", {"question_id": str(question.id), "content": u"测试问题回复内容至少10个字母10"})

        question = Question.objects.get(id=question.id)
        self.assertEqual(question.status,Question.STATUS_COMPLETED)
        self.assertNotEqual(question.pub_date,None)

    def test_letters(self):


        letter = Letter()
        letter.from_auser_id = 755
        letter.to_user_id = 150
        letter.content = u"测试消息内容"

        letter.save()

        response = self.client.get("/site/wodexiaoxi/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,u'免费私信<span class="badge">')

        response = self.client.get("/site/chaxiaoxi/",{"action":"unread","offset":0})
        self.assertEqual(len(response.json()),1)

        response = self.client.get('/site/chaxiaoxi/',{"action":"reading","from_auser":"755","offset":"0"})
        self.assertEqual(len(response.json()), 1)

        response = self.client.post('/site/faxiaoxi/',{"to_auser":755,"content":"测试消息回复内容"})
        self.assertEqual(response.json()['result'], True)

        analyst = Analyst.objects.get(user__username="uvw123")
        analyst.ban_letter = True
        analyst.banletter_time = timezone.now() + timedelta(days=1)
        analyst.save()

        response = self.client.post('/site/faxiaoxi/', {"to_auser": 755, "content": "测试消息回复内容"})
        self.assertEqual(response.json()['result'], False)


'''
class MySeleniumTests(StaticLiveServerTestCase):
    fixtures = []
    available_apps = (
                    'django.contrib.admin',
                    'django.contrib.auth',
                    'django.contrib.contenttypes',
                    'django.contrib.sessions',
                    'django.contrib.messages',
                    'django.contrib.staticfiles',
                    'jcs',
                    'DjangoUeditor',
                    'jauth',
                    'analyst',
                    'article',
                    'lottery',
                    'mobileapp',
                    'ask',
                )

    @classmethod
    def setUpClass(cls):
        super(MySeleniumTests, cls).setUpClass()
        cls.selenium = WebDriver()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(MySeleniumTests, cls).tearDownClass()

    def test_login(self):
        self.selenium.get("http://www.baidu.com")
        #self.selenium.get('%s%s' % (self.live_server_url, '/login/'))
        #username_input = self.selenium.find_element_by_name("username")
        #username_input.send_keys('myuser')
        #password_input = self.selenium.find_element_by_name("password")
        #password_input.send_keys('secret')
        #self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()
'''











