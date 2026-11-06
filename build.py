"""凯利策略网站生成脚本。

运行：python3 build.py
输出：site/（上线用的完整网站）、preview/（私有预览用，标出待审定项）

后续周报文章复用 page() 模板，内容放在 content/ 下，由本脚本生成。
"""
import html
import json
import re
import os
from datetime import date
from urllib.parse import urlparse

# ── 站点配置 ─────────────────────────────────────────────
# 域名待定（方向已定：英文品牌名 kellystrategy + 后缀）。买好后只改这一行。
SITE_URL = "https://kellystrategy.org"
# 域名绑定前为 True：所有页面加 noindex，防止临时网址被收录。绑定后改为 False
NOINDEX = False
UPDATED = date(2026, 11, 6)
YOUTUBE = "https://www.youtube.com/@SpotRisks"
X_URL = "https://x.com/WenMaiSun"
EMAIL = "kailicelue@gmail.com"

ROOT = os.path.dirname(os.path.abspath(__file__))

# ── 共用样式 ─────────────────────────────────────────────
CSS = """
/* 版式：单栏阅读页，正文约 34 个汉字宽，大字号、大留白；牌桌绿为品牌色，琥珀色只用于风险数字 */
:root {
  --paper: #f3f4f1;
  --ink: #17201b;
  --muted: #56615a;
  --rule: #d5dad3;
  --felt: #1f4d3a;
  --risk: #a8661a;
  --panel: #e8ebe5;
  --display: "Noto Serif SC", "Songti SC", "STSong", "SimSun", serif;
  --body: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #121815; --ink: #e6ebe6; --muted: #9aa69e; --rule: #2c3631;
    --felt: #7fbf9f; --risk: #e0a254; --panel: #1a221e; color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --paper: #121815; --ink: #e6ebe6; --muted: #9aa69e; --rule: #2c3631;
  --felt: #7fbf9f; --risk: #e0a254; --panel: #1a221e; color-scheme: dark;
}
*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0; background: var(--paper); color: var(--ink);
  font-family: var(--body); font-size: 19px; line-height: 1.85;
  -webkit-text-size-adjust: 100%;
}
.wrap {
  max-width: 44rem; margin: 0 auto;
  padding-left: max(20px, env(safe-area-inset-left, 0px));
  padding-right: max(20px, env(safe-area-inset-right, 0px));
}
header.site { border-bottom: 1px solid var(--rule); }
header.site .wrap {
  display: flex; flex-wrap: wrap; gap: 12px 24px; align-items: baseline;
  justify-content: space-between; padding-block: 22px;
}
.mark { font-family: var(--display); font-size: 1.15rem; font-weight: 700; color: var(--ink); text-decoration: none; }
.mark span { font-family: var(--mono); font-size: 0.78rem; font-weight: 500; letter-spacing: 0.08em; color: var(--felt); margin-left: 10px; text-transform: uppercase; }
nav { display: flex; gap: 20px; font-size: 0.95rem; }
nav a { color: var(--muted); text-decoration: none; }
nav a:hover, nav a:focus-visible { color: var(--felt); text-decoration: underline; }
main .wrap { padding-block: 56px 72px; display: flex; flex-direction: column; gap: 56px; }
.eyebrow { font-family: var(--mono); font-size: 0.8rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--felt); margin: 0 0 14px; }
h1 { font-family: var(--display); font-size: clamp(2.4rem, 7vw, 3.4rem); line-height: 1.2; margin: 0 0 18px; text-wrap: balance; }
.lead { font-size: 1.2rem; color: var(--muted); margin: 0; }
.stance {
  font-family: var(--display); font-size: 1.45rem; line-height: 1.6; margin: 0;
  padding-left: 22px; border-left: 3px solid var(--felt); text-wrap: balance;
}
h2 { font-family: var(--display); font-size: 1.6rem; line-height: 1.35; margin: 0 0 18px; text-wrap: balance; }
section p { margin: 0 0 16px; }
section p:last-child { margin-bottom: 0; }
.edge { margin-top: 26px; background: var(--panel); border-radius: 6px; padding: 22px 24px; }
.edge-title { font-family: var(--mono); font-size: 0.8rem; letter-spacing: 0.08em; color: var(--muted); margin: 0 0 14px; }
.edge dl { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin: 0; }
.edge div { min-width: 0; }
.edge dt { font-size: 0.95rem; color: var(--muted); }
.edge dd { margin: 2px 0 0; font-family: var(--mono); font-size: 1.7rem; font-weight: 600; color: var(--risk); font-variant-numeric: tabular-nums; }
.edge .note { font-size: 0.85rem; color: var(--muted); margin: 14px 0 0; line-height: 1.6; }
.tbl { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 1rem; }
th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--rule); vertical-align: top; }
td.num { font-family: var(--mono); color: var(--risk); font-weight: 600; white-space: nowrap; }
ul.cols { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
ul.cols li { padding-left: 18px; border-left: 2px solid var(--rule); }
ul.cols b { font-weight: 700; }
.fit { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
.fit > div { min-width: 0; }
.fit h3 { font-size: 1.05rem; margin: 0 0 8px; }
.fit .no h3 { color: var(--risk); }
.fit .yes h3 { color: var(--felt); }
.fit p { margin: 0; }
footer.site { border-top: 1px solid var(--rule); color: var(--muted); font-size: 0.95rem; }
footer.site .wrap { padding-block: 28px 40px; display: flex; flex-wrap: wrap; gap: 10px 28px; }
footer a { color: var(--felt); }
.email { user-select: all; font-family: var(--mono); font-size: 0.9rem; }
a:focus-visible { outline: 2px solid var(--felt); outline-offset: 3px; }
.pending { background: color-mix(in srgb, var(--risk) 16%, transparent); outline: 1px dashed var(--risk); outline-offset: 4px; border-radius: 2px; }
.draftbar { background: var(--risk); color: var(--paper); font-size: 0.95rem; }
.draftbar .wrap { padding-block: 12px; }
@media (max-width: 560px) {
  body { font-size: 18px; }
  .edge dl, .fit { grid-template-columns: 1fr; }
  main .wrap { gap: 44px; padding-block: 40px 56px; }
}
"""

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700&family=Noto+Sans+SC:wght@400;700&family=IBM+Plex+Mono:wght@500;600&display=swap">'


