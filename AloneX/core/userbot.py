# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of AloneXMusic

from pyrogram import Client
from AloneX import config, logger


class Userbot(Client):
    def __init__(self):
        """
        Initializes the userbot with multiple clients.
        """
        self.clients = []
        clients = {"one": "SESSION1", "two": "SESSION2", "three": "SESSION3"}

        for key, string_key in clients.items():
            name = f"AloneXUB{key[-1]}"
            session = getattr(config, string_key)

            # Session yoksa client oluşturma
            if not session:
                setattr(self, key, None)
                continue

            setattr(
                self,
                key,
                Client(
                    name=name,
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=session,
                ),
            )

    async def boot_client(self, num: int, ub: Client):
        """
        Boot a client and perform initial setup.
        """
        clients = {1: self.one, 2: self.two, 3: self.three}
        client = clients.get(num)

        if not client:
            return

        await client.start()

        # ✅ Logger mesajı zorunlu değil
        if getattr(config, "LOGGER_ID", 0):
            try:
                await client.send_message(config.LOGGER_ID, f"Assistant {num} Started")
            except Exception as ex:
                logger.warning(
                    f"Assistant {num} log grubuna mesaj atamadı, devam ediyorum. Reason: {ex}"
                )

        # ✅ Burada ub.me değil client.me kullanılmalı
        client.id = client.me.id
        client.name = client.me.first_name
        client.username = client.me.username
        client.mention = client.me.mention

        self.clients.append(client)

        # Kanal join opsiyonel
        try:
            await client.join_chat("AloneUpdates")
        except Exception:
            pass

        logger.info(f"Assistant {num} started as @{client.username}")

    async def boot(self):
        """
        Asynchronously starts the assistants.
        """
        if self.one:
            await self.boot_client(1, self.one)
        if self.two:
            await self.boot_client(2, self.two)
        if self.three:
            await self.boot_client(3, self.three)

    async def exit(self):
        """
        Asynchronously stops the assistants.
        """
        if self.one:
            await self.one.stop()
        if self.two:
            await self.two.stop()
        if self.three:
            await self.three.stop()
        logger.info("Assistants stopped.")
