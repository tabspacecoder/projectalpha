# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Document

admin.site.site_header = "Hello World Admin"
admin.site.index_title = "Welcome to the Admin Dashboard"

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    exclude = ('name', 'url', 'uploaded_at')
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('name', 'url', 'uploaded_at')
        return ()

    def get_fields(self, request, obj=None):
        if obj is None:
            return ('file',)
        return ('file', 'name', 'url', 'uploaded_at')