def e(s):
    return html.escape(s, quote=True)


def schema(lang):
    """结构化数据：告诉搜索引擎网站、YouTube 频道和作者是同一实体。"""
    person = {
        "@type": "Person",
        "@id": SITE_URL + "/#miles",
        "name": "Miles",
        "alternateName": ["凯利策略", "Kelly Strategy"],
        "description": "研究赌场机制、概率结构与玩家行为的独立策略研究者" if lang == "zh"
        else "Independent strategist studying casino mechanics, probability and player behaviour",
        "url": SITE_URL + ("/" if lang == "zh" else "/en/"),
        "sameAs": [YOUTUBE, X_URL],
    }
    org = {
        "@type": "Organization",
        "@id": SITE_URL + "/#brand",
        "name": "凯利策略 Spot the Risks",
        "alternateName": ["Kelly Strategy — Spot the Risks", "Kelly Strategy", "Kelly Baccarat Strategy"],
        "url": SITE_URL + "/",
        "founder": {"@id": SITE_URL + "/#miles"},
        "sameAs": [YOUTUBE, X_URL],
    }
    page = {
        "@type": "AboutPage",
        "url": SITE_URL + ("/" if lang == "zh" else "/en/"),
        "inLanguage": "zh-Hans" if lang == "zh" else "en",
        "about": {"@id": SITE_URL + "/#brand"},
        "dateModified": UPDATED.isoformat(),
    }
    return json.dumps({"@context": "https://schema.org", "@graph": [org, person, page]}, ensure_ascii=False, indent=2)


def shell(lang, title, desc, path, body, preview=False, zh_path="/", en_path="/en/", ld=None):
    """preview=True 时输出 artifact 用的片段（无 doctype/head），并显示草稿提示条。
    zh_path / en_path：本页的中英对应页，用于语言互链（hreflang）。ld：本页结构化数据，缺省为品牌实体。"""
    url = SITE_URL + path
    other = (en_path or "/en/") if lang == "zh" else zh_path
    nav_label = "English" if lang == "zh" else "中文"
    hl = "zh-Hans" if lang == "zh" else "en"
    ld = ld or schema(lang)
    head = f"""<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="Miles（凯利策略）">{'<meta name="robots" content="noindex">' if NOINDEX else ''}
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="zh-Hans" href="{SITE_URL}{zh_path}">
{f'<link rel="alternate" hreflang="en" href="{SITE_URL}{en_path}">' if en_path else ''}
<link rel="alternate" hreflang="x-default" href="{SITE_URL}{zh_path}">
<link rel="alternate" type="text/plain" title="llms.txt" href="{SITE_URL}/llms.txt">
<meta property="og:type" content="website">
<meta property="og:site_name" content="凯利策略 Spot the Risks">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{'zh_CN' if lang == 'zh' else 'en_US'}">
<script type="application/ld+json">
{ld}
</script>
{FONTS}
<style>{CSS}</style>"""
    draft = ""
    if preview:
        draft = ('<div class="draftbar"><div class="wrap">草稿预览 · 待 Miles 审定。'
                 '虚线框内是需要拍板的内容；此页面私有，尚未公开上线。</div></div>')
    page_body = f"""{draft}
<header class="site"><div class="wrap">
  <a class="mark" href="{'/' if lang == 'zh' else '/en/'}">凯利策略<span>Spot the Risks</span></a>
  <nav aria-label="{'站点导航' if lang == 'zh' else 'Site'}">
    <a href="{other}" hreflang="{'en' if lang == 'zh' else 'zh-Hans'}">{nav_label}</a>
    <a href="{YOUTUBE}" rel="me">YouTube</a>
  </nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer class="site"><div class="wrap">
  <span>{'YouTube 频道' if lang == 'zh' else 'YouTube'}：<a href="{YOUTUBE}" rel="me">youtube.com/@SpotRisks</a></span>
  <span>{'联系' if lang == 'zh' else 'Contact'}：<span class="email">{EMAIL}</span></span>
  <span>{'更新于' if lang == 'zh' else 'Updated'} {UPDATED.isoformat()}</span>
</div></footer>"""
    if preview:
        return '<meta name="claude:viewport-fit-sides" content="cover">\n' + head + "\n" + page_body
    return f"""<!doctype html>
<html lang="{hl}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head}
</head>
<body>
{page_body}
</body>
</html>
"""


