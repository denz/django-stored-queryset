from django.db import models

class Rel0(models.Model):
    pass

class TModel(models.Model):
    headline = models.CharField(max_length=64)
    related = models.ManyToManyField('stored.rel0')
