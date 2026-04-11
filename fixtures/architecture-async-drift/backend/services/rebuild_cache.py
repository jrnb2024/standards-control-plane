import asyncio


async def rebuild_cache() -> None:
    asyncio.create_task(_refresh_cache())


async def _refresh_cache() -> None:
    return None
