# -*- coding: utf-8 -*-
from llm_connector.storage.protocol import LlmStorage
from llm_connector.storage.mysql_primary import MysqlPrimaryStorage

__all__ = ["LlmStorage", "MysqlPrimaryStorage"]
