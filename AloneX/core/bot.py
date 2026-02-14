# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of AloneXMusic

import pyrogram
from AloneX import config, logger


class Bot(pyrogram.Client):
    def __init__(self):
        super().__init__(
            name="AloneX",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=pyrogram.enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
        )

        self.owner: int = int(config.OWNER_ID or 0)
        self.logger_id: int = int(config.LOGGER_ID or 0)

        # ✅ Bunlar SET olmalı (update() çalışsın diye)
        self.bl_users: set[int] = set()
        self.sudoers: set[int] = set([self.owner]) if self.owner else set()

    async def boot(self):
        """Starts the bot and performs initial setup."""
        await super().start()

        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        # ✅ Logger zorunlu değil: yoksa/çalışmıyorsa bot yine de açılır
        if not self.logger_id:
            logger.warning("LOGGER_ID boş/0. Logger kontrolü atlandı, bot çalışıyor.")
            logger.info(f"Bot started as @{self.username}")
            return

        try:
            # Bazı durumlarda peer cache için önce resolve denemek iyi olur
            await self.get_chat(self.logger_id)

            await self.send_message(
                self.logger_id,
                "Bot Started",
                disable_web_page_preview=True,
            )

            # Admin kontrolü: başarısız olursa botu kapatma, sadece uyar
            try:
                member = await self.get_chat_member(self.logger_id, self.id)
                if member.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR:
                    logger.warning("Bot logger grubunda admin değil. Bot çalışmaya devam edecek.")
            except Exception as ex:
                logger.warning(f"Logger admin kontrolü yapılamadı. Reason: {ex}")

        except Exception as ex:
            # ❗ En kritik düzeltme: artık SystemExit yok
            logger.warning(
                f"Logger grubuna erişilemedi (LOGGER_ID={self.logger_id}). "
                f"Bot çalışmaya devam edecek. Reason: {ex}"
            )

        logger.info(f"Bot started as @{self.username}")

    async def exit(self):
        await super().stop()
        logger.info("Bot stopped.")
