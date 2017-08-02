from django.contrib import admin

# Register your models here.
from ask.models import AnswerLevel, Question

admin.site.register(AnswerLevel)
admin.site.register(Question)
