# -*- coding: utf-8 -*-
#
# Copyright 2016 dpa-infocom GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from livebridge.base import BaseTarget, TargetResponse
from livebridge_slack.common import SlackClient


logger = logging.getLogger(__name__)


class SlackTarget(SlackClient, BaseTarget):

    type = "slack" 

    def get_id_at_target(self, post):
        id_at_target = None
        if post.target_doc:
            id_at_target = post.target_doc.get("ts")
        return id_at_target

    async def post_item(self, post):
        post_url = "{}chat.postMessage".format(self.endpoint)
        data = await self._build_post_data({
            "text": post.content,
            "unfurl_links": True,
        })
        return TargetResponse(await self._post(post_url, data))

    async def update_item(self, post):
        id_at_target = self.get_id_at_target(post)
        if not id_at_target:
            logger.warning("Handling updated item without TARGET-ID: [{}] on {}".format(post.id, self.target_id))
            return False

        update_url = "{}chat.update".format(self.endpoint)
        data = await self._build_post_data({
            "text": post.content,
            "ts": self.get_id_at_target(post),
        })
        return TargetResponse(await self._post(update_url, data))

    async def delete_item(self, post):
        id_at_target = self.get_id_at_target(post)
        if not id_at_target:
            logger.warning("Handling deleted item without TARGET-ID: [{}] on {}".format(post.id, self.target_id))
            return False

        url = "{}chat.delete".format(self.endpoint)
        data = await self._build_post_data({
            "ts": id_at_target,
        })
        return TargetResponse(await self._post(url, data))

    async def handle_extras(self, post):
        pass
