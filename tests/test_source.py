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
import asynctest
import asyncio
import json
import websockets
from asynctest import MagicMock
from livebridge.base import StreamingSource
from livebridge_slack.common import SlackClient
from livebridge_slack import SlackSource
from tests import load_json

SLACK_MSG = """{"type":"message","message":{"type":"message","user":"U1F2VML58","text":"Foo baz","edited":{"user":"U1F2VML58","ts":"1475166092.000000"},"ts":"1475157232.000011"},"subtype":"message_changed","hidden":true,"channel":"C1123456","previous_message":{"type":"message","user":"U1F2VML58","text":"Foo baz!","edited":{"user":"U1F2VML58","ts":"1475166025.000000"},"ts":"1475157232.000011"},"event_ts":"1475166092.396510","ts":"1475166092.000018"}"""

class SlackSourceTests(asynctest.TestCase):

    def setUp(self):
        self.token = "baz"
        self.channel = "foo"
        self.source = SlackSource(config={"auth": {"token":self.token}, "channel": self.channel})

    @asynctest.fail_on(unused_loop=False)
    def test_init(self):
        assert self.source.type == "slack"
        assert self.source.mode == "streaming"
        assert self.source.token == self.token
        assert self.source.channel == "foo"
        assert issubclass(SlackSource, SlackClient) == True
        assert issubclass(SlackSource, StreamingSource) == True

    async def test_stop(self):
        self.source.websocket = MagicMock()
        self.source.websocket.close = asynctest.CoroutineMock(return_value=True)
        res = await self.source.stop()
        assert res == True

    async def test_get_ws_url(self):
        api_res = {"url": "wss:example.com"}
        self.source._post = asynctest.CoroutineMock(return_value=api_res)
        res = await self.source._get_ws_url()
        assert res == api_res["url"]
        self.source._post.assert_called_once_with('https://slack.com/api/rtm.start', [('token', 'baz')])

    async def test_listen(self):
            conn = MagicMock(spec=websockets.client.WebSocketClientProtocol)
            conn.open = True
            conn.recv = asynctest.CoroutineMock(return_value=SLACK_MSG)
            conn.close = asynctest.CoroutineMock(return_value=True)
            websockets.connect = asynctest.CoroutineMock(return_value=True)
            async def side_effect():
                conn.open = False
            websockets.connect.return_value=conn

            self.source._get_ws_url = asynctest.CoroutineMock(return_value="ws://example.com")
            self.source._inspect_msg = asynctest.CoroutineMock(return_value=SLACK_MSG, side_effect=["foo", "baz", side_effect()])
            self.source._channel_id = "baz"

            cb = asynctest.CoroutineMock(return_value=True)
            res = await self.source.listen(cb)
            assert self.source._inspect_msg.call_count == 3
            assert cb.call_count == 2

            # fail with exception I
            self.source.websocket = "Test"
            websockets.connect = asynctest.CoroutineMock(side_effect=Exception("Test"))
            res = await self.source.listen(cb)
            assert res == True
            assert self.source.websocket == "Test"

            # fail with exception II
            websockets.connect = asynctest.CoroutineMock(side_effect=ConnectionRefusedError("ConnectionRefusedError"))
            res = await self.source.listen(cb)
            assert res == True
            assert self.source.websocket == "Test"

            # fail with exception III
            websockets.connect = asynctest.CoroutineMock(
                side_effect=websockets.exceptions.ConnectionClosed(code=1006, reason="Testing"))
            res = await self.source.listen(cb)
            assert res == True
            assert self.source.websocket == "Test"

    async def test_inspect(self):
        self.source._channel_id = "C1123456"
        exp_res = json.loads(SLACK_MSG)
        # update
        exp_res["livebridge"] = {"action": "update"}
        res = await self.source._inspect_msg(SLACK_MSG)
        assert res == exp_res
        # create
        exp_res["livebridge"] = {"action": "create"}
        exp_res["hidden"] = False
        res = await self.source._inspect_msg(SLACK_MSG.replace('"hidden":true', '"hidden":false'))
        assert res == exp_res
        # delete
        exp_res["livebridge"] = {"action": "delete"}
        exp_res["hidden"] = True
        exp_res["subtype"] = "message_deleted"
        res = await self.source._inspect_msg(SLACK_MSG.replace('"subtype":"message_changed"', '"subtype":"message_deleted"'))
        assert res == exp_res

    async def test_inspect_unknown_message(self):
        res = await self.source._inspect_msg("{}")
        assert res == None

    async def test_inspect_failing(self):
        res = await self.source._inspect_msg({})
        assert res == None

    async def test_reconnect(self):
        self.source.listen = asynctest.CoroutineMock(return_value=None)
        cb = "test"
        res = self.source.reconnect(cb)
        asyncio.sleep(2)
        assert self.source.listen.call_count == 1
        assert self.source.listen.call_args == asynctest.call(cb)
