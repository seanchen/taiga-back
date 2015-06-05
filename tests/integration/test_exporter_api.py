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

import pytest

from django.core.urlresolvers import reverse

from .. import factories as f
from taiga.base.utils import json


pytestmark = pytest.mark.django_db


def test_invalid_project_export(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("exporter-detail", args=[1000000])

    response = client.get(url, content_type="application/json")
    assert response.status_code == 404


def test_valid_project_export_with_celery_disabled(client, settings):
    settings.CELERY_ENABLED = False

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_owner=True)
    client.login(user)

    url = reverse("exporter-detail", args=[project.pk])

    response = client.get(url, content_type="application/json")
    assert response.status_code == 200
    response_data = json.loads(response.content.decode("utf-8"))
    assert "url" in response_data


def test_valid_project_export_with_celery_enabled(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_owner=True)
    client.login(user)

    url = reverse("exporter-detail", args=[project.pk])

    response = client.get(url, content_type="application/json")
    assert response.status_code == 202
    response_data = json.loads(response.content.decode("utf-8"))
    assert "export_id" in response_data


def test_valid_project_with_throttling(client, settings):
    settings.CELERY_ENABLED = False
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["import-dump-mode"] = "1/minute"

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_owner=True)
    client.login(user)

    url = reverse("exporter-detail", args=[project.pk])

    response = client.get(url, content_type="application/json")
    assert response.status_code == 200
    response = client.get(url, content_type="application/json")
    assert response.status_code == 429
