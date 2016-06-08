# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from locust import HttpLocust, TaskSet, task


class UserBehavior(TaskSet):

    @task(1)
    def index(self):
        self.client.get('/')


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
