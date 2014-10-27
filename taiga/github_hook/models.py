# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from taiga.projects.models import Project


def generate_secret():
    return uuid.uuid4().hex


class GitHubHookAttributes(models.Model):
    project = models.OneToOneField(Project, blank=False, null=False,
                    default="change me", related_name="github_hook_attributes",
                    verbose_name=_("git hub"))

    secret = models.CharField(max_length=255, null=False, blank=False,
                    default=generate_secret,
                    verbose_name=_("secret"))

    class Meta:
        verbose_name = "Github hook attributes"
        verbose_name_plural = "Github hook attributes"