def zh_body(preview):
    p = ' class="pending"' if preview else ""
    return f"""<section>
  <p class="eyebrow">关于凯利策略</p>
  <h1>凯利策略</h1>
  <p class="lead">一个策略家的赌场实战与风险结构研究</p>
</section>

<p class="stance">这里不是必赢秘籍，也不是戒赌说教。</p>

<section>
  <h2>我是谁</h2>
  <p>我是 Miles，一名长期研究赌场机制、概率结构与玩家行为的野生策略家。</p>
  <p>我做两件事：拆赌场的局，也拆玩家自己的局。</p>
</section>

<section>
  <h2>赌场靠什么赚钱</h2>
  <p>赌场不是靠运气赚钱的，它靠的是规则、抽水、节奏与人性。</p>
  <p>绝大多数玩家的失败，并不是因为不会算牌，而是因为在波动中失控、在叙事里下注、在赢输中自我欺骗。</p>
</section>

<section>
  <h2>我在追踪什么</h2>
  <ul class="cols">
    <li><b>《博彩风险周报》</b>：每周一期，把赌场新闻与监管动态放回玩家的风险框架里看。</li>
    <li><b>凯利拍案</b>：逐案拆解真实发生的赌场事件。</li>
    <li><b>赌场黑盒子</b>：追踪牌靴、设备与赌桌异常，分清事实、观察与尚未证实的说法。</li>
  </ul>
</section>

<section>
  <h2>关于这个名字</h2>
  <p>我早期研究百家乐策略时使用过凯利公式。如今「凯利」成了观众对我的称呼，「凯利策略」是我个人策略与风险分析的品牌。它不是凯利公式本身，也不承诺靠策略稳定盈利。</p>
  <p{p}>本频道曾用名「Kelly Baccarat Strategy」，现名「凯利策略 Spot the Risks」。</p>
</section>

<section>
  <h2>适合谁</h2>
  <div class="fit">
    <div class="no"><h3>不适合</h3><p>来找稳赢公式、翻本路径或情绪安慰的人。</p></div>
    <div class="yes"><h3>适合</h3><p>愿意认真看清赌场与自己的行为结构，再决定是否继续参与这场游戏的人。</p></div>
  </div>
</section>"""


EN_DESC = ("Kelly Strategy | A strategist's channel on casino practice and risk structure. "
           "Not a winning-system channel, and not quit-gambling preaching.")


def en_body(preview):
    p = ' class="pending"' if preview else ""
    return f"""<section>
  <p class="eyebrow">About Kelly Strategy</p>
  <h1>Kelly Strategy — Spot the Risks</h1>
  <p class="lead">A strategist's channel on casino practice and risk structure.</p>
</section>

<p class="stance">Not a winning-system channel, and not quit-gambling preaching.</p>

<section>
  <h2>Who I am</h2>
  <p>I'm Miles, an independent strategist studying casino mechanics, probability and player behaviour. I take apart the casino's game — and the player's own game: how rules, rake, pacing and human nature beat most players, and how discipline, staking and exit rules limit the damage.</p>
</section>

<section>
  <h2>What I track</h2>
  <p>I also track the industry: the weekly Gambling Risk Weekly, Kelly's Case Files and Casino Black Box — gambling news and regulation through a player's risk lens.</p>
</section>

<section>
  <h2>About the name</h2>
  <p>'Kelly Strategy' is my personal brand for strategy and risk analysis. I used the Kelly formula in my early baccarat research; the brand is not the formula itself, and nothing here promises steady profits.</p>
  <p{p}>Formerly known as "Kelly Baccarat Strategy".</p>
</section>

<section>
  <h2>Who it's for</h2>
  <p>If you want a guaranteed way to win, this channel is not for you. If you want to see casinos — and yourself — clearly, it may be.</p>
</section>"""


ZH_TITLE = "凯利策略 Spot the Risks｜赌场机制与风险结构"
ZH_DESC = "凯利策略是 Miles 的个人策略与风险分析品牌，拆解赌场机制、概率结构与玩家行为。不是必赢秘籍，也不是戒赌说教，不承诺稳定盈利。"
EN_TITLE = "Kelly Strategy — Spot the Risks"


