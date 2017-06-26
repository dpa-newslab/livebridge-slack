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
import aiohttp
import logging


logger = logging.getLogger(__name__)


class SlackClient(object):

    type = "slack"

    def __init__(self, *, config={}, **kwargs):
        self.token = config.get("auth", {}).get("token")
        self.channel = config.get("channel")
        self.endpoint = "https://slack.com/api/"
        self.target_id = "{}-{}".format(self.type, self.channel)
        self._channel_id = None
        self.last_updated = None

    @property
    def source_id(self):
        return "{}-{}".format(self.type, self.channel)

    @property
    async def channel_id(self):
        """Lookups channel_id for channel from slack api."""
        if not self._channel_id:
            url = "{}channels.list".format(self.endpoint)
            res = await self._post(url, [("token", self.token)])
            for c in res.get("channels", []):
                if c.get("is_channel") == True and c.get("name") == self.channel:
                    self._channel_id = c["id"]
                    break
        return self._channel_id

    async def _build_post_data(self, params={}):
        data = [
            ("token", self.token),
            ("channel", await self.channel_id),
        ]
        for k in sorted(params.keys()):
            if params.get(k):
                data.append((k, params[k]))
        return data

    async def _post(self, url, data=[], *, images=[], status=200):
        try:
            logger.debug("POST: {}".format(url))
            with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as resp:
                    if resp.status == status:
                        msg = await resp.json()
                        if msg.get("ok") == True:
                            return msg
                        else:
                            logger.error("Error when posting to slack: {}".format(msg))
                    else:
                        logger.debug("POST request failed with status [{}], expected {}".format(resp.status, status))
                        logger.debug(await resp.text())
        except aiohttp.client_exceptions.ClientOSError as e:
            logger.error("POST request failed for [{}] on {}".format(self.channel, self.endpoint))
            logger.error(e)
        return {}
