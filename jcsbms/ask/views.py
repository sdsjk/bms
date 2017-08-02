# coding:utf-8
from datetime import datetime, timedelta

from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse


# Create your views here.
from django.template.response import TemplateResponse
from django.utils import timezone

from ask.forms import ReplyForm
from ask.models import Question, Reply, question_completed, reply_post
from jcsbms.utils import formerror_cat
from mobileapp.models import Purchase

@permission_required("analyst.analyst_action")
def my_quesions(request):
    questions = Question.objects.filter(to_analyst=request.user.analyst).filter(Q(status= Question.STATUS_SUBMITED)
                                                                                |Q(status = Question.STATUS_COMPLETED))

    paginator = Paginator(questions.order_by("-last_modified"), 30)
    page_index = request.GET.get("page_index", 1)
    pager = paginator.page(page_index)
    for object in pager.object_list:
        to_replys= object.reply_set.filter(poster=object.from_user)
        if to_replys:
            object.lastinfo = u"最新追问:"+to_replys.last().content[:30]
            object.lastinfo_date  = '<div class="float-right text-right"  >' +timezone.localtime(to_replys.last().date_added).strftime("%Y-%m-%d %H:%M")+'</div>'

    return TemplateResponse(request, "ask/question_list.html", {"pager": pager})
@permission_required("analyst.analyst_action")
def quesion_info(request):
    question = Question.objects.get(id=request.GET["id"],to_analyst=request.user.analyst)
    if question.unread:
        question.unread=False
        question.save()
    return TemplateResponse(request, "ask/question_info.html", {"question": question})
@permission_required("analyst.analyst_action")
def quesion_replies(request):
    question = Question.objects.get(id=request.GET["qid"], to_analyst=request.user.analyst)
    reply_list=[]
    for reply in question.reply_set.all().order_by("id"):
        if reply.poster.id == question.from_user.id and reply.unread:
            reply.unread=False
            reply.save()
        reply_value ={}
        reply_value["poster"] =  "*******"+reply.poster.username[-4:]
        reply_value["content"]= reply.content
        reply_value["date_added"] =timezone.localtime(reply.date_added).strftime("%Y-%m-%d %H:%M:%S")
        reply_list.append(reply_value)
    return JsonResponse(reply_list,safe=False)
@permission_required("analyst.analyst_action")
def post_reply(request):

    question = Question.objects.get(id=request.POST["question_id"], to_analyst=request.user.analyst)
    if question.status != Question.STATUS_SUBMITED:
        return JsonResponse({"result": False, "message": u"交谈次数已经超过十次，问题已关闭"})

    reply = Reply()
    reply.poster=request.user
    reply.question =question
    form = ReplyForm(request.POST,instance=reply)
    if form.is_valid():
        with transaction.atomic():
            form.save()
            if question.reply_set.filter(poster=question.to_analyst.user).count()==1:
                question.expire_date=timezone.now()+timedelta(hours=12)
                question.save()
        reply_post(question)
        if question.reply_set.all().filter(poster=question.to_analyst.user).count() >= Question.MAX_ANSWER_TIME:
            with transaction.atomic():
                question.status = Question.STATUS_COMPLETED
                if question.pub_date ==None:
                    question.pub_date = timezone.now()+timedelta(hours=24)
                question.expire_date = timezone.now()
                question.save()
                Purchase.objects.filter(target=question.id,purchasetype=Purchase.PURCHASE_TYPE_ASK).update(status= Purchase.STATUS_SUCCESS)
            question_completed(question)
        return JsonResponse({"result": True})
    else:
        return JsonResponse({"result": False, "message": formerror_cat(form)})
@permission_required("analyst.analyst_action")
def set_pubdate(request):
    question = Question.objects.get(id=request.POST["question_id"], to_analyst=request.user.analyst)
    if question.pub_date:
        return JsonResponse({"result": False, "message": u"公布时间已设置"})
    else:
        question.pub_date = timezone.make_aware(datetime.strptime(request.POST["pub_date"],"%Y-%m-%d %H:%M"))
        question.save()
        return JsonResponse({"result": True})

