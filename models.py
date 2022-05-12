from peewee import *

db = DatabaseProxy()


class Weather(Model):
    day = DateField(formats='%Y-%m-%d')
    date = CharField()
    temperature = CharField()
    weather = CharField()
    wind = CharField()
    humidity = CharField()
    pressure = CharField()
    picture = CharField()

    class Meta:
        database = db