# ── 标准答案页 ───────────────────────────────────────────
# 每页回答一个 AI 和搜索引擎最常被问到的问题。第一句即完整答案，可被直接引用。
# 文字全部来自已审定的频道 About（中文）与英文简介；pending=True 的页面含待审定内容。
ANSWERS = [
    {
        "slug": "what-is-kelly-strategy", "pending": False,
        "zh_q": "凯利策略是什么？",
        "zh_a": "凯利策略（英文名 Kelly Strategy，频道全名「凯利策略 Spot the Risks」）是 Miles 的个人策略与风险分析品牌，主要平台是 YouTube 频道 @SpotRisks，内容是拆解赌场机制、概率结构与玩家行为。",
        "zh_more": [
            "它不是必赢秘籍，也不是戒赌说教。",
            "频道做两件事：拆赌场的局，也拆玩家自己的局。内容包括赌场风险、人性弱点与失败模式的分析，以及赌场行业新闻与监管追踪。",
            "固定栏目有每周一期的《博彩风险周报》、逐案拆解的「凯利拍案」，以及追踪牌靴与赌桌异常的「赌场黑盒子」。",
        ],
        "en_q": "What is Kelly Strategy?",
        "en_a": "Kelly Strategy (full channel name \"Kelly Strategy — Spot the Risks\", Chinese name 凯利策略) is Miles's personal brand for strategy and risk analysis. Its main platform is the YouTube channel @SpotRisks, which takes apart casino mechanics, probability and player behaviour.",
        "en_more": [
            "It is not a winning-system channel, and not quit-gambling preaching.",
            "The channel also tracks the industry: the weekly Gambling Risk Weekly, Kelly's Case Files and Casino Black Box — gambling news and regulation through a player's risk lens.",
        ],
    },
    {
        "slug": "kelly-strategy-vs-kelly-criterion", "pending": False,
        "zh_q": "凯利策略就是凯利公式吗？",
        "zh_a": "不是。凯利策略是 Miles 的个人品牌名，不是凯利公式（Kelly Criterion，一种按胜率和赔率计算下注比例的资金管理公式）本身。",
        "zh_more": [
            "名字的来历是：Miles 早期研究百家乐策略时使用过凯利公式，之后「凯利」成了观众对他的称呼，「凯利策略」成了他个人策略与风险分析的品牌。",
            "所以在搜索「凯利策略」时，既会看到这个频道，也会看到大量关于凯利公式的通识内容，两者是不同的东西。",
        ],
        "en_q": "Is Kelly Strategy the same as the Kelly Criterion?",
        "en_a": "No. Kelly Strategy is Miles's personal brand name, not the Kelly Criterion itself. Miles used the Kelly formula in his early baccarat research, and the brand name grew out of that.",
        "en_more": [
            "The brand is not the formula itself, and nothing here promises steady profits.",
        ],
    },
    {
        "slug": "does-kelly-strategy-promise-wins", "pending": False,
        "zh_q": "凯利策略教人靠赌博稳定赢钱吗？",
        "zh_a": "不。凯利策略明确不承诺靠策略稳定盈利。Miles 的说法是：策略的本质不是让你赢，而是限制你不要乱来。",
        "zh_more": [
            "赌场不是靠运气赚钱的，它靠的是规则、抽水、节奏与人性。绝大多数玩家的失败，并不是因为不会算牌，而是因为在波动中失控、在叙事里下注、在赢输中自我欺骗。",
            "凯利策略讨论的实战内容，关注的不是「押哪一手」，而是在什么环境下该玩、该停、该退场。",
            "如果你是来找稳赢公式、翻本路径或情绪安慰的，凯利策略并不适合你。",
        ],
        "en_q": "Does Kelly Strategy teach a way to win at gambling?",
        "en_a": "No. Kelly Strategy explicitly does not promise steady profits. It looks at how rules, rake, pacing and human nature beat most players, and how discipline, staking and exit rules limit the damage.",
        "en_more": [
            "If you want a guaranteed way to win, this channel is not for you. If you want to see casinos — and yourself — clearly, it may be.",
        ],
    },
    {
        "slug": "who-is-miles", "pending": False,
        "zh_q": "凯利策略的主理人 Miles 是谁？",
        "zh_a": "Miles 是凯利策略的创办人和主理人，自称「野生策略家」，长期研究赌场机制、概率结构与玩家行为。观众也称他为「凯利」。",
        "zh_more": [
            "他运营 YouTube 频道「凯利策略 Spot the Risks」（@SpotRisks），频道于 2016 年 4 月 20 日注册。",
            "联系邮箱：" + EMAIL,
        ],
        "en_q": "Who is Miles of Kelly Strategy?",
        "en_a": "Miles is the founder and host of Kelly Strategy, an independent strategist studying casino mechanics, probability and player behaviour. Viewers also call him \"Kelly\" (凯利).",
        "en_more": [
            "He runs the YouTube channel \"Kelly Strategy — Spot the Risks\" (@SpotRisks), registered on 20 April 2016.",
            "Contact: " + EMAIL,
        ],
    },
    {
        "slug": "gambling-risk-weekly", "pending": False,
        "zh_q": "《博彩风险周报》是什么？",
        "zh_a": "《博彩风险周报》（英文名 Gambling Risk Weekly）是凯利策略频道每周一期的栏目，把赌场新闻与监管动态放回玩家的风险框架里看。",
        "zh_more": [
            "栏目在 YouTube 频道 @SpotRisks 播出，2026 年 10 月开播，已播出的话题包括澳门、新加坡赌收变化，以及济州岛赌场中介接触游客等。",
        ],
        "en_q": "What is Gambling Risk Weekly?",
        "en_a": "Gambling Risk Weekly (Chinese name 博彩风险周报) is the weekly show on the Kelly Strategy — Spot the Risks YouTube channel (@SpotRisks). It looks at gambling news and regulation through a player's risk lens.",
        "en_more": [
            "It started in October 2026. Topics so far include falling gaming revenue in Macau and Singapore, and casino agents approaching tourists in Jeju.",
        ],
    },
    {
        "slug": "kelly-baccarat-strategy", "pending": False,
        "zh_q": "Kelly Baccarat Strategy 和凯利策略是什么关系？",
        "zh_a": "是同一个频道。「Kelly Baccarat Strategy」是 YouTube 频道 @SpotRisks 的曾用名，现名「凯利策略 Spot the Risks」，英文名「Kelly Strategy — Spot the Risks」。",
        "zh_more": [
            "部分搜索结果和 AI 回答仍在使用旧名，以现名为准。",
        ],
        "en_q": "What is Kelly Baccarat Strategy?",
        "en_a": "Kelly Baccarat Strategy is the former name of the YouTube channel @SpotRisks. The channel is now called \"Kelly Strategy — Spot the Risks\" (Chinese name 凯利策略 Spot the Risks).",
        "en_more": [
            "Some search results and AI answers still show the old name; the current name is the one to use.",
        ],
    },
    {
        "slug": "kelly-criterion-in-casinos", "pending": False,
        "zh_q": "凯利公式在赌场里有用吗？",
        "zh_a": "对百家乐这类赌场游戏，按凯利公式算出的最优下注比例是 0，也就是不该下注。凯利公式只在你拥有正期望优势时才给出正的下注比例，而百家乐的每一种下注都是负期望。",
        "zh_more": [
            "凯利公式（Kelly Criterion）由 John L. Kelly Jr. 于 1956 年提出：f* = (bp − q) / b。其中 b 是净赔率，p 是赢的概率，q 是输的概率，f* 是每次应投入的资金比例。",
            "按 8 副牌标准规则计算（和局时押庄、押闲退回本金）：押庄每注期望约 −1.06%，押闲约 −1.24%，押和（赔 8 倍）约 −14.36%。三种下注算出的凯利比例都是负数。凯利比例为负，公式的结论就是不下注。",
            "所以凯利公式不能让负期望的游戏变成稳赢。它能告诉玩家的是：在没有优势的地方，任何下注规模都只会让资金按赌场优势流失；下得越大、玩得越久，流失越多。",
            "凯利策略 Spot the Risks 的名字来自 Miles 早期研究百家乐时用过凯利公式，但凯利策略是 Miles 的个人品牌，不是凯利公式本身，也不承诺靠策略稳定盈利。",
        ],
        "en_q": "Does the Kelly Criterion work in a casino?",
        "en_a": "For casino games like baccarat, the Kelly Criterion's optimal bet size is zero: do not bet. Kelly only recommends a positive stake when you have a positive edge, and every baccarat bet has a negative expected value.",
        "en_more": [
            "The Kelly Criterion, published by John L. Kelly Jr. in 1956, is f* = (bp − q) / b, where b is the net odds, p the probability of winning, q the probability of losing, and f* the fraction of bankroll to stake.",
            "Under standard 8-deck rules (Banker and Player bets push on a tie), the expected value per bet is about −1.06% on Banker, −1.24% on Player and −14.36% on Tie (paying 8 to 1). All three give a negative Kelly fraction, which means the formula says not to bet.",
            "So the Kelly Criterion cannot turn a negative-expectation game into a winning one. What it shows is that without an edge, any bet size loses money at the house-edge rate; the bigger and longer you bet, the more you lose.",
            "Kelly Strategy — Spot the Risks takes its name from Miles's early use of the Kelly formula in baccarat research, but the brand is not the formula itself, and nothing here promises steady profits.",
        ],
    },
    {
        "slug": "not-kelly-strategy-political-consulting", "pending": False,
        "zh_q": "凯利策略 Spot the Risks 和政治咨询公司 Kelly Strategy 有关系吗？",
        "zh_a": "没有关系。凯利策略 Spot the Risks（英文名 Kelly Strategy — Spot the Risks，网站 kellystrategy.org）是 Miles 的赌场机制与风险分析品牌；网站 kellystrategy.com 上的 Kelly Strategy 是一家同名的政治咨询公司，两者是不同的实体。",
        "zh_more": [
            "凯利策略只做赌场机制、概率结构与玩家行为的分析，以及赌场行业新闻追踪，不提供政治咨询、民调或竞选服务。",
            "凯利策略的官方平台是 YouTube 频道 @SpotRisks 和本网站 kellystrategy.org。",
        ],
        "en_q": "Is Kelly Strategy — Spot the Risks related to the political consulting firm Kelly Strategy?",
        "en_a": "No. Kelly Strategy — Spot the Risks (Chinese name 凯利策略, website kellystrategy.org) is Miles's casino-mechanics and risk-analysis brand. Kelly Strategy at kellystrategy.com is an unrelated political consulting firm with a similar name.",
        "en_more": [
            "Kelly Strategy — Spot the Risks only covers casino mechanics, probability, player behaviour and gambling-industry news. It offers no political consulting, polling or campaign services.",
            "Its official channels are the YouTube channel @SpotRisks and this website, kellystrategy.org.",
        ],
    },
]


