# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.contrib import admin
from django.urls import path

from .favicon import favicon_urlpatterns
from .views.front_page import FrontPageView
from .views.rss_feed import WnppNewsFeedView

urlpatterns = [
    path('', FrontPageView.as_view(), name='front_page'),
    path('admin/', admin.site.urls),
    path('news.php5', WnppNewsFeedView(), name='news'),
] + favicon_urlpatterns()
