import mongoengine as me
import sys
sys.path.append('../')
import settings

class ASCampaign(me.Document):
    _id = me.ObjectIdField()
    problemId = me.StringField(required = True)
    campaignId = me.StringField(required = True)
    isNetwork = me.BooleanField(required = True)
    startDate = me.DateTimeField()
    expiredDate = me.DateTimeField()
    priority = me.StringField(required = True)
    campaignType = me.StringField(required = True, db_field='type') 
    total = me.FloatField(required = True)
    placeIds = me.ListField(required = True)
    weights = me.DictField(required = True)
    profiles = me.ListField(required = True)
    createDate = me.DateTimeField(required = False)

    # Meta variables
    meta = {
        'collection': settings.campaign_collection
        }


class ASPlace(me.Document):
    _id = me.ObjectIdField()
    problemId = me.StringField(required = True)
    placeId = me.IntField(required = True)
    ctrs = me.DictField(required = True)
    views = me.DictField(required = True)
    profilesRatio = me.ListField(required = True)
    shareRate = me.FloatField(required = True)
    createDate = me.DateTimeField(required = False)
    shareType = me.StringField()

    # Meta variables
    meta = {
        'collection': settings.place_stat_collection
        }


class ASShareRate(me.Document):
    _id = me.ObjectIdField()
    problemId  = me.StringField(required = True)
    ratio = me.FloatField(required = True)
    createDate = me.DateTimeField(required = False)

    # Meta variables
    meta = {
        'collection': settings.share_rate_collection
        }


class ASResult(me.Document):
    problemId = me.StringField(required= True)
    campaignId = me.StringField(required= True)
    placeId =  me.IntField(required = True)
    date = me.DateTimeField(required = True)
    view = me.FloatField(required = True)
    createDate = me.DateTimeField(required = False)

    # Meta variables
    meta = {
        'collection': settings.output_collection       
        }


class ASProblemInfo(me.Document):
    problemType = me.StringField(required = True)
    name = me.StringField(required = True)
    createDate = me.DateTimeField(required = True)
    lowerRatio = me.FloatField(required = False)

    # Meta variables
    meta = {
        'collection': settings.problem_info_collection
        }


class ASUnplanned(me.Document):
    problemId = me.StringField(required = True)
    campaignId = me.StringField(required = True)
    unplanned = me.FloatField(required = True)
    createDate = me.DateTimeField(required = True)

    meta = {
        'collection': settings.unplanned_collection
        }