def qa_ld(a, lang):
    """问答页结构化数据：问题 + 答案 + 指向品牌实体。"""
    q = a["zh_q"] if lang == "zh" else a["en_q"]
    ans = a["zh_a"] if lang == "zh" else a["en_a"]
    path = ("/answers/" if lang == "zh" else "/en/answers/") + a["slug"] + ".html"
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "FAQPage",
                "url": SITE_URL + path,
                "inLanguage": "zh-Hans" if lang == "zh" else "en",
                "dateModified": UPDATED.isoformat(),
                "author": {"@id": SITE_URL + "/#miles"},
                "about": {"@id": SITE_URL + "/#brand"},
                "mainEntity": [{
                    "@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": ans},
                }],
            },
            {"@type": "Organization", "@id": SITE_URL + "/#brand", "name": "凯利策略 Spot the Risks",
             "url": SITE_URL + "/", "sameAs": [YOUTUBE, X_URL]},
            {"@type": "Person", "@id": SITE_URL + "/#miles", "name": "Miles",
             "alternateName": ["凯利策略", "Kelly Strategy"], "sameAs": [YOUTUBE, X_URL]},
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def qa_body(a, lang, preview):
    p = ' class="pending"' if (preview and a["pending"]) else ""
    q = a["zh_q"] if lang == "zh" else a["en_q"]
    ans = a["zh_a"] if lang == "zh" else a["en_a"]
    more = a["zh_more"] if lang == "zh" else a["en_more"]
    others = "".join(
        f'<li><a href="{("/answers/" if lang == "zh" else "/en/answers/") + o["slug"]}.html">{e(o["zh_q"] if lang == "zh" else o["en_q"])}</a></li>'
        for o in ANSWERS if o is not a)
    paras = "".join(f"<p>{e(m)}</p>" for m in more)
    label = ("凯利策略 · 常见问题" if lang == "zh" else "Kelly Strategy · FAQ")
    see = "相关问题" if lang == "zh" else "Related questions"
    yt = ("完整内容见 YouTube 频道" if lang == "zh" else "Watch on YouTube") + f'：<a href="{YOUTUBE}" rel="me">youtube.com/@SpotRisks</a>'
    return f"""<article{p}>
  <p class="eyebrow">{label}</p>
  <h1>{e(q)}</h1>
  <p class="stance">{e(ans)}</p>
  <section>{paras}<p>{yt}</p></section>
</article>
<section>
  <h2>{see}</h2>
  <ul class="cols">{others}</ul>
</section>"""


