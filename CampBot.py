import discord
from discord.ext import commands
import random
import datetime
import asyncio
import os
import sys

intents = discord.Intents.all()

bot = commands.Bot(intents=intents, command_prefix="?")

msg_ch = None

@bot.event
async def on_ready():
    print(f'已登入為 {bot.user}')

    while True:
        inp = await asyncio.to_thread(input, "> ")
        if inp == "exit":
            await bot.close()
            for task in asyncio.all_tasks():
                task.cancel()
            break
        if msg_ch == None:
            continue
        ch = bot.get_channel(msg_ch)
        assert ch != None
        await ch.send(f"From Terminal: {inp}")
    sys.exit()

@bot.command()
async def links(ctx):
    table = {
            "範例程式碼與指令": "https://github.com/CSIE-Camp/example-code-2025",
            "官方網站": "https://camp.ntnucsie.info/",
    }
    title = "各種連結"
    embed = discord.Embed(title=f"{title}", color=0x0000ff)
    for (key, value) in table.items():
        embed.add_field(name=key, value=value, inline=False)
        pass
    embed.set_footer(text=f"NTNU CSIE Camp 2025")
    await ctx.send(embed=embed)


@bot.command()
async def set_ch(ctx, chid):
    global msg_ch
    try: 
        msg_ch = int(chid)
    except ValueError: 
        await ctx.send("無效ID"); return 
    
    try: 
        _a = bot.get_channel(chid)
    except: 
        await ctx.send("沒有這一個頻道")
        return




