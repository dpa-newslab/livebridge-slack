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
from copy import deepcopy
from datetime import datetime
from livebridge_slack import SlackPost


SOURCE_DOC = {'ts': '1475579307.000004', 'previous_message': {'user': 'U1F2VML58', 'text': 'Development', 'ts': '1475578806.000002', 'type': 'message'}, 'message': {'user': 'U1F2VML58', 'text': 'Developments', 'ts': '1475578806.000002', 'edited': {'user': 'U1F2VML58', 'ts': '1475579307.000000'}, 'type': 'message'}, 'subtype': 'message_changed', 'hidden': True, 'channel': 'C1JQPPBJ6', 'type': 'message', 'event_ts': '1475579307.349265', 'livebridge': {'action': 'update'}}

class SlackPostTest(asynctest.TestCase):

    def setUp(self):
        self.post = deepcopy(SOURCE_DOC)
        self.content= "foobaz"
        self.sp = SlackPost(self.post, content=self.content, images=[])

    @asynctest.fail_on(unused_loop=False)
    def test_init(self):
        assert self.sp.data == self.post
        assert hasattr(self.sp, "is_deleted") == True
        assert hasattr(self.sp, "is_update") == True
        assert self.sp.id == self.post["message"]["ts"]
        assert self.sp.source_id ==  "C1JQPPBJ6"
        assert self.sp.created == datetime(2016, 10, 4, 11, 0, 6, 2)
        assert self.sp.updated == datetime(2016, 10, 4, 11, 8, 27, 4)
        assert self.sp.images == []
        assert self.sp.content == self.content

    @asynctest.fail_on(unused_loop=False)
    def test_get_action(self):
        # ignore/submitted
        # should be update
        self.post["livebridge"]["action"] = "update"
        assert self.sp.get_action() == "update"

        # test delete
        self.post["livebridge"]["action"] = "delete"
        assert self.sp.get_action() == "delete"

        # test ignore for unknown
        self.post["livebridge"]["action"] = "create"
        assert self.sp.get_action() == "create"

    @asynctest.fail_on(unused_loop=False)
    def test_get_updated(self):
        assert self.sp.updated == datetime(2016, 10, 4, 11, 8, 27, 4)
        assert self.sp.created == datetime(2016, 10, 4, 11, 0, 6, 2)
        del self.sp.data["message"]
        assert self.sp.updated == datetime(2016, 10, 4, 11, 8, 27, 4)
        assert self.sp.created == datetime(2016, 10, 4, 11, 8, 27, 4)

    @asynctest.fail_on(unused_loop=False)
    def test_get_deleted_id(self):
        assert self.sp.id==  "1475578806.000002"
        self.sp.data["deleted_ts"] = "foo"
        assert self.sp.id == "foo"

    @asynctest.fail_on(unused_loop=False)
    def test_is_not_delete(self):
        assert self.sp.is_deleted == False

    @asynctest.fail_on(unused_loop=False)
    def test_is_sticky(self):
        assert self.sp.is_sticky == False

    @asynctest.fail_on(unused_loop=False)
    def test_is_deleted(self):
        self.sp.data["livebridge"]["action"] = "delete"
        assert self.sp.is_deleted == True

        self.sp.data["livebridge"]["action"] = "update"
        assert self.sp.is_deleted == False

    @asynctest.fail_on(unused_loop=False)
    def test_is_update(self):
        self.sp.data["livebridge"]["action"] = "update"
        assert self.sp.is_update == True

        self.sp.data["livebridge"]["action"] = "delete"
        assert self.sp.is_update == False

    @asynctest.fail_on(unused_loop=False)
    def test_target_doc(self):
        assert self.sp.target_doc == None
        self.sp._existing = {"target_doc": {"doc": "foo"}}
        assert self.sp.target_doc == self.sp._existing["target_doc"]

    @asynctest.fail_on(unused_loop=False)
    def test_target_doc_setter(self):
        assert self.sp.target_doc == None
        self.sp.target_doc = {"target_doc": {"doc": "foo"}}
        assert self.sp.target_doc ==  {"target_doc": {"doc": "foo"}}

    @asynctest.fail_on(unused_loop=False)
    def test_target_id(self):
        assert self.sp._target_id == None
        self.sp._target_id = "foobaz"
        assert self.sp.target_id == "foobaz"

    @asynctest.fail_on(unused_loop=False)
    def test_target_id_from_existing(self):
        self.sp.set_existing({"target_id": "foobaz"})
        assert self.sp.target_id == "foobaz"