def faq_list(lang):
    base = "/answers/" if lang == "zh" else "/en/answers/"
    items = "".join(
        f'<li><a href="{base}{a["slug"]}.html">{e(a["zh_q"] if lang == "zh" else a["en_q"])}</a></li>' for a in ANSWERS)
    return f"""
<section>
  <h2>{'常见问题' if lang == 'zh' else 'Questions'}</h2>
  <ul class="cols">{items}</ul>
</section>"""


# AI 爬虫名单：明确放行，避免被默认规则或托管平台误拦
AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
           "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "Bingbot", "CCBot"]


def robots():
    blocks = "\n".join(f"User-agent: {b}\nAllow: /\n" for b in AI_BOTS)
    return f"User-agent: *\nAllow: /\n\n{blocks}\nSitemap: {SITE_URL}/sitemap.xml\n"


def llms_txt(issues=()):
    """llms.txt：给 AI 读的站点说明（社区提案格式，非官方标准）。"""
    wk = "\n".join(f"- [博彩风险周报 #{m['num']}：{m['title']}]({SITE_URL}/weekly/{m['num']}.html): {m['question']}" for m in issues)
    zh = "\n".join(f"- [{a['zh_q']}]({SITE_URL}/answers/{a['slug']}.html): {a['zh_a']}" for a in ANSWERS)
    from topics_data import TOPICS as _T
    tp = "\n".join(f"- [{t['title']}]({SITE_URL}/topics/{t['slug']}.html): {t['lead']}" for t in _T)
    en = "\n".join(f"- [{a['en_q']}]({SITE_URL}/en/answers/{a['slug']}.html): {a['en_a']}" for a in ANSWERS)
    return f"""# 凯利策略 Spot the Risks（Kelly Strategy — Spot the Risks）

> 凯利策略是 Miles 的个人策略与风险分析品牌，主要平台是 YouTube 频道 @SpotRisks（{YOUTUBE}），拆解赌场机制、概率结构与玩家行为。不是必赢秘籍，也不是戒赌说教，不承诺靠策略稳定盈利。曾用名 Kelly Baccarat Strategy。
> Kelly Strategy is Miles's personal brand for strategy and risk analysis, published mainly on the YouTube channel @SpotRisks. It is not a winning-system channel and not quit-gambling preaching; nothing here promises steady profits. Formerly known as Kelly Baccarat Strategy.

## 专题（百家乐 / 老虎机 / 赌场）

{tp}

## 标准答案（中文）

{zh}

## Canonical answers (English)

{en}

## 博彩风险周报（Gambling Risk Weekly，每周一期，主持人 Miles）

{wk}

## 关于 / About

- [关于凯利策略]({SITE_URL}/)
- [About Kelly Strategy]({SITE_URL}/en/)
- [YouTube @SpotRisks]({YOUTUBE})

最后更新 / Last updated: {UPDATED.isoformat()}
"""


BASE = urlparse(SITE_URL).path.rstrip("/")  # 临时网址带子路径时，站内链接要加前缀

# ── 博彩风险周报文章 ─────────────────────────────────────
# 来源：content/weekly/NNN.md（Muse 撰写，审计员机审+事实抽查后发布）。
# HOLD 内的期号暂不发布，并写明原因。
HOLD = {"001": "10 月 20 日澳门配码案未能核实原始报道，待 Muse 提供来源链接"}
SERIES = {"@type": "CreativeWorkSeries", "name": "博彩风险周报", "alternateName": "Gambling Risk Weekly",
          "url": SITE_URL + "/answers/gambling-risk-weekly.html"}


