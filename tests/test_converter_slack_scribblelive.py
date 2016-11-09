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
from livebridge_slack import SlackScribbleliveConverter

class SlackScribbleliveConverterTest(asynctest.TestCase):

    def setUp(self):
        self.converter = SlackScribbleliveConverter()

    async def test_convert(self):
        post = {"text": "foo"}
        conversion = await self.converter.convert(post)
        assert conversion.content == "foo"

    async def test_convert_failing(self):
        conversion = await self.converter.convert(None)
        assert conversion.content == ""

    async def test_bold(self):
        post = {"text": "*foo* bla*fasel* baz"}
        conversion = await self.converter.convert(post)
        assert conversion.content == "<b>foo</b> bla<b>fasel</b> baz"

    async def test_italic(self):
        post = {"text": "_foo_ bla_fasel_ baz"}
        conversion = await self.converter.convert(post)
        assert conversion.content == "<i>foo</i> bla<i>fasel</i> baz"

    async def test_strike(self):
        post = {"text": "~foo~ bla~fasel~ baz"}
        conversion = await self.converter.convert(post)
        assert conversion.content == "<s>foo</s> bla<s>fasel</s> baz"

    async def test_links(self):
        post = {"text": "foo <https://example.com> baz"}
        conversion = await self.converter.convert(post)
        assert conversion.content == 'foo <a href="https://example.com">https://example.com</a> baz'

        post = {"text": "foo <https://example.com|Example> baz"}
        conversion = await self.converter.convert(post)
        assert conversion.content == 'foo <a href="https://example.com">Example</a> baz'

    async def test_images(self):
        post =  {
        "text": "\nText\n\n<http://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/c55d86a5c5b6144bebe2490f4ce14be671dd7>\n ",
        "attachments": [{
            "image_url": "http://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/c55d86a5c5b6144bebe2490f4ce14be671dd7",
            "from_url": "http://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/c55d86a5c5b6144bebe2490f4ce14be671dd7",
        }],}
        conversion = await self.converter.convert(post)
        assert conversion.content == 'Text<br><br><img src="http://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/c55d86a5c5b6144bebe2490f4ce14be671dd7" />'
