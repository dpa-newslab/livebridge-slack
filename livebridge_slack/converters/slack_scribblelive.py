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
import re
from livebridge.base import BaseConverter, ConversionResult

logger = logging.getLogger(__name__)

class SlackScribbleliveConverter(BaseConverter):

    source = "slack"
    target = "scribble"

    async def convert(self, post):
        content =  ""
        try:
            msg = post.get("message", post)
            content = msg.get("text", "").strip()
            for a in msg.get("attachments", []):
                if a.get("from_url"):
                    content = content.replace('<{}>'.format(a["from_url"]), '<img src="{}" />'.format(a["from_url"]))
            content = re.sub(r'\*([^\*]*)\*?', "<b>\\1</b>", content, re.I|re.M)
            content = re.sub(r'\_([^\_]*)\_?', "<i>\\1</i>", content, re.I|re.M)
            content = re.sub(r'\~([^\~]*)\~?', "<s>\\1</s>", content, re.I|re.M)
            content = re.sub(r'\<(http[^\>\|]*)\|([^\>]*)\>?', '<a href="\\1">\\2</a>', content, re.I|re.M)
            content = re.sub(r'\<(http[^\>\|]*)\>?', '<a href="\\1">\\1</a>', content, re.I|re.M)
            content = re.sub(r'\n', '<br>', content, re.I|re.M)
        except Exception as e:
            logger.error("Converting post failed.")
            logger.exception(e)
        return ConversionResult(content=content)