@bot.event
async def on_message(message):
    if message.author.bot:  # 忽略bot自己傳的訊息
        return
    
    if message.content == "?抽籤":
        acg_quotes = [
            "o月是xx的oo",
            "oo吧！xx",
            "oo與xx之間的慘烈修羅場",
            "ooo也要xxx",
            "oo的奇妙xx",
            "oooo，怎麼想都是你們的錯",
            "從oo看還是從xx看",
            "從零開始的oooo",
            "進擊的oo",
            "魔法少女oo",
            "某oo的xxxx",
            "我的oo不可能這麼可愛",
            "我們仍未知道oooo",
            "只有oo知道的世界",
            "oo什麼的最討厭了",
            "oo，我的oo",
            "oo又死了真沒人性",
            "啊哈哈，佐祐理不知道",
            "抱歉，我在想hellshake矢野",
            "笨蛋是不會感冒的",
            "不被發現就不算犯罪哦",
            "不得了",
            "不是假髮，是桂！",
            "不是蘿莉控，是女權主義者",
            "不要不要的",
            "不要吃我",
            "不要瞎掰好嗎",
            "不要在意細節",
            "大蔥插菊花治療感冒",
            "剛剛o了一下",
            "觀賞用·保存用·布教用",
            "畫個圈圈詛咒你",
            "機智得一逼",
            "嫁不出去了",
            "今天的風兒好喧囂啊",
            "今天很快樂對不對？我們明天一定會更快樂的，oooo!",
            "警察叔叔，就是這個人",
            "巨乳只有下垂的未來",
            "絕望了，我對這個oo的世界絕望了",
            "看，人就像垃圾一樣！",
            "可愛即正義",
            "可喜可賀，可喜可賀",
            "快看他畫風和我們不一樣",
            "快向全國的oo道歉",
            "喵帕斯",
            "木有魚丸/魚丸粗面",
            "男人變態有什麼錯",
            "你的愛還不夠啊",
            "你傻逼！再見！",
            "釀了你哦",
            "你是想要聽真話還是假話",
            "女人有四張嘴",
            "くぁwせdrftgyふじこlp",
            "去死兩次",
            "其實我對oo還是蠻有自信的",
            "人傻不能怨社會",
            "人生無常，大腸包小腸",
            "如果oo就是神作了",
            "生氣了嗎",
            "是oo的friends呢",
            "是將軍啊啊啊！",
            "酸甜苦辣咸，ooooo",
            "甜食是裝在另一個胃裡的",
            "未被穿過的胖次是沒有價值的",
            "我得了一種不oo就會xx的病",
            "我一定會回來的",
            "我對普通的oo沒有興趣",
            "我考慮了一下還是無法接受啊",
            "我是輸給了地球的重力",
            "現實就是個垃圾遊戲",
            "一旦接受了這種設定",
            "已經吃不下了",
            "有一個好消息和一個壞消息",
            "這麼可愛一定是男孩子",
            "這在我們業界是一種獎勵",
            "這種東西小範圍享受就可以了",
            "畢竟老夫也不是什麼惡魔",
            "感覺像是喝了很烈的酒一樣",
            "就這樣插進去就行了",
            "Niconiconi",
            "誰都無法預測的命運之舞台",
            "太oo了吧",
            "為了保護我們心愛的ooo……成為偶像！",
            "為什麼要演奏春日影",
            "哇嘎立馬斯/長頸鹿",
            "一輩子oo",
            "我什麼都願意做",
            "我什麼都沒有",
            "小祥●▛▙小祥●▛▙小祥●▛▙小祥●▛▙小祥●▛▙小祥●▛▙小祥●▛▙",
            "又要重複嗎，絕望的輪迴",
            "oo比我更重要嗎？/夾腳",
            "啊咧咧",
            "我的車裡有空調",
            "我叫oo，是個偵探",
            "我是高中生偵探工藤新一",
            "超高校級的oo",
            "o井戶",
            "賭上爺爺的名義",
            "淨TM扯淡",
            "計畫通",
            "謎已經全部解開了",
            "其他人做得到嗎",
            "我要成為新世界的卡密",
            "異議あり！",
            "兇手就在我們中間",
            "這是我爸爸在夏威夷教我的",
            "這個遊戲，我有必勝法！/必勝法",
            "真相永遠只有一個",
            "真相併非永遠只有一個",
            "oo真是天使",
            "愛醬大oo",
            "不是只有小學生才有處男嗎",
            "鼻子發酸，感覺好痛苦",
            "超好玩的！你有什麼不滿嗎",
            "此乃謊言！",
            "但是，是男的",
            "島村之刃",
            "都是oo的錯",
            "EMT",
            "風太大我聽不見",
            "哥哥借我詞典",
            "哥哥讓開這樣我殺不了那傢伙",
            "還有馬桶蓋子",
            "就算不結婚有妹妹不就好了嗎",
            "就算是oo，只要有愛就沒問題",
            "就這麼愉快地決定了",
            "就因為你戴了黃色眼鏡看到的才是黃色的",
            "Just Monika",
            "可是那一天，我有了新的想法",
            "貓也可以",
            "沒有人受傷的世界完成了",
            "那萬一有了就墮掉好了",
            "你們的關係可真好啊",
            "你們都是我的翅膀",
            "你還記得自己是男的",
            "你最好乖乖聽話",
            "貧乳是稀有價值",
            "任性可是女孩子的天性呢",
            "日本隊又贏了",
            "為什麼你會這麼熟練啊",
            "我曾經把你當做過自慰對象",
            "我和你將在那個新世界裡成為新的夏娃和夏娃",
            "我很好奇",
            "我認為H是不對的",
            "我喜歡尼婭，還有大家",
            "我現在內心感到悲痛欲絕",
            "我已經看到結局了",
            "我在未來等你",
            "小兔子暗黑無限破",
            "心葉，你一定不懂吧",
            "胸部什麼的，明明只是裝飾",
            "選擇吧",
            "一股戀愛喜劇的酸臭味",
            "有趣的女人",
            "有什麼要來了",
            "由於oo問題，約定畢業後恢復xx關係",
            "遠的不是距離，而是次元啊",
            "在妹妹的房間用妹妹的電腦玩對妹妹耍流氓的遊戲",
            "真是可愛呢",
            "我將來，想當攝影師",
            "真有你們的啊SE",
            "這是最優先事項喔！",
            "這手今晚不洗了",
            "之後幹了個爽",
            "自己嚇自己",
            "oo還能再戰xx年",
            "oo，你算計我！oo！",
            "oo是會互相吸引的",
            "oo是能成為我母親的女性",
            "不就是一塊石頭麼，看我用高達把它推回去",
            "不能逃避、不能逃避、不能逃避",
            "不要停下來啊！",
            "不作死就不會死，為什麼不明白！",
            "被重力束縛住靈魂的人類",
            "創造新時代的不會是老人",
            "動啊，鐵奧",
            "高達屹立於大地之上",
            "感受到了世界的惡意",
            "後備隱藏能源",
            "腳只是裝飾而已，上面的大人物是不會懂的",
            "看我正義的一擊！",
            "離地球毀滅還有ooo天",
            "連我爸爸都沒有打過我",
            "聯邦的MS都是怪物嗎",
            "陌生的天花板",
            "馬上啟動新的武藏指揮官",
            "你渴望力量嗎",
            "你們都是我的翅膀",
            "你說這個誰懂啊！",
            "你敢違抗擁有巴耶力的我嗎",
            "你有近距離見過oo嗎，它拯救的生命多到超乎你的想像",
            "難道藏了我所不知道的笑點？",
            "前方高能反應",
            "讓我見識一下吧，聯邦軍MS的性能",
            "人類總是重複同樣的錯誤",
            "弱者為何要戰鬥",
            "人類是無法相互理解的",
            "三天三夜",
            "Sieg Zeon",
            "所羅門喲，我又回來了",
            "突破天際",
            "我犯下了無法挽回的錯誤",
            "我就是高達",
            "我來組成頭部",
            "我是為了與你相遇才出生的",
            "已經不用再戰鬥了",
            "因為年輕而犯下的錯",
            "因為還是個小鬼啊（坊やだからさ）",
            "這時只要微笑就可以了",
            "這就是青春嗎",
            "這不是女人的名字嗎",
            "這是何等的失態",
            "只不過是主監視器壞了",
            "只要打不中就沒有什麼大不了",
            "鑽頭是男人的浪漫",
            "左舷彈幕太薄了",
            "oo是什麼，能吃嗎",
            "oo，快用你那無敵的xx想想辦法吧",
            "oo，你這傢伙在看我吧",
            "oo，我的超人",
            "oo你個大笨蛋",
            "o——o——",
            "必可活用於下一次",
            "不要靠近我啊",
            "不，學長，是我們oo",
            "不會浪費你太多時間的",
            "不要小看我的情報網",
            "大腦在顫抖",
            "但oo實在是太xx了",
            "但是我拒絕",
            "但我的痛苦在你之上",
            "對不起oo，沒能讓你使出全力",
            "對他使用炎拳吧",
            "德國的科學技術是世界第一",
            "大哥哥，一起玩吧",
            "惡·即·斬",
            "復！活！",
            "復活吧，我的愛人！",
            "伏爾加博士，請原諒我！",
            "GET DA☆ZE！",
            "咕殺",
            "哈哈你去死吧",
            "好強大的靈壓！",
            "好肉麻的兩公婆，好在他們不是我父母，否便樣衰了",
            "好討厭的感覺啊",
            "好耶",
            "海的那邊……是敵人……",
            "回老家結婚",
            "會贏的",
            "活下去",
            "和我的oo是同樣類型的xx呢",
            "接下來才是真正的地獄",
            "姐姐姐姐，oooo。雷姆雷姆，oooo",
            "就是本人……就是本人！",
            "就算是神也殺給你看",
            "看啊，你的死兆星在天上閃耀",
            "連自己心愛的人都救不了，我還算什麼oo",
            "萊納，你坐啊！",
            "連一刻都沒有為oo的死亡哀悼，立刻趕到戰場的是",
            "冒險家翻抽屜有什麼不對",
            "沒有人能在我的BGM里打敗我",
            "我說，那邊的人全都是處男嗎？",
            "那個oo，被這種東西打敗了嗎！！！",
            "那一天，人類終於想起了oo的恐怖",
            "那種事不要啊",
            "你不是還有生命嗎",
            "你從什麼時候開始產生了oooo的錯覺",
            "你的下一句話是",
            "你會記得你吃過多少片麵包嗎",
            "你相信引力嗎",
            "你已經死了",
            "你以為oo，我就會xx嗎？",
            "你真是怠惰呢",
            "你也想起舞嗎",
            "你在...說什麼？",
            "歐拉",
            "胖次看光光",
            "前略，天國的oo君",
            "前面可是地獄啊",
            "全都打一頓！",
            "燃燒吧，小宇宙",
            "人類才勇敢",
            "人類的讚歌是勇氣的讚歌",
            "人類為什麼要互相傷害",
            "傷疤是男子漢的勳章",
            "時間要開始加速了",
            "屍體在說話",
            "是我迪奧噠",
            "雖然我可愛又迷人，但我會招來死亡",
            "所以我說那個醬汁呢？",
            "太棒了，我逐漸理解一切",
            "為王的誕生，獻上禮砲！",
            "我ooo願稱你為最強",
            "我不做人了",
            "我的生涯一片無悔",
            "我的王之力啊！",
            "我就將我剛剛體驗到的事直接說出來吧！",
            "我連宇宙盡頭在哪裡都不知道，怎麼會知道這個",
            "我們的戰鬥才剛剛開始",
            "我是魔法使",
            "我是沒興趣，而你是沒才能",
            "我禿了，也變強了",
            "我想起來了",
            "我愚蠢的oo啊",
            "我是，超級貝吉塔！",
            "我要做oo的狗",
            "放棄思考",
            "吾等前方，絕無敵手！",
            "吾心吾行澄如明鏡，所作所為皆為正義",
            "無限劍制",
            "下一個就是你了，承太郎",
            "現在你感覺如何？感覺如何了！？",
            "獻出心臟",
            "相同的招式對聖鬥士是沒用的",
            "想死一次嗎",
            "要上嗎？我打oo！？",
            "要用魔法打敗魔法",
            "藝術就是爆炸",
            "因為我們是ooo",
            "勇士喜歡巨乳有什麼錯",
            "永遠無法到達oo的真實",
            "又斬了無聊的東西",
            "在我眼裡都是渣",
            "戰鬥力只有5的渣渣",
            "戰你娘親",
            "這個男人，有兩把刷子",
            "這麼小的東西也算卍解？",
            "這雖然是遊戲，但可不是鬧著玩的",
            "這是便宜糖",
            "這是我最後的波紋",
            "這是一場試煉",
            "這味道……是說謊的味道",
            "這也在你的計算之中嗎",
            "真是膚淺",
            "真是HIGH到不行",
            "正面上我啊",
            "只要能到達那個地方",
            "諸君，我喜歡oo",
            "不要扶他",
            "城之內之死",
            "臣服在漢諾崇高的力量面前吧",
            "出現吧！我的他媽西（靈魂）！",
            "打麻將真開心啊",
            "對閃光防禦",
            "墮落！萌死他卡多！（抽卡！怪獸卡！）",
            "好強！太強了！",
            "好戲從現在才要開始！",
            "很了不起的大象先生吧",
            "教練，我想打籃球",
            "快住手！這根本不是決鬥！",
            "沒有等級不就是等級零嗎",
            "那裡已經不是你的領域了",
            "那我呢",
            "你的生命猶如風中殞地",
            "哦多！oo選手衝上了賽道",
            "青眼白龍攻擊布倫希爾德",
            "鏘鏘鏘！衝擊性的事實！",
            "區區oo送給你了",
            "神之一手",
            "所累哇多卡納（這可說不定吶）",
            "完美的手牌",
            "為什麼oo在這裡？靠自己的力量逃出來了嗎",
            "我不喜歡oo",
            "我已經燃燒殆盡了，只剩下雪白的灰",
            "無限立直",
            "下一回合你就完了",
            "小學生真是太棒了",
            "一飛沖天啊，我！",
            "意義不明的卡",
            "因為我是天才",
            "用oo帶來笑容",
            "這是為了生存下來的我的掙扎！",
            "這個遊戲，我有必勝法！/必勝法",
            "最強的ooo一切都是必然的",
            "這仇，我記下了",
            "不oo的話不就只能去死了嗎",
            "不也挺好嗎",
            "不要以為這樣就算贏了",
            "代表月亮消滅你/我要替月行道，警惡懲奸",
            "都是夏美子的錯",
            "和我簽訂契約，成為魔法少女吧",
            "精密檢查",
            "頭腦稍微冷靜一下吧",
            "我……還要當魔法少女到什麼時候？",
            "我，真是個笨蛋",
            "已經沒什麼好怕的了",
            "Ciallo",
            "操到叫苦連天",
            "啊嘞你剛剛咋舌了",
            "人被殺就會死",
            "你是我的Master嗎",
            "圍繞著你的世界，比你想像的要溫柔一些",
            "我不是蘿莉控，只是喜歡的人剛好是蘿莉而已！",
            "現在是你比較強",
            "亞瑟王不懂人心",
            "要上了ooo——xx的儲備足夠嗎",
            "只要殺了oo我隨便你搞",
            "oo是x文明",
            "oo是這樣的。xx只要yy就可以，可是oo要考慮的事情就很多了",
            "oo無權為我授勳",
            "應該由oo侍奉xx",
            "oo永不為奴",
            "All your base are belong to us",
            "部落都是廢物",
            "滴滴，你個王八蛋！",
            "El Psy Kongroo",
            "En Taro oo",
            "軌言軌語",
            "漢斯，你的咖啡真難喝",
            "哈哈，覺得眼熟？",
            "好討厭，眼淚一直停不下來",
            "哼哼哼！呵呵呵呵！哈哈哈哈哈！",
            "和平源自力量",
            "歡迎回來，指揮官",
            "可以讓我玩一會嗎？",
            "開幕雷擊",
            "來盤昆特牌吧",
            "竜神の剣を喰らえ",
            "門(窗戶)像是和空間固定在了一起，紋絲不動",
            "男人就該干男人",
            "你的英勇長存人心",
            "你們這是自尋死路",
            "你怎麼還在",
            "納米機器，小子！",
            "全場最佳",
            "人不能，至少不應該",
            "RUA",
            "如此強大的力量",
            "如今又再度變得溫順了",
            "如果你是龍，也好",
            "少女祈禱中",
            "神說你還不能死在這裡",
            "聖光啊，你有看到那個oo嗎",
            "是oo，我們有救了",
            "收了可觀的小費後，酒館老闆小聲道",
            "說得好，但這毫無意義",
            "萬物皆虛，萬事皆允",
            "我得重新集結部隊",
            "我選擇死亡",
            "完蛋，我被oo包圍了",
            "效果拔群",
            "膝蓋中了一箭",
            "癢，好吃",
            "一大波殭屍正在接近",
            "因為神聖的F2A連結著我們每一個人",
            "猶豫，就會敗北",
            "戰爭，戰爭從未改變",
            "這是何等的靈壓啊",
            "這是oo的，讓我們感覺到xx",
            "偵測到在途的聚變打擊",
            "抓住一隻野生的oo",
            "總有一天我的生命將抵達終點，而你，將加冕為王",
            "再來一回合！",
            "oo很簡單，我已經嘗試了不下千回",
            "愛情是盲目的",
            "今晚的月色真美",
            "恐怖如斯",
            "來者啊，快把一切希望揚棄",
            "女孩子是由砂糖、香辛料和某些美好東西組成的",
            "前天看到了小兔，昨天是小鹿，今天是你",
            "我的神，我的神，為什麼離棄我",
            "我要這天，再遮不住我眼……",
            "我真是個罪孽深重的女人",
            "小火把在閒逛",
            "噫！好！我中了！",
            "站住，你是如此美麗",
            "最上川",
            "oo的笑容由我來守護",
            "oo還在追我",
            "oo，請把力量借給我",
            "oo，你出息了啊",
            "寶↗生↘永↗夢↘",
            "對哦，我就是傳說中的魔法少女Beast",
            "根本贏不了，我聽不懂",
            "假面騎士的末日到了",
            "今晚去吃烤肉",
            "奶奶曾經說過",
            "你都守護了什麼",
            "其實宗方根本不會喝酒",
            "認真你就輸了",
            "撒，來細數你的罪惡吧",
            "為什麼在一旁看著！難道你真的背叛了嗎",
            "我的身體已經殞地",
            "我沒有夢想，但我可以守護夢想",
            "我只是個科學家，我沒有他們那樣的力量",
            "我只是路過的oo",
            "我自始至終都是最佳狀態",
            "無敵的oo倒下了",
            "我將效忠於您",
            "現在，我的手中抓住了未來",
            "相信是不需要理由的",
            "相信我，你也可以變成光",
            "鄉隊員不是在與傑克的搏鬥中死了嗎",
            "消滅奧特曼的計畫是佐菲定的",
            "謝謝你，泰羅",
            "一天是oo，你這輩子都是oo",
            "英雄可不能臨陣脫逃啊",
            "這份笑容，就是健康的證明哦",
            "這副嫉妒我的表情",
            "大家並沒有那麼脆弱",
            "沒有那種世俗的欲望",
            "你們兩個，乾脆交往算啦",
            "太妙了",
            "我的字典裡沒有oo",
            "呀啦那一卡（不來一發麼）",
            "眼睛，我的眼睛",
            "在虛構的故事當中尋求真實感的人腦袋一定有問題",
            "請問，這是鴿子嗎？",
            "這是禁止事項"
        ]
        quote = random.choice(acg_quotes)
        quote = quote.replace("ooo", "寫程式").replace("oo", "程式").replace("o", "卷")
        result = random.randint(1, 100)
        content = ""
        if result <= 1:
            content = "不可思議的傳說大吉！"
        if result <= 3:
            content = "超級無敵大吉！"
        if result <= 5:
            content = "無敵大吉！"
        if result <= 10:
            content = "大吉！"
        elif result <= 30:
            content = "中吉！"
        elif result <= 50:
            content = "普通吉！"
        elif result <= 70:
            content = "小吉！"
        else:
            content = "迷你吉！"
        embed = discord.Embed(title=f"{content}", color=0x00ff00)
        embed.set_footer(text=f"今日適合你的一句話：{quote}")
        await message.channel.send(embed=embed)

    if message.content == "?拉霸":
        """
        拉霸遊戲
        """
        symbols = [
            "<:discord:1385577039838449704>", 
            "<:python:1385577058184466502>", 
            "<:block:1385577076865630300>", 
            "<:mushroom:1385577154775089182>",
            "<:dino:1385577110965321840>", 
            "<:money:1385577138727686286>", 
            "<:block:1385577076865630300>"
        ]
        result = [random.choice(symbols) for _ in range(5)]
        result_str = "".join(result)
        await message.channel.send(f"{result_str}")
        max_count = max(result.count(symbol) for symbol in symbols)
        if max_count == 5:
            await message.channel.send(f"五個！！！天才！？")
        elif max_count == 4:
            await message.channel.send(f"四個！！很優秀！")
        elif max_count == 3:
            await message.channel.send(f"三個！不錯")
        else:
            await message.channel.send(f"菜就多練")

        return
    
    if message.content.startswith("?查詢課表"):
        custom_time = message.content.split(" ") # mmddhhmm (測試用)

        datetime_now = datetime.datetime.now()


        if (len(custom_time) > 1 and datetime_now < datetime.datetime(2025, 7, 1, 0, 0)):
            try:
                datetime_now = datetime.datetime.strptime(custom_time[1], "%m%d%H%M")
                datetime_now = datetime_now.replace(year=2025)  # 假設課程在 2025 年
            except ValueError:
                await message.channel.send("請輸入正確的時間格式：mmddhhmm")
                return

        lesson_time = [
            datetime.datetime(2025, 7, 1, 9, 30), # 2025-07-01 09:30 報到
            datetime.datetime(2025, 7, 1, 10, 30), # 2025-07-01 10:30 開幕
            datetime.datetime(2025, 7, 1, 12, 0), # 2025-07-01 12:00 LUNCH TIME
            datetime.datetime(2025, 7, 1, 13, 30), # 2025-07-01 13:30 課程一
            datetime.datetime(2025, 7, 1, 17, 40), # 2025-07-01 17:40 DINNER TIME
            datetime.datetime(2025, 7, 1, 19, 0), # 2025-07-01 19:00 晚上活動
            datetime.datetime(2025, 7, 1, 21, 0), # 2025-07-01 21:00 CODING/SLEEPING TIME

            datetime.datetime(2025, 7, 2, 9, 40), # 2025-07-02 09:40 課程二
            datetime.datetime(2025, 7, 2, 12, 0), # 2025-07-02 12:00 LUNCH TIME
            datetime.datetime(2025, 7, 2, 13, 30), # 2025-07-02 13:30 選修課一
            datetime.datetime(2025, 7, 2, 15, 10), # 2025-07-02 15:10 課程三
            datetime.datetime(2025, 7, 2, 17, 50), # 2025-07-02 17:50 DINNER TIME
            datetime.datetime(2025, 7, 2, 19, 0), # 2025-07-02 19:00 晚上活動
            datetime.datetime(2025, 7, 2, 21, 0), # 2025-07-02 21:00 CODING/SLEEPING TIME

            datetime.datetime(2025, 7, 3, 9, 40), # 2025-07-03 09:40 課程四
            datetime.datetime(2025, 7, 3, 12, 0), # 2025-07-03 12:00 LUNCH TIME
            datetime.datetime(2025, 7, 3, 13, 30), # 2025-07-03 13:30 選修課二
            datetime.datetime(2025, 7, 3, 15, 10), # 2025-07-03 15:10 黑客松
            datetime.datetime(2025, 7, 3, 17, 30), # 2025-07-03 17:30 DINNER TIME
            datetime.datetime(2025, 7, 3, 19, 0), # 2025-07-03 19:00 晚上活動
            datetime.datetime(2025, 7, 3, 21, 0), # 2025-07-03 21:00 CODING/SLEEPING TIME

            datetime.datetime(2025, 7, 4, 9, 40), # 2025-07-04 09:40 黑客松 & 吃午餐
            datetime.datetime(2025, 7, 4, 13, 20), # 2025-07-04 13:20 黑客松報告
            datetime.datetime(2025, 7, 4, 15, 20), # 2025-07-04 15:20 閉幕
            datetime.datetime(2025, 7, 4, 17, 0) # 2025-07-04 17:00 結束
        ]

        lesson_name = [
            "報到", "開幕", "午餐時間", "課程一", "晚餐時間", "晚上活動", "Coding/Sleeping Time",
            "課程二", "午餐時間", "選修課一", "課程三", "晚餐時間", "晚上活動", "Coding/Sleeping Time",
            "課程四", "午餐時間", "選修課二", "黑客松", "晚餐時間", "晚上活動", "Coding/Sleeping Time",
            "黑客松 & 吃午餐", "黑客松報告", "閉幕", "結束"
        ]

        current_lesson = None
        for lesson_idx in range(len(lesson_time)):
            if datetime_now > lesson_time[-(lesson_idx + 1)]:
                current_lesson = -(lesson_idx + 1)
                break
        if current_lesson == None:
            await message.channel.send("目前還沒有開始喔～")
            return

        await message.channel.send(f"目前時間：{datetime_now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                                   f"目前課程：{lesson_name[current_lesson]}\n"
                                   f"剩餘時間：{int(((lesson_time[current_lesson + 1] - datetime_now).seconds) / 60)} 分鐘\n"
                                   f"下個課程：{lesson_name[current_lesson + 1] if current_lesson + 1 < len(lesson_name) else '無'}\n")
        
        addtional_messages = []
        if datetime_now.hour < 3 or datetime_now.hour >= 24:
            addtional_messages = ["現在是凌晨耶:O，快去睡覺", "~~這麼爆肝，很有成為工程師的淺力喔~~", "你...怎麼那麼晚還在想我(/////)"]

        if lesson_name[current_lesson] == "報到":
            addtional_messages = ["歡迎來到資工營！", "居然有人已經發現這個功能了"]

        if lesson_name[current_lesson] == "開幕":
            addtional_messages = ["愉快的資工營終於開始了~", "我以為這裡是主控台ㄟ，"]

        if lesson_name[current_lesson] == "午餐時間":
            addtional_messages = ["好耶，是吃飯時間，快樂:D"]

        if lesson_name[current_lesson] == "晚餐時間":
            addtional_messages = ["晚餐吃得飽，隔天精神好0v0"]

        if lesson_name[current_lesson] == "晚上活動":
            addtional_messages = ["現在正在活動，別跟我聊天了啦> <"]

        remain_time = int(((lesson_time[current_lesson + 1] - datetime_now).seconds) / 60)
        if lesson_name[current_lesson] == "黑客松 & 吃午餐":
            if remain_time < 60:
                addtional_messages = ["最後衝刺！加油加油！"]
            elif remain_time < 30:
                addtional_messages = [""]
            elif remain_time < 10:
                addtional_messages = ["等等...為什麼你還有閒情逸致跟我聊天=v="]

        addtional_message = random.choice(addtional_messages)
        await message.channel.send(addtional_message)
        
        return
    await bot.process_commands(message)
    
