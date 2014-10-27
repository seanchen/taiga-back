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

import re

from django.utils.translation import ugettext_lazy as _

from taiga.projects.models import Project, IssueStatus, TaskStatus, UserStoryStatus

from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory

from .exceptions import ActionSyntaxException

class BaseEventHook(object):

    def __init__(self, project, payload):
        self.project = project
        self.payload = payload

    def process_event(self):
        raise NotImplementedError("process_event must be overwritten")


class PushEventHook(BaseEventHook):

    def process_event(self):
        if self.payload is None:
            return

        commits = self.payload.get("commits", [])
        for commit in commits:
            message = commit.get("message", None)
            self._process_message(message)

    def _process_message(self, message):
        """
          The message we will be looking for seems like
            TG-XX #yyyyyy
          Where:
            XX: is the ref for us, issue or task
            yyyyyy: is the status slug we are setting
        """
        if message is None:
            return

        p = re.compile("TG-(\d+) +#([-\w]+)")
        m = p.search(message)
        if m:
            ref = m.group(1)
            status_slug = m.group(2)
            self._change_status(ref, status_slug)

    def _change_status(self, ref, status_slug):
        if Issue.objects.filter(project=self.project, ref=ref).exists():
            modelClass = Issue
            statusClass = IssueStatus
        elif Task.objects.filter(ref=ref).exists():
            modelClass = Task
            statusClass = TaskStatus
        elif UserStory.objects.filter(ref=ref).exists():
            modelClass = UserStory
            statusClass = UserStoryStatus
        else:
            raise ActionSyntaxException(_("The referenced element doesn't exist"))

        element = modelClass.objects.get(project=self.project, ref=ref)

        try:
            status = statusClass.objects.get(project=self.project, slug=status_slug)
        except IssueStatus.DoesNotExist:
            raise ActionSyntaxException(_("The status doesn't exist"))

        element.status = status
        element.save()

class IssuesEventHook(BaseEventHook):
    def process_event(self):
        if self.payload.get('action', None) != "opened":
            return

        subject = self.payload.get('issue', {}).get('title', None)
        description = self.payload.get('issue', {}).get('body', None)
        github_reference = self.payload.get('issue', {}).get('number', None)

        if not all([subject, description, github_reference]):
            raise ActionSyntaxException(_("Invalid issue information"))

        Issue.objects.create(
            project=self.project,
            subject=subject,
            description=description,
            status=self.project.default_issue_status,
            type=self.project.default_issue_type,
            severity=self.project.default_severity,
            priority=self.project.default_priority,
            external_reference=['github', github_reference],
            owner=self.project.owner
        )
