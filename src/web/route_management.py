import asyncio
import typing as t

import aiohttp
import requests


class Route:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

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

    def _fetch(self, method: str, path: str, data: dict = None, **kwargs) -> t.Tuple[dict, bool]:
        if not data:
            data = {}

        url = self.form_url(self.base_url + path, data)

        with requests.request(method, url, **kwargs) as response:
            json = response.json()
            return json

    async def _async_fetch(self, method: str, path: str, data: dict = None, **kwargs) -> t.Tuple[dict, bool]:
        if not data:
            data = {}

        url = self.form_url(self.base_url + path, data)

        async with self.__lock:
            async with self.__session.request(method, url, **kwargs) as response:
                json = await response.json()
                return json
