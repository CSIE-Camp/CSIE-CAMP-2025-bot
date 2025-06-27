# 共用工具
from src import config


async def check_channel(interaction):
    if interaction.channel.id not in config.ALLOWED_GAME_CHANNEL_IDS:
        if config.ALLOWED_GAME_CHANNEL_IDS:
            cid = config.ALLOWED_GAME_CHANNEL_IDS[0]
            channel_mention = f"<#{cid}>"
        else:
            channel_mention = "指定頻道"
        await interaction.response.send_message(
            f"請在 {channel_mention} 頻道使用本指令！", ephemeral=True
        )
        return False
    return True
