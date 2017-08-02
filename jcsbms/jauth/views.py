# coding:utf-8

import json
import os

from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import JsonResponse,HttpResponseRedirect


from .models import Userinfo
from .forms import LoginForm

from jcsbms.image_processing import crop_avatar
from DjangoUeditor.utils import GenerateRndFilename

from jcsbms.utils import getClientIp, getUserAgent, formerror_cat
import logging
import hashlib
from analyst.models import Analyst, AnalystNewPassword

logger = logging.getLogger("django")
# Create your views here.
@login_required
def index(request):
    return TemplateResponse(request,"jauth/index.html",{})

def login(request):

    if request.method == "GET":
        next = request.GET.get("next","")
        return TemplateResponse(request,"jauth/login.html",{"next":next})

    elif request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():

            user = auth.authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])

            logger.info("user:`%s`, ip:%s, ua:%s" % (form.cleaned_data['username'], getClientIp(request), getUserAgent(request) ))

            if user is not None and user.is_active:

                auth.login(request, user)

                analyst = None
                new_password = None
                m = hashlib.md5(form.cleaned_data["password"])
                password = m.hexdigest()
                try:
                    analyst = Analyst.objects.get(user_id=user.id)
                except Analyst.DoesNotExist, e:
                    logger.error("%s is not analyst, error: %s", user, e)

                if analyst:
                    try:
                        new_password = AnalystNewPassword.objects.get(analyst_id=analyst.id)
                        if new_password.password == password:
                            new_password = None
                    except AnalystNewPassword.DoesNotExist, e:
                        logger.info("create new password for %s", user)
                        new_password = AnalystNewPassword()

                    if new_password:
                        new_password.analyst_id = analyst.id
                        new_password.analyst_name = analyst.nick_name
                        new_password.password = password
                        new_password.save()

                return JsonResponse({"result":True})
            else:
                return JsonResponse({"result":False})
        else:
            return JsonResponse({"result":False,"message":formerror_cat(form)})
    return JsonResponse({"result":False,"message":"invalid request!"})

@login_required
def upload_myavatar(request):
    if request.method == "GET":
        return TemplateResponse(request, "jauth/upload_myavatar.html")
    else:
        userinfo = Userinfo.objects.get(user=request.user)
        img_url = request.POST.get("img_url","")
        user_dir = img_url[8:24]
        if userinfo.user_dir != user_dir:
            return JsonResponse({"result":False,"message":u"非法数据操作已记录"})
        size = (int(request.POST["x1"]),int(request.POST["y1"]),int(request.POST["x2"]),int(request.POST["y2"]))
        userinfo.avatar = crop_avatar(img_url,size)
        userinfo.save()
        return JsonResponse({"result":True})


@login_required
def upload_avatar(request):
    if request.method == "GET":
        return TemplateResponse(request, "jauth/upload_avatar.html")
    else:
        userinfo = Userinfo.objects.get(user=request.user)
        img_url = request.POST.get("img_url","")
        user_dir = img_url[8:24]
        if userinfo.user_dir != user_dir:
            return JsonResponse({"result":False,"message":u"非法数据操作已记录"})
        size = (int(request.POST["x1"]),int(request.POST["y1"]),int(request.POST["x2"]),int(request.POST["y2"]))
        userinfo.avatar = crop_avatar(img_url,size)
        userinfo.save()
        return JsonResponse({"result":True})


mime2type = {}
mime2type["image/gif"]="gif"
mime2type["image/jpeg"]="jpg"
mime2type["image/png"]="png"
userdir_prefix = "upfiles/"
@login_required
def avatar_upload(request):
    if "action" in request.POST:

        action = request.POST["action"]
        if action =="upload" and "file" in request.FILES:
            userinfo = Userinfo.objects.get(user=request.user)
            uploadpath = userdir_prefix+userinfo.user_dir+"/"
            f = request.FILES["file"]
            if f.content_type not in mime2type:
                return TemplateResponse(request, 'jauth/avatarupload_result.html', {"result":False,"message":u"只能上传jpg、png、gif文件"})
            if f.size >2*1024*1024:
                return TemplateResponse(request, 'jauth/avatarupload_result.html', {"result":False,"message":u"上传文件不能大于2M"})
            file_type = mime2type[f.content_type]
            filename = GenerateRndFilename(f.name,file_type)
            saved_path=default_storage.save(os.path.join(uploadpath,filename),f)
            #add_image(uploadpath+filename,userinfo)

            #filepath = os.path.join(MEDIA_ROOT,filename)
            #这个while可能会导致访问阻塞,但概率很小。
            #with open(filepath, 'wb+') as destination:
            #    for chunk in f.chunks():
            #        destination.write(chunk)
            #fileurl = MEDIA_URL + filename
            return TemplateResponse(request, 'jauth/avatarupload_result.html', {"result":True,"fileurl":saved_path})
    else:
        return TemplateResponse(request, 'jcs/fileupload.html')

@login_required
def set_password(request):
    user =request.user
    if request.method == "GET":
        return TemplateResponse(request, 'jauth/set_password.html')
    elif request.method == "POST":
        if user.check_password(request.POST['oldpassword']):
            user.set_password(request.POST['newpassword'])
            user.save()
            return JsonResponse({"result":True})
        else:
            return JsonResponse({"result":False,"message":u"原密码错误!"})


@login_required
def login_out(request):
    auth.logout(request)
    return HttpResponseRedirect('/yonghu/denglu/')


def user_info(request):
    user = request.user
    callback = request.GET.get('callback', '')
    if not request.user.is_authenticated():
        result = {"code": "1000", "message": u"您尚未登录".encode(encoding='utf-8')}
    else:
        group_list = []
        for g in user.groups.all():
            group_list.append(g.name)
        result = {
            "code": "0000",
            "data":{
                "user": {
                    "id": user.id,
                    "name": user.username,
                    "email": user.email
                },
                "groups": group_list,
                "permissions": list(user.get_all_permissions()),
            }
        }

    if callback:
        return HttpResponse('%s(%s)' % (callback, json.dumps(result)))
    else:
        return JsonResponse(result)