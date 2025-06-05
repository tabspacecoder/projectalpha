from __future__ import unicode_literals

from django.db import models
import os
from django.utils import timezone
from django.core.exceptions import ValidationError
from storages.backends.s3boto3 import S3Boto3Storage
from .vector_store_opensearch import vectorize_pdf_and_index_in_opensearch_bulk_v3

# import boto3
# session = boto3.Session()
# credentials = session.get_credentials().get_frozen_credentials()
# print("Access Key:", credentials.access_key)
# print("Secret Key:", credentials.secret_key)
# print("Token:", credentials.token)

s3_storage = S3Boto3Storage()
# Create your models here.
def validate_file_extension(value):
    valid_extensions = ['.pdf']
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

        self.process_file(uploaded_file=self.file, name=self.file.name)
        name = s3_storage.save(name=self.file.name, content=self.file)
        print("Uploaded File Name : ",name)

        if is_new:
            self.name = name.split('uploads/')[1]
            self.url = s3_storage.url(name)
            # file = s3_storage.open('uploads/' + self.name, mode='r')
            # print(file.read())
            super().save(update_fields=['name', 'url'])

    def __str__(self):
        return self.name or "Unnamed Document"

    def process_file(self, uploaded_file, name):
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        #Opensearch model loading
        vectorize_pdf_and_index_in_opensearch_bulk_v3(file_bytes=file_bytes, filename=name.split('uploads/')[1])



        #Fiass model loading
        # filename_prefix = os.path.splitext(os.path.basename(self.file.name))[0]
        # num_chunks = vectorize_pdf_and_upload_to_s3(file_bytes, filename_prefix)
        # print(f"Processed and uploaded {num_chunks} chunks to S3.")
