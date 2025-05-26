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

    def save(self, *args, **kwargs):
        if self.file and self._state.adding:
            self.process_file(self.file)
        super().save(*args, **kwargs)

    def process_file(self, uploaded_file):
        uploaded_file.seek(0)
        file_data = uploaded_file.read()
        print(f"File size: {len(file_data)} bytes")