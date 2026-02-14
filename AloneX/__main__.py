# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of AloneXMusic

import asyncio
import importlib

from AloneX import anon, app, config, db, logger, stop, userbot, yt
from AloneX.plugins import all_modules


async def main():
    # DB + client boot
    await db.connect()
    await app.boot()
    await userbot.boot()
    await anon.boot()

    # Plugins
    for module in all_modules:
        importlib.import_module(f"AloneX.plugins.{module}")
    logger.info(f"Loaded {len(all_modules)} modules.")

    # Cookies URL varsa indir
    if getattr(config, "COOKIES_URL", None):
        if config.COOKIES_URL:
            await yt.save_cookies(config.COOKIES_URL)

    # Cache / sudo / blacklist
    sudoers = await db.get_sudoers()
    app.sudoers.update(sudoers)
    app.bl_users.update(await db.get_blacklisted())
    logger.info(f"Loaded {len(app.sudoers)} sudo users.")

    # ✅ Pyrogram 1.x için idle yerine sonsuz bekleme
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        # stop() async ise çağırmayacağız; zaten SIGTERM ile kapanır
        # burada sadece güvenli çıkış
        pass
