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

from taiga.projects.models import Project
from taiga.projects.issues.models import Issue

from .exceptions import ActionSyntaxException

class BaseEventHook(object):

    def __init__(self, payload):
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
        if message is None:
            return

        p = re.compile("TG-([-\w]+)-(\d+) +#(\w+)")
        m = p.search(message)
        if m:
            project_slug = m.group(1)
            ref = m.group(2)
            action = m.group(3)
            self._execute_action(project_slug, ref, action)

    def _execute_action(self, project_slug, ref, action):
        # Closing set the issue in the first one of the closed project statuses
        if action == "close":
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise ActionSyntaxException(_("The project doesn't exist"))

            try:
                issue = Issue.objects.get(project=project, ref=ref)
            except Issue.DoesNotExist:
                raise ActionSyntaxException(_("The issue doesn't exist"))

            status = project.issue_statuses.filter(is_closed=True).order_by("order").first()
            if status is None:
                raise ActionSyntaxException(_("The project needs at least one closed status for issues"))

            issue.status = status
            issue.save()