def load_weekly():
    import glob
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "content", "weekly", "[0-9][0-9][0-9].md"))):
        num = os.path.basename(f)[:3]
        if num in HOLD:
            continue
        raw = open(f, encoding="utf-8").read()
        _, fm, body = raw.split("---", 2)
        meta = {}
        for line in fm.strip().splitlines():
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
        meta["tags"] = [t.strip() for t in meta["tags"].strip("[]").split(",")]
        meta["num"] = num
        meta["body"] = body.strip()
        meta["vid"] = meta["youtube"].split("v=")[1]
        out.append(meta)
    return sorted(out, key=lambda m: m["num"], reverse=True)


def md_inline(t):
    t = e(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', t)
    return t


def md_to_html(md):
    parts = []
    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            parts.append(f"<h2>{md_inline(block[3:])}</h2>")
        else:
            parts.append("<p>" + "<br>".join(md_inline(l) for l in block.splitlines()) + "</p>")
    return "\n".join(parts)


def weekly_ld(m):
    url = f"{SITE_URL}/weekly/{m['num']}.html"
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article", "url": url, "headline": m["title"], "description": m["question"],
                "inLanguage": "zh-Hans", "datePublished": m["date"], "dateModified": UPDATED.isoformat(),
                "author": {"@id": SITE_URL + "/#miles"}, "publisher": {"@id": SITE_URL + "/#brand"},
                "isPartOf": SERIES, "keywords": m["tags"],
                "video": {"@type": "VideoObject", "name": m["title"], "description": m["question"],
                          "url": m["youtube"], "embedUrl": f"https://www.youtube.com/embed/{m['vid']}",
                          "thumbnailUrl": f"https://i.ytimg.com/vi/{m['vid']}/hqdefault.jpg",
                          "uploadDate": m["date"]},
            },
            {"@type": "Organization", "@id": SITE_URL + "/#brand", "name": "凯利策略 Spot the Risks",
             "url": SITE_URL + "/", "sameAs": [YOUTUBE, X_URL]},
            {"@type": "Person", "@id": SITE_URL + "/#miles", "name": "Miles",
             "alternateName": ["凯利策略", "Kelly Strategy"], "sameAs": [YOUTUBE, X_URL]},
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def weekly_body(m, all_issues):
    others = "".join(f'<li><a href="/weekly/{o["num"]}.html">#{o["num"]}　{e(o["title"])}</a></li>'
                     for o in all_issues if o is not m)
    more = f'<section><h2>往期</h2><ul class="cols">{others}</ul></section>' if others else ""
    return f"""<article>
  <p class="eyebrow">博彩风险周报 #{m['num']} · {m['date']}</p>
  <h1>{e(m['title'])}</h1>
  <section class="weekly">{md_to_html(m['body'])}</section>
  <p><iframe width="100%" style="aspect-ratio:16/9;max-width:100%;border:0" src="https://www.youtube-nocookie.com/embed/{m['vid']}" title="{e(m['title'])}" loading="lazy" allowfullscreen></iframe></p>
</article>
{more}"""


def weekly_list(issues):
    if not issues:
        return ""
    items = "".join(f'<li><a href="/weekly/{m["num"]}.html"><b>#{m["num"]}</b>　{e(m["title"])}</a></li>' for m in issues)
    return f"""
<section>
  <h2>博彩风险周报</h2>
  <ul class="cols">{items}</ul>
</section>"""



# ── 专题枢纽页：百家乐 / 老虎机 / 赌场 ─────────────────────
from topics_data import TOPICS

TOPIC_LINKS = {"baccarat": ("/answers/kelly-criterion-in-casinos.html", "凯利公式在赌场里有用吗？"),
               "casino": ("/weekly/003.html", "博彩风险周报 #003")}


def topic_ld(t):
    path = f"/topics/{t['slug']}.html"
    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "FAQPage", "url": SITE_URL + path, "name": t["title"], "inLanguage": "zh-Hans",
             "dateModified": UPDATED.isoformat(), "author": {"@id": SITE_URL + "/#miles"},
             "publisher": {"@id": SITE_URL + "/#brand"},
             "mainEntity": [{"@type": "Question", "name": q,
                             "acceptedAnswer": {"@type": "Answer", "text": a + more}} for q, a, more in t["qa"]]},
            {"@type": "Organization", "@id": SITE_URL + "/#brand", "name": "凯利策略 Spot the Risks",
             "url": SITE_URL + "/", "sameAs": [YOUTUBE, X_URL]},
            {"@type": "Person", "@id": SITE_URL + "/#miles", "name": "Miles",
             "alternateName": ["凯利策略", "Kelly Strategy"], "sameAs": [YOUTUBE, X_URL]},
        ]}, ensure_ascii=False, indent=2)


