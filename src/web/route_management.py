import asyncio
import typing as t
from urllib.parse import quote as _uriquote

import aiohttp
import requests


class Route:
    def __init__(self, method: str, base_url: str, path: str, **parameters) -> None:
        self.path = path
        self.method = method

        url = base_url + self.path

        if parameters:
            self.url = url.format(**{k: _uriquote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        else:
            self.url = url

        self.__session = aiohttp.ClientSession()
        self.__lock = asyncio.Lock()

    @staticmethod
    def form_url(url: str, data: dict = None) -> str:
        if not data:
            data = {}

        url += "?" + "&".join([
            f"{dict_key}={dict_value}" for dict_key, dict_value in data.items()
        ])

        return url

    async def close(self) -> None:
        await self.__session.close()

    def _fetch(self, data: dict = None) -> t.Tuple[dict, bool]:
        if not data:
            data = {}

        url = self.form_url(self.url, data)

        with requests.get(url) as response:
            json = response.json()
            return json

    async def _async_fetch(self, data: dict = None) -> t.Tuple[dict, bool]:
        if not data:
            data = {}

        url = self.form_url(self.url, data)

        async with self.__lock:
            async with self.__session.get(url) as response:
                json = await response.json()
                return json
