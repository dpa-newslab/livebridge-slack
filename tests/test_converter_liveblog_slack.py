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
import os.path
from livebridge_slack import LiveblogSlackConverter
from livebridge.base import ConversionResult
from tests import load_json

class SlackConverterTest(asynctest.TestCase):

    def setUp(self):
        self.converter = LiveblogSlackConverter()

    async def test_simple_conversion(self):
        post = load_json('post_to_convert.json')
        conversion = await self.converter.convert(post)
        assert type(conversion) == ConversionResult
        assert len(conversion.content) >= 1
        assert conversion.content == """\n*Text*  mit ein parr _Formatierungen_. Und einem <http://dpa.de|Link>. Und weiterer ~Text~.\n\n\nhttp://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/aa7c892f1b1b7df17f635106e27c55d86a5c5b6144bebe2490f4ce14be671dd7\n\nGähn  _(Mich)_ \nListen:\n • Eins\n • Zwei\n • Drei\n\n\n • u1\n • u2\n • u3\n\n\n>*Mit dem Wissen wächst der Zweifel.*\n> • _Johann Wolfgang von Goethe_\n\n\nNochmal _*abschließender* _ Text.\n\nhttps://twitter.com/dpa_live/status/775991579676909568\n"""
        await self.converter.remove_images(conversion.images)

    async def test_simple_conversion_failing(self):
        # let it fail with catched exception
        post = load_json('post_to_convert.json')
        del post["groups"][1]["refs"]
        conversion = await self.converter.convert(post)
        assert conversion.content == ""
        assert conversion.images == []

    async def test_convert_quote(self):
        item = {"item": {"meta": {"quote": "Zitat", "credit": "Urheber"}}}
        res = await self.converter._convert_quote(item)
        assert res == ">*Zitat*\n> • _Urheber_\n\n"

    async def test_convert_quote_without_credit(self):
        item = {"item": {"meta": {"quote": "Zitat"}}}
        res = await self.converter._convert_quote(item)
        assert res == ">*Zitat*\n"

    async def test_convert_text(self):
        text = "<p>Test&nbsp;  <b>&nbsp; </b>ein<b> Text     <br><br> mit</b>ohne  <b><br></b>  <i>test</i> <strike>foo</strike>baz<br></p>"
        text += "<ol><li>eins</li><li>zwei</li><li>drei</li></ol>"
        text += "<ul><li>EINS</li><li>ZWEI</li><li>DREI</li></ul>"
        res = await self.converter._convert_text({"item":{"text": text}})
        assert res == "\nTest   ein *Text \n mit* ohne \n  _test_ ~foo~baz\n\n • eins\n • zwei\n • drei\n\n • EINS\n • ZWEI\n • DREI\n\n\n"

    async def test_convert_image(self):
        post = load_json('post_to_convert.json')
        img_item = post["groups"][1]["refs"][1]
        res, _ = await self.converter._convert_image(img_item)
        assert res == "\nhttp://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/aa7c892f1b1b7df17f635106e27c55d86a5c5b6144bebe2490f4ce14be671dd7\n\nGähn  _(Mich)_ "

        img_item["item"]["meta"]["caption"] = ""
        img_item["item"]["meta"]["credit"] = ""
        res, _ = await self.converter._convert_image(img_item)
        assert res == "\nhttp://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/aa7c892f1b1b7df17f635106e27c55d86a5c5b6144bebe2490f4ce14be671dd7\n "

    async def test_convert_image_exception(self):
        res, _ = await self.converter._convert_image({})
        assert res == ""

    async def test_twitter(self):
        tweet_item = {
            'item': {
                'meta': {
                    'html': '<div id="_axdhzruve">\n     <blockquote class="twitter-tweet">\n         <p>\nDeutsche Sprache, schwere Sprache <script>\n    window.twttr = (function(d, s, id) {\n        var js, fjs = d.getElementsByTagName(s)[0],t = window.twttr || {};\n        if (d.getElementById(id)) return t; js = d.createElement(s);js.id = id;\n        js.src = "https://platform.twitter.com/widgets.js";\n        fjs.parentNode.insertBefore(js, fjs); t._e = [];\n        t.ready = function(f) {t._e.push(f);}; return t;}(document, "script", "twitter-wjs"));\n    window.twttr.ready(function(){\n        window.twttr.widgets.load(document.getElementById("_axdhzruve"));\n    });\n</script>',
                    'original_url': 'https://twitter.com/dpa_live/status/775658483400183808',
                },
                'item_type': 'embed',
            }
        }
        assert "\n"+tweet_item["item"]["meta"]["original_url"]+"\n" == await self.converter._convert_embed(tweet_item)

        del tweet_item["item"]["meta"]["original_url"]
        assert "" == await self.converter._convert_embed(tweet_item)

    async def test_youtube(self):
        tweet_item = {
            'item': {
                'meta': {
                    'original_url': 'https://www.youtube.com/watch?v=wq1R93UMqlk',
                },
                'item_type': 'embed',
            }
        }
        assert "\n"+tweet_item["item"]["meta"]["original_url"]+"\n" == await self.converter._convert_embed(tweet_item)

        del tweet_item["item"]["meta"]["original_url"]
        assert "" == await self.converter._convert_embed(tweet_item)
