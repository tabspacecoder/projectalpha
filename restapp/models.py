# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import os
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

s3_storage = S3Boto3Storage()
# Create your models here.
def validate_file_extension(value):
    valid_extensions = ['.pdf', '.txt']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported file extension: {ext}. Allowed types: {", ".join(valid_extensions)}')
class Document(models.Model):
    file = models.FileField(upload_to='uploads/', validators=[validate_file_extension])
    name = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        is_new = self._state.adding and self.file

        super().save(*args, **kwargs)

        self.process_file(self.file)
        name = s3_storage.save(name=self.file.name, content=self.file)

        if is_new:
            self.name = name.split('uploads/')[1]
            self.url = s3_storage.url(name)
            # file = s3_storage.open('uploads/' + self.name, mode='r')
            # print(file.read())
            super().save(update_fields=['name', 'url'])

    def __str__(self):
        return self.name or "Unnamed Document"

    def process_file(self, uploaded_file):
        uploaded_file.seek(0)
        file_data = uploaded_file.read() # True if uploaded
        # print(default_storage.__class__)
        print(f"File size: {len(file_data)} bytes")