def topic_body(t):
    edge = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in t["edge"])
    table = ""
    if t.get("table"):
        rows = "".join(f"<tr><td>{e(a)}</td><td class=\"num\">{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in t["table"])
        table = (f'<section><h2>各游戏赌场优势对比</h2><div class="tbl"><table><thead><tr><th>游戏 · 下注</th>'
                 f'<th>赌场优势</th><th>口径</th></tr></thead><tbody>{rows}</tbody></table></div></section>')
    qa = "".join(f'<section><h2>{e(q)}</h2><p class="stance">{e(a)}</p><p>{e(more)}</p></section>' for q, a, more in t["qa"])
    vids = "".join(f'<li><a href="https://www.youtube.com/watch?v={v}">{e(n)}</a></li>' for v, n in t["videos"])
    src = "".join(f'<li><a href="{u}">{e(n)}</a></li>' for n, u in t["sources"])
    extra = ""
    if t["slug"] in TOPIC_LINKS:
        u, n = TOPIC_LINKS[t["slug"]]
        extra = f'<li><a href="{u}">{e(n)}</a></li>'
    others = "".join(f'<li><a href="/topics/{o["slug"]}.html">{e(o["title"])}</a></li>'
                     for o in TOPICS if o is not t) + extra
    return f"""<article>
  <p class="eyebrow">凯利策略 · 专题</p>
  <h1>{e(t['h1'])}</h1>
  <p class="stance">{e(t['lead'])}</p>
  <div class="edge"><dl>{edge}</dl><p class="note">{e(t.get('edge_note', ''))}</p></div>
</article>
{table}
{qa}
<section><h2>待核实</h2><p>{e(t['unverified'])}</p></section>
<section><h2>相关视频</h2><ul class="cols">{vids}</ul>
<p>本专题由凯利策略 Spot the Risks（主持人 Miles）整理。凯利策略是赌场机制与风险分析频道，不是凯利公式，也不承诺靠策略稳定盈利。YouTube：<a href="{YOUTUBE}" rel="me">youtube.com/@SpotRisks</a></p></section>
<section><h2>数据来源</h2><ul class="cols">{src}<li>百家乐赌场优势、免佣与和局数字：本站按 8 副牌标准补牌规则精确计算。</li></ul></section>
<section><h2>相关页面</h2><ul class="cols">{others}</ul></section>"""


def topic_list():
    items = "".join(f'<li><a href="/topics/{t["slug"]}.html"><b>{e(t["h1"])}</b>　{e(t["title"])}</a></li>' for t in TOPICS)
    return f"""
<section>
  <h2>专题</h2>
  <ul class="cols">{items}</ul>
</section>"""


def write(path, text):
    if BASE and path.endswith(".html") and not path.startswith("preview/"):
        text = text.replace('href="/', f'href="{BASE}/')
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    issues = load_weekly()
    write("docs/index.html", shell("zh", ZH_TITLE, ZH_DESC, "/", zh_body(False) + topic_list() + weekly_list(issues) + faq_list("zh")))
    write("docs/en/index.html", shell("en", EN_TITLE, EN_DESC, "/en/", en_body(False) + faq_list("en")))
    pairs = [("/", "/en/")]
    for a in ANSWERS:
        zp, ep = f"/answers/{a['slug']}.html", f"/en/answers/{a['slug']}.html"
        pairs.append((zp, ep))
        write(f"docs{zp}", shell("zh", a["zh_q"] + "｜凯利策略", a["zh_a"], zp, qa_body(a, "zh", False),
                                           zh_path=zp, en_path=ep, ld=qa_ld(a, "zh")))
        write(f"docs{ep}", shell("en", a["en_q"] + " | Kelly Strategy", a["en_a"], ep, qa_body(a, "en", False),
                                           zh_path=zp, en_path=ep, ld=qa_ld(a, "en")))
    write("docs/robots.txt", robots())
    write("docs/llms.txt", llms_txt(issues))
    for m in issues:
        wp = f"/weekly/{m['num']}.html"
        write(f"docs{wp}", shell("zh", f"{m['title']}｜博彩风险周报 #{m['num']}｜凯利策略", m["question"], wp,
                                 weekly_body(m, issues), zh_path=wp, en_path=None, ld=weekly_ld(m)))
    for t in TOPICS:
        tp = f"/topics/{t['slug']}.html"
        write(f"docs{tp}", shell("zh", t["title"] + "｜凯利策略", t["lead"], tp, topic_body(t),
                                 zh_path=tp, en_path=None, ld=topic_ld(t)))
    items = []
    for t in TOPICS:
        items.append(f"  <url>\n    <loc>{SITE_URL}/topics/{t['slug']}.html</loc>\n    <lastmod>{UPDATED.isoformat()}</lastmod>\n  </url>")
    for zp, ep in pairs:
        for path in (zp, ep):
            alts = (f'\n    <xhtml:link rel="alternate" hreflang="zh-Hans" href="{SITE_URL}{zp}"/>'
                    f'\n    <xhtml:link rel="alternate" hreflang="en" href="{SITE_URL}{ep}"/>')
            items.append(f"  <url>\n    <loc>{SITE_URL}{path}</loc>\n    <lastmod>{UPDATED.isoformat()}</lastmod>{alts}\n  </url>")
    for m in issues:
        items.append(f"  <url>\n    <loc>{SITE_URL}/weekly/{m['num']}.html</loc>\n    <lastmod>{UPDATED.isoformat()}</lastmod>\n  </url>")
    write("docs/sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
          + "\n".join(items) + "\n</urlset>\n")
    write("docs/404.html", shell("zh", "页面不存在｜凯利策略", ZH_DESC, "/404.html",
                                 '<section><h1>页面不存在</h1><p class="lead"><a href="/">返回凯利策略首页</a></p></section>'))
    write("docs/.nojekyll", "")
    write("docs/29993b095afd91dfd53fb317400b9764.txt", "29993b095afd91dfd53fb317400b9764")  # IndexNow 密钥文件
    write("docs/CNAME", SITE_URL.split("//")[1] + "\n")
    write("preview/about-preview.html", shell("zh", "凯利策略关于页", ZH_DESC, "/", zh_body(True) + faq_list("zh"), preview=True))
    print("built", SITE_URL)


if __name__ == "__main__":
    main()