@bot.command()
async def startDrama(ctx):
    if ctx.author.id != 825730483601276929:  # 替換為你的 Discord ID
        print(f"{ctx.author.display_name} 沒有權限使用這個指令")
        return

    drama_channel_name = "demo區"
    drama_channel = discord.utils.get(ctx.guild.text_channels, name=f"{drama_channel_name}")

    starfish_webhook = await drama_channel.create_webhook(name="Starfish")
    starfish_avatar = ctx.guild.get_member(825730483601276929).avatar.url
    starfish_name = ctx.guild.get_member(825730483601276929).name

    names = ["第一小隊", "第二小隊", "第三小隊", "第四小隊", "第五小隊", "第六小隊"]
    random.shuffle(names)

    embed = discord.Embed(title="抽籤結果", description="以下是報告的順序", color=0xff0000)
    for i, name in enumerate(names):
        embed.add_field(name=f"第 {i + 1} 組報告", value=name, inline=False)
    
    await starfish_webhook.send("呼，我到了", username=starfish_name, avatar_url=starfish_avatar)
    await asyncio.sleep(3)
    await starfish_webhook.send("等我一下喔，現在要抽籤對吧", username=starfish_name, avatar_url=starfish_avatar)
    await asyncio.sleep(3)
    await starfish_webhook.send("ㄟ！惠惠，幫我抽個籤", username=starfish_name, avatar_url=starfish_avatar)
    await asyncio.sleep(2)
    await drama_channel.send("你很煩耶，好啦，我在營隊裡也是幫你很多忙ㄟ")
    await asyncio.sleep(3)
    await drama_channel.send("說好的酬勞可別忘了喔...( $ _ $ )")
    await asyncio.sleep(2)
    await starfish_webhook.send("噓...不是，不是說好不能談...$ 了嗎", username=starfish_name, avatar_url=starfish_avatar)
    await asyncio.sleep(2)
    await drama_channel.send("可是你已經說要...")
    await asyncio.sleep(1)
    msg = await starfish_webhook.send("好啦好啦，會給會給啦，快做事啦", username=starfish_name, avatar_url=starfish_avatar, wait=True)
    await asyncio.sleep(1)
    await msg.add_reaction("😀")
    async with drama_channel.typing():
        await asyncio.sleep(5)
    await drama_channel.send(embed=embed)
    await asyncio.sleep(2)
    await drama_channel.send("抽好了~")
    await asyncio.sleep(3)
    await drama_channel.send("說好的...別忘了喔( •̀ ω •́ )✧")
    await asyncio.sleep(1)
    await starfish_webhook.send("好好好，沒你的戲份了，掰掰", username=starfish_name, avatar_url=starfish_avatar)
    await asyncio.sleep(3)
    await starfish_webhook.send("如各位所見，以上，就是報告順序！", username=starfish_name, avatar_url=starfish_avatar)
    await asyncio.sleep(2)
    await starfish_webhook.send("抽完籤我就回來啦，等我一下！", username=starfish_name, avatar_url=starfish_avatar)

    starfish_webhook.delete()

def main():
    try:
        bot.run(os.getenv("DISCORD_TOKEN"))  # 啟動機器人，使用環境變數中的 Discord Token
    except SystemExit:
        print("Exited")
        return
    
if __name__ == "__main__":
    main()

