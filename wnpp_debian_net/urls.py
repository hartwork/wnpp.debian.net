# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.contrib import admin
from django.urls import path

from .views.front_page import FrontPageView

urlpatterns = [
    path('', FrontPageView.as_view(), name='front_page'),
    path('admin/', admin.site.urls),
]
