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

import io
import csv

from taiga.base.utils import db, text
from taiga.projects.history.services import take_snapshot
from taiga.events import events

from . import models


def get_tasks_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of tasks.

    :param bulk_data: List of tasks in bulk format.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of `Task` instances.
    """
    return [models.Task(subject=line, **additional_fields)
            for line in text.split_in_lines(bulk_data)]


def create_tasks_in_bulk(bulk_data, callback=None, precall=None, **additional_fields):
    """Create tasks from `bulk_data`.

    :param bulk_data: List of tasks in bulk format.
    :param callback: Callback to execute after each task save.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of created `Task` instances.
    """
    tasks = get_tasks_from_bulk(bulk_data, **additional_fields)
    db.save_in_bulk(tasks, callback, precall)
    return tasks


def update_tasks_order_in_bulk(bulk_data:list, field:str, project:object):
    """
    Update the order of some tasks.
    `bulk_data` should be a list of tuples with the following format:

    [(<task id>, {<field>: <value>, ...}), ...]
    """
    task_ids = []
    new_order_values = []
    for task_data in bulk_data:
        task_ids.append(task_data["task_id"])
        new_order_values.append({field: task_data["order"]})

    events.emit_event_for_ids(ids=task_ids,
                              content_type="tasks.task",
                              projectid=project.pk)

    db.update_in_bulk_with_ids(task_ids, new_order_values, model=models.Task)


def snapshot_tasks_in_bulk(bulk_data, user):
    task_ids = []
    for task_data in bulk_data:
        try:
            task = models.Task.objects.get(pk=task_data['task_id'])
            take_snapshot(task, user=user)
        except models.UserStory.DoesNotExist:
            pass


def tasks_to_csv(project, queryset):
    csv_data = io.StringIO()
    fieldnames = ["ref", "subject", "description", "user_story", "milestone", "owner",
                  "owner_full_name", "assigned_to", "assigned_to_full_name",
                  "status", "is_iocaine", "is_closed", "us_order",
                  "taskboard_order", "attachments", "external_reference", "tags"]
    for custom_attr in project.taskcustomattributes.all():
        fieldnames.append(custom_attr.name)

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for task in queryset:
        task_data = {
            "ref": task.ref,
            "subject": task.subject,
            "description": task.description,
            "user_story": task.user_story.ref if task.user_story else None,
            "milestone": task.milestone.name if task.milestone else None,
            "owner": task.owner.username,
            "owner_full_name": task.owner.get_full_name(),
            "assigned_to": task.assigned_to.username if task.assigned_to else None,
            "assigned_to_full_name": task.assigned_to.get_full_name() if task.assigned_to else None,
            "status": task.status.name,
            "is_iocaine": task.is_iocaine,
            "is_closed": task.status.is_closed,
            "us_order": task.us_order,
            "taskboard_order": task.taskboard_order,
            "attachments": task.attachments.count(),
            "external_reference": task.external_reference,
            "tags": ",".join(task.tags or []),
        }
        for custom_attr in project.taskcustomattributes.all():
            value = task.custom_attributes_values.attributes_values.get(str(custom_attr.id), None)
            task_data[custom_attr.name] = value

        writer.writerow(task_data)

    return csv_data
