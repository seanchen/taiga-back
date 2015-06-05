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

from taiga.base.api.permissions import (TaigaResourcePermission, HasProjectPerm,
                                        IsProjectOwner, AllowAny, IsSuperUser)


class WikiPagePermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_wiki_pages')
    by_slug_perms = HasProjectPerm('view_wiki_pages')
    create_perms = HasProjectPerm('add_wiki_page')
    update_perms = HasProjectPerm('modify_wiki_page')
    partial_update_perms = HasProjectPerm('modify_wiki_page')
    destroy_perms = HasProjectPerm('delete_wiki_page')
    list_perms = AllowAny()
    render_perms = AllowAny()

class WikiLinkPermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_wiki_links')
    create_perms = HasProjectPerm('add_wiki_link')
    update_perms = HasProjectPerm('modify_wiki_link')
    partial_update_perms = HasProjectPerm('modify_wiki_link')
    destroy_perms = HasProjectPerm('delete_wiki_link')
    list_perms = AllowAny()
