# -*- coding: utf-8 -*-
from __future__ import annotations


class LlmConnectorError(Exception):
    """Base error for the connector."""


class RouteNotFoundError(LlmConnectorError):
    pass


class RouteSuspendedError(LlmConnectorError):
    pass


class MissingApiKeyError(LlmConnectorError):
    pass


class BundleSuspendedError(LlmConnectorError):
    """One or more required model slots are suspended — batch must not run."""
