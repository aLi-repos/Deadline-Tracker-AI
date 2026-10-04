import asyncio
from telegram import Bot


async def main():
    token = input("Enter your Telegram bot token: ").strip()

    bot = Bot(token=token)

    print("\nWaiting for a message from your Telegram bot...")
    print("Open Telegram and send: Hello")
    print("Keep this terminal open.\n")

    last_update_id = None

    while True:
        updates = await bot.get_updates(
            offset=last_update_id,
            timeout=10
        )

        for update in updates:
            last_update_id = update.update_id + 1

            if update.message:
                print("\n✅ Message received!")
                print("Chat ID:", update.message.chat.id)
                print("Username:", update.message.chat.username)
                print("Name:", update.message.chat.first_name)

                return


if __name__ == "__main__":
    asyncio.run(main())