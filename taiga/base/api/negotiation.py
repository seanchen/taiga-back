# Copyright (C) 2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2015 David Barragán <bameda@dbarragan.com>
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

# This code is partially taken from django-rest-framework:
# Copyright (c) 2011-2014, Tom Christie

"""
Content negotiation deals with selecting an appropriate renderer given the
incoming request.  Typically this will be based on the request's Accept header.
"""

from django.http import Http404

from taiga.base import exceptions
from .settings import api_settings

from .utils.mediatypes import order_by_precedence
from .utils.mediatypes import media_type_matches
from .utils.mediatypes import _MediaType


class BaseContentNegotiation(object):
    def select_parser(self, request, parsers):
        raise NotImplementedError(".select_parser() must be implemented")

    def select_renderer(self, request, renderers, format_suffix=None):
        raise NotImplementedError(".select_renderer() must be implemented")


class DefaultContentNegotiation(BaseContentNegotiation):
    settings = api_settings

    def select_parser(self, request, parsers):
        """
        Given a list of parsers and a media type, return the appropriate
        parser to handle the incoming request.
        """
        for parser in parsers:
            if media_type_matches(parser.media_type, request.content_type):
                return parser
        return None

    def select_renderer(self, request, renderers, format_suffix=None):
        """
        Given a request and a list of renderers, return a two-tuple of:
        (renderer, media type).
        """
        # Allow URL style format override.  eg. "?format=json
        format_query_param = self.settings.URL_FORMAT_OVERRIDE
        format = format_suffix or request.QUERY_PARAMS.get(format_query_param)

        if format:
            renderers = self.filter_renderers(renderers, format)

        accepts = self.get_accept_list(request)

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isni't as bad as it first looks :)
        #     Worst case is we"re looping over len(accept_list) * len(self.renderers)
        for media_type_set in order_by_precedence(accepts):
            for renderer in renderers:
                for media_type in media_type_set:
                    if media_type_matches(renderer.media_type, media_type):
                        # Return the most specific media type as accepted.
                        if (_MediaType(renderer.media_type).precedence >
                            _MediaType(media_type).precedence):
                            # Eg client requests "*/*"
                            # Accepted media type is "application/json"
                            return renderer, renderer.media_type
                        else:
                            # Eg client requests "application/json; indent=8"
                            # Accepted media type is "application/json; indent=8"
                            return renderer, media_type

        raise exceptions.NotAcceptable(available_renderers=renderers)

    def filter_renderers(self, renderers, format):
        """
        If there is a ".json" style format suffix, filter the renderers
        so that we only negotiation against those that accept that format.
        """
        renderers = [renderer for renderer in renderers
                     if renderer.format == format]
        if not renderers:
            raise Http404
        return renderers

    def get_accept_list(self, request):
        """
        Given the incoming request, return a tokenised list of media
        type strings.

        Allows URL style accept override.  eg. "?accept=application/json"
        """
        header = request.META.get("HTTP_ACCEPT", "*/*")
        header = request.QUERY_PARAMS.get(self.settings.URL_ACCEPT_OVERRIDE, header)
        return [token.strip() for token in header.split(",")]
