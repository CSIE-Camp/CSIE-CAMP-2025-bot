import discord
from discord.ext import commands
from src.utils.achievements import achievement_manager, ACHIEVEMENTS


class AchievementCog(commands.Cog):
    """成就相關指令"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="成就", aliases=["achievements", "achievement"])
    async def show_achievements(self, ctx, user: discord.Member = None):
        """顯示成就列表"""
        target_user = user or ctx.author
        user_achievements = await achievement_manager.get_user_achievements(target_user.id)
        
        # 創建嵌入式訊息
        embed = discord.Embed(
            title=f"🏆 {target_user.display_name} 的成就",
            color=0x00ff00 if user_achievements else 0x808080
        )
        
        if user_achievements:
            # 顯示已獲得的成就
            achieved_text = ""
            total_reward = 0
            for achievement in user_achievements:
                achieved_text += f"{achievement.icon} **{achievement.name}**\n{achievement.description}\n"
                achieved_text += "\n"
            
            embed.add_field(
                name=f"已獲得成就 ({len(user_achievements)}/{len(ACHIEVEMENTS)})",
                value=achieved_text,
                inline=False
            )
            
            if total_reward > 0:
                embed.add_field(
                    name="總獎勵金額",
                    value=f"💰 {total_reward} 元",
                    inline=False
                )
        else:
            embed.add_field(
                name="尚未獲得任何成就",
                value="開始遊戲來獲得你的第一個成就吧！",
                inline=False
            )
        
        # 顯示未獲得的成就（作為提示）
        achieved_ids = [ach.id for ach in user_achievements]
        unachieved = [ach for ach in ACHIEVEMENTS.values() if ach.id not in achieved_ids]
        
        if unachieved:
            unachieved_text = ""
            for achievement in unachieved[:3]:  # 只顯示前3個未獲得的成就
                unachieved_text += f"❓ **{achievement.name}**\n{achievement.description}\n"
                unachieved_text += "\n"
            
            if len(unachieved) > 3:
                unachieved_text += f"...還有 {len(unachieved) - 3} 個成就等待解鎖"
            
            embed.add_field(
                name="未獲得的成就",
                value=unachieved_text,
                inline=False
            )
        
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
        embed.set_footer(text="繼續努力解鎖更多成就吧！")
        
        await ctx.send(embed=embed)

    @commands.command(name="成就列表", aliases=["all_achievements"])
    async def list_all_achievements(self, ctx):
        """顯示所有可獲得的成就"""
        embed = discord.Embed(
            title="🏆 所有可獲得的成就",
            description="以下是所有可以獲得的成就列表：",
            color=0xFFD700
        )
        
        for achievement in ACHIEVEMENTS.values():
            field_value = f"{achievement.description}\n"
            
            embed.add_field(
                name=f"{achievement.icon} {achievement.name}",
                value=field_value,
                inline=True
            )
        
        embed.set_footer(text=f"總共有 {len(ACHIEVEMENTS)} 個成就可以獲得")
        await ctx.send(embed=embed)

    @commands.command(name="測試成就", aliases=["test_achievement"])
    @commands.has_permissions(administrator=True)
    async def test_achievement(self, ctx, achievement_id: str = None):
        """測試成就系統（僅管理員可用）"""
        if not achievement_id:
            available_achievements = ", ".join(ACHIEVEMENTS.keys())
            await ctx.send(f"請指定成就ID。可用的成就ID: {available_achievements}")
            return
        
        if achievement_id not in ACHIEVEMENTS:
            await ctx.send(f"找不到成就ID: {achievement_id}")
            return
        
        success = await achievement_manager.check_and_award_achievement(
            ctx.author.id, achievement_id, ctx
        )
        
        if not success:
            await ctx.send("你已經擁有這個成就了！")

    @test_achievement.error
    async def test_achievement_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 此指令僅限管理員使用！")


async def setup(bot):
    await bot.add_cog(AchievementCog(bot))
