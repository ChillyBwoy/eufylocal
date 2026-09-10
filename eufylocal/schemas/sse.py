from typing import Literal

from pydantic import BaseModel, Field


class ServerSideMessageBase(BaseModel): ...


class ServerSideReadyMessage(ServerSideMessageBase):
    type: Literal["ready"] = Field(default="ready")


class ServerSideRefreshMessage(ServerSideMessageBase):
    type: Literal["refresh"] = Field(default="refresh")


class ServerSideStatusMessage(ServerSideMessageBase):
    type: Literal["status"] = Field(default="status")


type ServerSideMessage = ServerSideReadyMessage | ServerSideRefreshMessage | ServerSideStatusMessage
