import aiohttp


async def send_dm(discord_bot_token: str, discord_user_id: int, content: str) -> None:
    headers = {"Authorization": f"Bot {discord_bot_token}", "Content-Type": "application/json"}
    base_url = "https://discord.com/api/v10"

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(
            f"{base_url}/users/@me/channels", json={"recipient_id": str(discord_user_id)}
        ) as resp:
            resp.raise_for_status()
            channel_data = await resp.json()
            channel_id = channel_data["id"]

        async with session.post(
            f"{base_url}/channels/{channel_id}/messages", json={"content": content}
        ) as resp:
            resp.raise_for_status()
