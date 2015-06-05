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

import datetime

from optparse import make_option

from django.db.models.loading import get_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from djmail.template_mail import MagicMailBuilder, InlineCSSTemplateMail

from taiga.projects.models import Project, Membership
from taiga.projects.history.models import HistoryEntry
from taiga.projects.history.services import get_history_queryset_by_model_instance
from taiga.users.models import User


class Command(BaseCommand):
    args = '<email>'
    option_list = BaseCommand.option_list + (
        make_option('--locale', '-l', default=None, dest='locale',
            help='Send emails in an specific language.'),
    )

    help = 'Send an example of all emails'

    def handle(self, *args, **options):
        if len(args) != 1:
            print("Usage: ./manage.py test_emails <email-address>")
            return

        locale = options.get('locale')
        test_email = args[0]

        mbuilder = MagicMailBuilder(template_mail_cls=InlineCSSTemplateMail)

        # Register email
        context = {"lang": locale, "user": User.objects.all().order_by("?").first(), "cancel_token": "cancel-token"}
        email = mbuilder.registered_user(test_email, context)
        email.send()

        # Membership invitation
        membership = Membership.objects.order_by("?").filter(user__isnull=True).first()
        membership.invited_by = User.objects.all().order_by("?").first()
        membership.invitation_extra_text = "Text example, Text example,\nText example,\n\nText example"

        context = {"lang": locale, "membership": membership}
        email = mbuilder.membership_invitation(test_email, context)
        email.send()

        # Membership notification
        context = {"lang": locale, "membership": Membership.objects.order_by("?").filter(user__isnull=False).first()}
        email = mbuilder.membership_notification(test_email, context)
        email.send()

        # Feedback
        context = {
            "lang": locale,
            "feedback_entry": {
                "full_name": "Test full name",
                "email": "test@email.com",
                "comment": "Test comment",
            },
            "extra": {
                "key1": "value1",
                "key2": "value2",
            },
        }
        email = mbuilder.feedback_notification(test_email, context)
        email.send()

        # Password recovery
        context = {"lang": locale, "user": User.objects.all().order_by("?").first()}
        email = mbuilder.password_recovery(test_email, context)
        email.send()

        # Change email
        context = {"lang": locale, "user": User.objects.all().order_by("?").first()}
        email = mbuilder.change_email(test_email, context)
        email.send()

        # Export/Import emails
        context = {
            "lang": locale,
            "user": User.objects.all().order_by("?").first(),
            "project": Project.objects.all().order_by("?").first(),
            "error_subject": "Error generating project dump",
            "error_message": "Error generating project dump",
        }
        email = mbuilder.export_error(test_email, context)
        email.send()
        context = {
            "lang": locale,
            "user": User.objects.all().order_by("?").first(),
            "error_subject": "Error importing project dump",
            "error_message": "Error importing project dump",
        }
        email = mbuilder.import_error(test_email, context)
        email.send()

        deletion_date = timezone.now() + datetime.timedelta(seconds=60*60*24)
        context = {
            "lang": locale,
            "url": "http://dummyurl.com",
            "user": User.objects.all().order_by("?").first(),
            "project": Project.objects.all().order_by("?").first(),
            "deletion_date": deletion_date,
        }
        email = mbuilder.dump_project(test_email, context)
        email.send()

        context = {
            "lang": locale,
            "user": User.objects.all().order_by("?").first(),
            "project": Project.objects.all().order_by("?").first(),
        }
        email = mbuilder.load_dump(test_email, context)
        email.send()

        # Notification emails
        notification_emails = [
            ("issues.Issue", "issues/issue-change"),
            ("issues.Issue", "issues/issue-create"),
            ("issues.Issue", "issues/issue-delete"),
            ("tasks.Task", "tasks/task-change"),
            ("tasks.Task", "tasks/task-create"),
            ("tasks.Task", "tasks/task-delete"),
            ("userstories.UserStory", "userstories/userstory-change"),
            ("userstories.UserStory", "userstories/userstory-create"),
            ("userstories.UserStory", "userstories/userstory-delete"),
            ("milestones.Milestone", "milestones/milestone-change"),
            ("milestones.Milestone", "milestones/milestone-create"),
            ("milestones.Milestone", "milestones/milestone-delete"),
            ("wiki.WikiPage", "wiki/wikipage-change"),
            ("wiki.WikiPage", "wiki/wikipage-create"),
            ("wiki.WikiPage", "wiki/wikipage-delete"),
        ]

        context = {
            "lang": locale,
            "project": Project.objects.all().order_by("?").first(),
            "changer": User.objects.all().order_by("?").first(),
            "history_entries": HistoryEntry.objects.all().order_by("?")[0:5],
            "user": User.objects.all().order_by("?").first(),
        }

        for notification_email in notification_emails:
            model = get_model(*notification_email[0].split("."))
            snapshot = {
                "subject": "Tests subject",
                "ref": 123123,
                "name": "Tests name",
                "slug": "test-slug"
            }
            queryset = model.objects.all().order_by("?")
            for obj in queryset:
                end = False
                entries = get_history_queryset_by_model_instance(obj).filter(is_snapshot=True).order_by("?")

                for entry in entries:
                    if entry.snapshot:
                        snapshot = entry.snapshot
                        end = True
                        break
                if end:
                    break
            context["snapshot"] = snapshot

            cls = type("InlineCSSTemplateMail", (InlineCSSTemplateMail,), {"name": notification_email[1]})
            email = cls()
            email.send(test_email, context)
