# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.contrib import admin
from django.urls import path

from .views.favicon import favicon_urlpatterns
from .views.front_page import FrontPageView
from .views.rss_feed import WnppNewsFeedView
from .views.security_txt import security_txt_urlpatterns
from .views.static_files import staticfiles_urlpatterns

urlpatterns = [
    path('', FrontPageView.as_view(), name='front_page'),
    path('admin/', admin.site.urls),
    path('news.php5', WnppNewsFeedView(), name='news'),
] + favicon_urlpatterns() + staticfiles_urlpatterns() + security_txt_urlpatterns()
