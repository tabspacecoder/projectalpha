# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Document(models.Model):
    file = models.FileField(upload_to='uploads/')
    name = file.name
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name