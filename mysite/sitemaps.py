# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = 'daily'

    def items(self):
        return ['migpt:index', 'migpt:create_interview_session', 'migpt:view_profile', 'migpt:update_profile', 'migpt:contact', 'migpt:feedback', 'migpt:display_result']

    def location(self, item):
        return reverse(item)
