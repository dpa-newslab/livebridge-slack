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
import asyncio
import logging
import websockets
import json
from livebridge_slack.common import SlackClient
from livebridge_slack.post import SlackPost
from livebridge.base import StreamingSource


logger = logging.getLogger(__name__)


class SlackSource(SlackClient, StreamingSource):

    type = "slack"

    async def _get_ws_url(self):
        url = "{}rtm.start".format(self.endpoint, None)
        streams = await self._post(url, [("token", self.token)])
        wss_url = streams.get("url")
        return wss_url

    async def _inspect_msg(self, msg_str):
        try:
            msg = json.loads(msg_str)
            msg["livebridge"] = {}
            if msg.get("type") == "message" and msg.get("channel") == await self.channel_id:
                if not msg.get("hidden"):
                    msg["livebridge"]["action"] = "create"
                elif msg.get("subtype") == "message_changed":
                    if msg.get("message") and not msg["message"].get("attachements"):
                        msg["livebridge"]["action"] = "update"
                elif msg.get("subtype") == "message_deleted":
                    msg["livebridge"]["action"] = "delete"
            else:
                logger.debug("DATA: {}".format(msg_str))
                return None
            return msg
        except Exception as e:
            logger.debug("Failing inspection of msg: {}".format(e))
        return None

    def reconnect(self, callback):
        logger.debug("Reconnecting...")
        asyncio.ensure_future(self.listen(callback))

    async def listen(self, callback):
        try:
            wss_url = await self._get_ws_url()
            channel_id = await self.channel_id
            logger.info("Listening to ChannelID: {}".format(channel_id))
            logger.info("Connecting to {}".format(wss_url))
            self.websocket = await websockets.connect(wss_url)
            while self.websocket.open:
                msg = await self.websocket.recv()
                doc = await self._inspect_msg(msg)
                if doc:
                    asyncio.ensure_future(callback([SlackPost(doc)]))
        except ConnectionRefusedError as e:
            logger.error("Exception listening to websocket {} {}: {}".format(self.type, self.channel, e))
            asyncio.get_event_loop().call_later(5, self.reconnect, callback)
        except websockets.exceptions.ConnectionClosed as e:
            logger.error("Webocket connection closed: {} {} {}".format(self.type, self.channel, e))
            if e.code == 1006:
                asyncio.get_event_loop().call_later(5, self.reconnect, callback)
        except Exception as e:
            logger.error("Exception listening to websocket {} {} {}".format(self.type, self.channel, e))
        return True

    async def stop(self):
        logger.debug("Stopping slack websocket")
        asyncio.ensure_future(self.websocket.close(reason="Stopping bridge"))
        return True
