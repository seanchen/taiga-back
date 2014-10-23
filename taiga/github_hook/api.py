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

import json
import hmac
import hashlib

from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _

from taiga.base.api.viewsets import GenericViewSet

from . import event_hooks

#TODO: remove this one and read it when necesary from the project attributes
HOOK_SECRET_KEY = "tpnIwJDz4e".encode("utf-8")

class Http401(APIException):
    status_code = 401


class GitHubViewSet(GenericViewSet):
    # We don't want rest framework to parse the request body and transform it in
    # a dict in request.DATA, we need it raw
    parser_classes = ()

    # This dict associates the event names we are listening for (https://developer.github.com/webhooks/#events)
    event_hooks = {
        "push": event_hooks.push
    }

    def _validate_signature(self, request):
        x_hub_signature = request.META.get("HTTP_X_HUB_SIGNATURE", None)
        if not x_hub_signature:
            return False

        sha_name, signature = x_hub_signature.split('=')
        if sha_name != 'sha1':
            return False

        # HMAC requires its key to be bytes, but data is strings.
        mac = hmac.new(HOOK_SECRET_KEY, msg=request.body,digestmod=hashlib.sha1)
        return hmac.compare_digest(mac.hexdigest(), signature)

    def create(self, request, *args, **kwargs):
        if not self._validate_signature(request):
            raise Http400(_("Bad signature"))

        event_name = request.META.get("HTTP_X_GITHUB_EVENT", None)
        payload = json.loads(request.body.decode("utf-8"))

        #TODO: remove prints
        print("Event: ", event_name)
        print(payload)

        event_hook = self.event_hooks.get(event_name, None)
        if event_hook is not None:
            event_hook(payload)

        return Response({})
