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
from asynctest import MagicMock
from aiohttp.client_exceptions import ClientOSError
from livebridge.base import BaseTarget, BasePost, TargetResponse
from livebridge_slack.common import SlackClient
from livebridge_slack import SlackTarget
from tests import load_json


class TestResponse:
    __test__ = False

    def __init__(self, url, data={}, status=200):
        self.status = status
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass

    async def json(self):
        return self.data

    async def text(self):
        return repr(self.data)


class SlackTargetTests(asynctest.TestCase):

    def setUp(self):
        self.token = "baz"
        self.channel = "foo"
        self.client = SlackTarget(config={"auth": {"token":self.token}, "channel": self.channel})

    @asynctest.fail_on(unused_loop=False)
    def test_init(self):
        assert self.client.type == "slack"
        assert self.client.token == self.token
        assert self.client.channel == "foo"
        assert issubclass(SlackTarget, BaseTarget) == True
        assert issubclass(SlackTarget, SlackClient) == True
        assert isinstance(self.client, BaseTarget) == True
        assert self.client.source_id == "slack-foo"

    @asynctest.fail_on(unused_loop=False)
    def test_get_id_target(self):
        post_data = load_json('post_to_convert.json')

        post = BasePost(post_data)
        post.target_doc = {"ts": 456}
        assert self.client.get_id_at_target(post) == 456

        post.target_doc = {}
        assert self.client.get_id_at_target(post) == None

    async def test_build_post_data(self):
        self.client._channel_id = "123456"
        data = await self.client._build_post_data()
        assert data[0] == ("token", self.token)
        assert data[1] == ("channel", "123456")
        
        params = {
            "ts": "1466511630.000011",
            "parser": "none",
            "text": "Slacky text.",
            "username": "Benutzer",
        }
        data = await self.client._build_post_data(params)
        assert data[0] == ("token", self.token)
        assert data[1] == ("channel", "123456")
        # remove default param token
        del data[0]
        del data[0]
        for d in data:
            assert d[1] == params[d[0]]

    async def test_channel_id(self):
        api_res = {"ok": True, "channels": [
            {"id": "AAAAAA", "name": "bdt-to-weblines", "is_channel": True},
            {"id": "BBBBBB", "name": "foo", "is_channel": True},
            {"id": "CCCCC", "name": "random", "is_channel": True}]}
        self.client._post =  asynctest.CoroutineMock(return_value=api_res)
        channel_id = await self.client.channel_id
        assert channel_id == "BBBBBB"

        # not known
        self.client._channel_id = None
        self.client.channel = "Not"
        channel_id = await self.client.channel_id
        assert channel_id == None

    async def test_post_item(self):
        api_res = {"ok": True, "channel":"ABCDEFG","ts":"1466511630.000011",
                   "message":{
                        "text":"foobaz", "username":"Liveticker",
                        "bot_id":"ABCDEFG", "type":"message",
                        "subtype":"bot_message","ts":"1466511630.000011"}}
        self.client._post =  asynctest.CoroutineMock(return_value=api_res)

        post = MagicMock()
        post.images = []
        post.content = "Test, mit Ü."
        resp = await self.client.post_item(post)
        assert resp == api_res

    async def test_update_item(self):
        api_res = {"ok": True, "channel":"ABCDEFG","ts":"1466511630.000011",
                   "message":{
                        "text":"foobaz", "username":"Liveticker",
                        "bot_id":"ABCDEFG", "type":"message",
                        "subtype":"bot_message","ts":"1466511630.000011"}}
        self.client._post =  asynctest.CoroutineMock(return_value=api_res)

        post = MagicMock()
        post.images = []
        post.content = "Test, mit Ü."
        post.target_doc = {"ts": 456}
        resp = await self.client.update_item(post)
        assert resp == api_res
        assert self.client._post.call_args == asynctest.call('https://slack.com/api/chat.update',
                             [('token', 'baz'), ('channel', None), ('text', 'Test, mit Ü.'), ('ts', 456)])

    async def test_update_item_failin(self):
        self.client.get_id_at_target = lambda x: None
        post = MagicMock()
        post.images = []
        post.content = "Test, mit Ü."
        post.target_doc = {"ts": 456}
        res = await self.client.update_item(post)
        assert res == False

    async def test_delete_item(self):
        self.client._post = asynctest.CoroutineMock(return_value={"foo":"baz"})
        self.client._channel_id = "Foo"
        self.client.get_id_at_target = lambda x: "12345"
        post = MagicMock()
        resp = await self.client.delete_item(post)
        assert type(resp) == TargetResponse
        assert resp == {"foo": "baz"}
        assert self.client._post.call_args == asynctest.call('https://slack.com/api/chat.delete',
            [("token", "baz"), ("channel", "Foo"), ("ts", "12345")])

    async def test_delete_item_failing(self):
        self.client.get_id_at_target = lambda x: None
        post = MagicMock()
        resp = await self.client.delete_item(post)
        assert resp == False

    async def test_handle_extras(self):
        resp = await self.client.handle_extras({})
        assert resp == None

    async def test_common_post(self):
        with asynctest.patch("aiohttp.client.ClientSession.post") as patched:
            patched.return_value = TestResponse(url="http://foo.com", status=201, data={"ok": True})
            res = await self.client._post("https://dpa.com/resource", data={"foo": "bla"}, status=201)
            assert type(res) == dict
            assert res == {"ok": True}

            # failing
            res = await self.client._post("https://dpa.com/resource", status=404)
            assert res == {}

            patched.return_value = TestResponse(url="http://foo.com", status=201, data={"ok": False})
            res = await self.client._post("https://dpa.com/resource", data={"foo": "bla"}, status=201)
            assert res == {}

            patched.side_effect = ClientOSError()
            res = await self.client._post("https://dpa.com/resource", data={"foo": "bla"}, status=201)
            assert res == {}
