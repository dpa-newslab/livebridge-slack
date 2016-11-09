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
import bleach
import logging
import re

from livebridge.base import BaseConverter, ConversionResult

logger = logging.getLogger(__name__)

class LiveblogSlackConverter(BaseConverter):

    source = "liveblog"
    target = "slack"

    async def _convert_text(self, item):
        logger.debug("CONVERTING TEXT")
        content = "\n"+item["item"]["text"]
        content = content.replace("&nbsp;", " ")
        content = bleach.clean(content, tags=["p", "br", "b", "i", "strike", "ul", "li", "ol", "a", "div"], strip=True)
        content = re.sub(r'<a.*?href="([^"]*)".*?>(.*?)</a>', '<\\1|\\2>', content, flags=re.I|re.M)
        content = content.replace("<ol>", "").replace("</ol>", "\n")
        content = re.sub(r'[ ]+', ' ', content)
        content = re.sub(r'<b> ', ' <b>', content)
        content = re.sub(r' </b>', '</b> ', content)
        content = re.sub(r'<i> ', ' <i>', content)
        content = re.sub(r' </i>', '</i> ', content)
        content = re.sub(r'<b>[ ]*</b>', ' ', content)
        content = re.sub(r'<i>[ ]*</i>', ' ', content)
        content = content.replace("<ul>", "").replace("</ul>", "\n")
        content = content.replace("</li>", "\n")
        content = content.replace("<li>", " • ")
        content = content.replace("</p>", "\n")
        content = content.replace("</div>", "\n")
        content = content.replace("<b>", "*")
        content = content.replace("</b>", "* ")
        content = content.replace("<br><br>", "<br>")
        content = content.replace("<br>", "\n")
        content = re.sub(r'<\/?i>', '_', content)
        content = re.sub(r'<\/?strike>', '~', content)
        content = re.sub('<(a|br|div|p)>', '', content)
        content = content.replace("«_", "_«")
        content = content.replace("_»", "»_")
        content = content.replace("«*", "*«")
        content = content.replace("*»", "»*")
        content = content.replace(" ** ", " ")
        content = content.replace("\n**", " ")
        content = content.replace("*\n*", "\n")
        return content+"\n"

    async def _convert_quote(self, item):
        logger.debug("CONVERTING QUOTE")
        meta = item["item"]["meta"]
        content = ">*{}*\n".format(meta.get("quote","").replace("\n", " "))
        if meta.get("credit"):
            content += "> • _{}_\n\n".format(meta.get("credit", ""))
        return content

    async def _convert_image(self, item):
        logger.debug("CONVERTING IMAGE")
        content = ""
        tmp_path = None
        try:
            # handle image
            image_data = item["item"]["meta"]["media"]["renditions"]["viewImage"]
            if image_data.get("href"):
                content += "\n{}\n".format(image_data["href"])
            # handle text
            caption = item["item"]["meta"]["caption"]
            if caption:
                content += "\n{} ".format(caption)
            credit = item["item"]["meta"]["credit"]
            if credit:
                content += " _({})_ ".format(credit)
            else:
                # assure at last a whitespace!
                content += " "
        except Exception as e:
            logger.error("SLACK: Fatal error when converting image.")
            logger.exception(e)
        return content, tmp_path

    async def _convert_embed(self, item):
        logger.debug("CONVERTING EMBED")
        content = ""
        meta = item["item"]["meta"]
        if meta.get("original_url"):
            if meta.get("html", "").find('class="twitter-tweet"') > -1 or \
               meta["original_url"].find("youtube") > -1:
                content = "\n{}\n".format(meta["original_url"])
        return content

    async def convert(self, post):
        content =  ""
        images = []
        try:
            for g in post.get("groups", []):
                if g["id"] != "main":
                    continue

                for item in g["refs"]:
                    if item["item"]["item_type"] == "text":
                        content += await self._convert_text(item)
                    elif item["item"]["item_type"] == "quote":
                        content += await self._convert_quote(item)
                    elif item["item"]["item_type"] == "image":
                        img_text, _ = await self._convert_image(item)
                        content += img_text
                    elif item["item"]["item_type"] == "embed":
                        content += await self._convert_embed(item)
        except Exception as e:
            logger.error("Converting to slack post failed.")
            logger.exception(e)
        return ConversionResult(content=content)
