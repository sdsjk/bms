# coding:utf-8
'''
Created by dengel on 15/11/23.

@author: stone

'''
from django import  forms

from lottery.models import TeamName, Prize, Team, Fixture, CupLeague, RenXuan


class TeamNameForm(forms.ModelForm):
    class Meta:
        model = TeamName
        fields = ["standard_name"]

class PrizeForm(forms.ModelForm):
    class Meta:
        model = Prize
        fields = ["start_time","end_time","reward","description"]

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["sport_type","name", "project"]



class FixtureForm(forms.ModelForm):
    class Meta:
        model = Fixture
        fields = ["cup_name","start_time","home_team","away_team","remark"]

class CupLeagueForm(forms.ModelForm):
    class Meta:
        model = CupLeague
        fields = ['name', "sport_type", "project"]

class RenXuanForm(forms.ModelForm):
    class Meta:
        model = RenXuan
        fields = ['issue', "end_time", 'match1', 'match2', 'match3', 'match4',
                  'match5', 'match6', 'match7', 'match8', 'match9', 'match10',
                  'match11', 'match12', 'match13','match14',
                  ]


