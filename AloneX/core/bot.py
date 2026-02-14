# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of AloneXMusic

from pyrogram import Client
from AloneX import config, logger


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="AloneX",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode="html",  # ✅ Pyrogram 1.x uyumlu
        )

        self.owner = int(getattr(config, "OWNER_ID", 0) or 0)
        self.logger_id = int(getattr(config, "LOGGER_ID", 0) or 0)

        # ✅ SET olmalı (update çalışsın)
        self.bl_users = set()
        self.sudoers = set([self.owner]) if self.owner else set()

    async def boot(self):
        await super().start()

        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        if not self.logger_id:
            logger.warning("LOGGER_ID boş/0. Logger kontrolü atlandı, bot çalışıyor.")
            logger.info(f"Bot started as @{self.username}")
            return

        try:
            # peer resolve
            await self.get_chat(self.logger_id)

            await self.send_message(
                self.logger_id,
                "Bot Started",
                disable_web_page_preview=True,
            )

            # ✅ Pyrogram 1.x: member.status string döner
            try:
                member = await self.get_chat_member(self.logger_id, self.id)
                if member.status != "administrator":
                    logger.warning("Bot logger grubunda admin değil. Bot çalışmaya devam edecek.")
            except Exception as ex:
                logger.warning(f"Logger admin kontrolü yapılamadı. Reason: {ex}")

        except Exception as ex:
            logger.warning(
                f"Logger grubuna erişilemedi (LOGGER_ID={self.logger_id}). "
                f"Bot çalışmaya devam edecek. Reason: {ex}"
            )

        logger.info(f"Bot started as @{self.username}")

    async def exit(self):
        await super().stop()
        logger.info("Bot stopped.")
