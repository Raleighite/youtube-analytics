from peewee import *

db = SqliteDatabase('youtubedata.db')


class Video (object):
    video_id = CharField(max_length=14, primary_key=True)
    video_title = TextField()
    video_views = IntegerField()
    video_favorites = IntegerField()
    video_favorites_removed = IntegerField()
    date_published = DateTimeField()  #    DatePublished
    channel = CharField(max_length=250)  #    Channel video lives on
    language = CharField(max_length=100) #    Language
    video_description = TextField() #    Video Description
    comments = IntegerField()
    video_length = FloatField() #    Video Lengeth
    video_likes = IntegerField()
    video_dislikes = IntegerField()
    video_shares = IntegerField()
    subscribers_earned = IntegerField()
    video_retention = IntegerField()

    class Meta:
        database = db


def initialize():
    """Create the database table unless it already exists"""
    db.connect()
    db.create_tables([Video], safe=True)

