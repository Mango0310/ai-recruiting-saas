"""Generate 10 PDF resumes with Chinese font via PyMuPDF + SimHei embedding.

Simplified: uses insert_text with embedded font. No textbox measurement issues.
"""

import fitz, os
from pathlib import Path

OUTPUT_DIR = Path(r"D:\honor share\ai-recruiting-saas\demo-data\resumes-text\pdfs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_FILE = "C:/Windows/Fonts/simhei.ttf"
assert os.path.exists(FONT_FILE), f"Font not found: {FONT_FILE}"

# Font name used throughout
FN = "C"

PAGE_W, PAGE_H = 595, 842
M = 45
BLUE = (0.102, 0.227, 0.420)
BLUE_LT = (0.91, 0.94, 0.98)
BLUE_MID = (0.18, 0.37, 0.62)
DARK = (0.2, 0.2, 0.2)
GRAY = (0.42, 0.42, 0.42)
GRAY_LT = (0.62, 0.62, 0.62)
WHITE = (1, 1, 1)
BG = (0.94, 0.95, 0.97)


def new_page(doc):
    p = doc.new_page(width=PAGE_W, height=PAGE_H)
    p.insert_font(fontname="C", fontfile=FONT_FILE)
    return p


def txt(p, x, y, text, size=9, color=DARK):
    """Simple insert_text. Silently skip empty text."""
    if not text or not text.strip():
        return y
    p.insert_text((x, y), text, fontname="C", fontsize=size, color=color)
    return y


def header(p, name, sub, email, phone):
    p.draw_rect(fitz.Rect(0, 0, PAGE_W, 78), color=None, fill=BLUE)
    txt(p, M, 38, name, size=21, color=WHITE)
    txt(p, M, 60, sub, size=9, color=(0.75, 0.82, 0.92))
    txt(p, M, 73, f"{email}  |  {phone}", size=8, color=(0.65, 0.72, 0.85))


def stitle(p, y, title):
    p.draw_rect(fitz.Rect(M, y + 2, 3, 12), color=None, fill=BLUE)
    txt(p, M + 10, y + 11, title, size=11, color=BLUE)
    return y + 26


def tags(p, y, tag_list):
    x = M
    for tag in tag_list:
        # Estimate width: ~5pt per CJK char, ~4pt per ASCII char at 7.5pt font
        w_est = sum(5 if ord(c) > 127 else 4 for c in tag)
        bw = w_est + 10
        if x + bw > PAGE_W - M:
            x = M
            y += 18
        p.draw_rect(fitz.Rect(x, y, x + bw, y + 16), color=None, fill=BLUE_LT)
        p.draw_rect(fitz.Rect(x, y, x + bw, y + 16), color=(0.80, 0.85, 0.93))
        txt(p, x + 5, y + 12, tag, size=7.5, color=BLUE)
        x += bw + 5
    return y + 24


def bline(p, y, text, indent=0, size=9):
    return txt(p, M + indent, y, text, size=size, color=DARK) + 3


def brow(p, y, left, right):
    txt(p, M, y, left, size=10, color=DARK)
    txt(p, PAGE_W - M - 80, y, right, size=8, color=GRAY)
    return y + 18


def bul(p, y, text):
    txt(p, M + 5, y, "·", size=8, color=BLUE_MID)
    return txt(p, M + 16, y, text, size=8.5, color=(0.35, 0.35, 0.35)) + 3


resumes = [
    {
        "name": "陈明",
        "sub": "高级后端工程师 · 6年经验 · Go / 微服务 / 跨境支付",
        "email": "chenming@email.com", "phone": "13800001111",
        "tags": ["Go", "Python", "gRPC", "Kubernetes", "PostgreSQL", "Redis", "Kafka", "分布式事务", "CI/CD", "微服务"],
        "secs": [
            ("求职意向", [("", "高级后端工程师 / 架构师，期望薪资 40K-55K")]),
            ("工作经历", [
                ("星辰科技有限公司 | 高级后端工程师", "2023.03 - 至今", [
                    "负责跨境支付系统从0到1架构设计，日均交易额5000万+",
                    "Go + gRPC + Kubernetes微服务改造，单机QPS从2000提升到5万",
                    "设计Saga分布式事务方案，解决多币种结算数据一致性问题",
                    "主导CI/CD流水线建设，部署频率从每周1次提升到每天20次",
                ]),
                ("云帆网络 | 后端工程师", "2020.07 - 2023.02", [
                    "参与电商中台订单系统开发，日均300万订单，P99延迟从800ms降到120ms",
                    "引入Redis + Kafka实现异步化，扛住双十一10倍流量峰值",
                ]),
            ]),
            ("教育背景", [
                ("", "浙江大学 | 硕士 | 软件工程 | 2017-2020"),
                ("", "武汉理工大学 | 本科 | 计算机科学与技术 | 2013-2017"),
            ]),
            ("自我评价", [("", "擅长高并发分布式系统设计，有跨境支付和电商中台实战经验。GitHub开源项目贡献者。")]),
        ],
    },
    {
        "name": "林小婉",
        "sub": "跨境电商运营经理 · 5年经验 · 东南亚市场 / 用户增长",
        "email": "linxiaowan@email.com", "phone": "13800002222",
        "tags": ["海外运营", "用户增长", "TikTok营销", "A/B测试", "Google Ads", "Shopee", "Lazada", "英语流利"],
        "secs": [
            ("求职意向", [("", "跨境电商运营经理 / 海外业务负责人，期望薪资 30K-40K")]),
            ("工作经历", [
                ("出海汇科技有限公司 | 东南亚运营负责人", "2023.06 - 至今", [
                    "SaaS产品印尼/越南/泰国三地本地化运营，年GMV从2000万增长到1.2亿",
                    "搭建12人本地化团队（内容/活动/用户增长方向），覆盖三个市场",
                    "定价策略A/B测试，付费转化率从3.2%提升到5.8%",
                    "与TikTok、Shopee合作联合营销活动，单次新增注册用户15万+",
                ]),
                ("蓝鲸跨境 | 运营经理", "2020.03 - 2023.05", [
                    "负责欧美市场用户增长和留存，管理Google Ads + Facebook投放（月均50万）",
                    "搭建邮件营销自动化体系，用户7日留存率提升40%",
                ]),
            ]),
            ("教育背景", [
                ("", "广东外语外贸大学 | 硕士 | 国际商务 | 2016-2018"),
                ("", "暨南大学 | 本科 | 电子商务 | 2012-2016"),
            ]),
            ("语言能力", [("", "英语：流利（商务谈判级别）  |  印尼语：基础（日常沟通）")]),
        ],
    },
    {
        "name": "周雨晴",
        "sub": "资深UI/UX设计师 · 4年经验 · B端SaaS / 设计系统",
        "email": "zhouyuqing@email.com", "phone": "13800003333",
        "tags": ["Figma", "Sketch", "Design System", "原型设计", "用户研究", "Design Thinking", "B端设计"],
        "secs": [
            ("求职意向", [
                ("", "资深UI/UX设计师，期望薪资 28K-38K"),
                ("", "作品集：dribbble.com/yuqing-design  |  behance.net/yuqing-ux"),
            ]),
            ("工作经历", [
                ("UXDesign Studio | 独立设计师", "2023.01 - 至今", [
                    "为3家B2B SaaS公司提供产品设计服务，涵盖ERP、CRM、跨境物流管理系统",
                    "从0到1搭建设计系统，包含200+组件，覆盖Web端和移动端",
                    "主导某跨境ERP产品的UX改版，用户任务完成率从62%提升到89%",
                ]),
                ("星辰科技 | UI设计师", "2021.03 - 2022.12", [
                    "负责企业级SaaS后台界面设计，服务500+企业客户",
                    "设计还原度从60%提升到95%，建立完整设计规范文档",
                ]),
            ]),
            ("教育背景", [("", "中国美术学院 | 本科 | 视觉传达设计 | 2016-2020")]),
            ("自我评价", [("", "专注B端SaaS产品设计，注重设计系统搭建和用户体验量化。")]),
        ],
    },
    {
        "name": "王浩然",
        "sub": "海外市场推广经理 · 5年经验 · Google / Facebook / TikTok投放",
        "email": "wanghaoran@email.com", "phone": "13800004444",
        "tags": ["Google Ads", "Facebook Ads", "TikTok Ads", "SEO", "SEM", "GA4", "归因模型", "KOL营销", "A/B测试"],
        "secs": [
            ("求职意向", [("", "海外市场推广经理 / 增长负责人，期望薪资 35K-45K")]),
            ("工作经历", [
                ("速卖科技 | 海外增长负责人", "2022.04 - 至今", [
                    "负责跨境电商SaaS产品全球用户增长，年度预算800万",
                    "Google Ads + Facebook + LinkedIn多渠道投放，ROAS从1.8提升到3.5",
                    "SEO优化自然流量提升3倍，核心关键词Google排名前3",
                    "搭建归因模型（MMM+增量测试），精准衡量各渠道贡献",
                ]),
                ("出海通 | 海外推广经理", "2019.08 - 2022.03", [
                    "管理Google/Facebook/TikTok三渠道投放，月均预算50万",
                    "欧美和东南亚市场差异化推广策略，根据市场定制素材和落地页",
                ]),
            ]),
            ("教育背景", [
                ("", "上海外国语大学 | 硕士 | 国际新闻传播 | 2017-2019"),
                ("", "华东师范大学 | 本科 | 广告学 | 2013-2017"),
            ]),
            ("语言能力", [("", "英语：专业八级  |  西班牙语：基础")]),
        ],
    },
    {
        "name": "张磊",
        "sub": "供应链管理经理 · 7年经验 · 跨境物流 / 海外仓 / FBA",
        "email": "zhanglei@email.com", "phone": "13800005555",
        "tags": ["供应链管理", "WMS", "库存预测", "跨境物流", "FBA", "海外仓运营", "供应商管理", "成本优化"],
        "secs": [
            ("求职意向", [("", "供应链管理经理 / 物流总监，期望薪资 35K-50K")]),
            ("工作经历", [
                ("闪电供应链科技 | 供应链总监", "2023.03 - 至今", [
                    "负责跨境电商全链路供应链管理：采购+仓储+物流+关务四大环节",
                    "搭建供应商竞价+评分机制，采购成本降低12%",
                    "WMS系统上线，仓库拣货效率提升60%，库存准确率达到99.7%",
                    "优化跨境物流线路，欧洲专线时效从15天缩短到8天，成本降低18%",
                ]),
                ("跨境通物流 | 供应链经理", "2020.01 - 2023.02", [
                    "管理3个海外仓（洛杉矶/法兰克福/雅加达），总面积2万平米",
                    "建立库存预测模型，缺货率从8%降到2.5%，周转天数从45天优化到28天",
                ]),
            ]),
            ("教育背景", [
                ("", "上海交通大学 | 硕士 | 物流工程与管理 | 2015-2017"),
                ("", "南京大学 | 本科 | 工业工程 | 2011-2015"),
            ]),
            ("自我评价", [("", "深耕跨境供应链7年，擅长数据驱动的效率优化和成本控制。有DHL、菜鸟等物流合作资源。")]),
        ],
    },
    {
        "name": "刘思远",
        "sub": "高级前端工程师 · 5年经验 · React / Next.js / TypeScript",
        "email": "liusiyuan@email.com", "phone": "13800006666",
        "tags": ["React", "Next.js", "TypeScript", "Tailwind CSS", "Node.js", "GraphQL", "Webpack", "性能优化", "i18n"],
        "secs": [
            ("求职意向", [("", "高级前端工程师，期望薪资 35K-48K")]),
            ("工作经历", [
                ("鲸灵科技 | 前端技术负责人", "2023.06 - 至今", [
                    "跨境电商SaaS平台前端架构，基于React + Next.js + TypeScript",
                    "性能优化：首屏加载从4.2s降到1.1s，Lighthouse评分从45提升到92",
                    "搭建150+组件库，单元测试覆盖率85%，3条业务线复用",
                    "SSR改造，SEO流量提升200%，Google排名显著上升",
                ]),
                ("云帆网络 | 前端工程师", "2021.03 - 2023.05", [
                    "电商后台管理系统：商品管理/订单管理/数据看板核心模块开发",
                    "实现动态表单渲染引擎，需求开发周期从3天缩短到半天",
                ]),
            ]),
            ("教育背景", [("", "华中科技大学 | 本科 | 软件工程 | 2015-2019")]),
            ("个人项目", [("", "技术博客 siyuan.dev（月均PV 2万+）|  GitHub：github.com/siyuan-liu")]),
        ],
    },
    {
        "name": "赵雪莹",
        "sub": "跨境财务经理 · 6年经验 · VAT合规 / 多币种核算 / 四大背景",
        "email": "zhaoxueying@email.com", "phone": "13800007777",
        "tags": ["跨境财务", "多币种核算", "VAT合规", "外汇风险管理", "转移定价", "US GAAP", "IFRS", "IPO审计"],
        "secs": [
            ("求职意向", [("", "跨境财务经理 / 国际税务专员，期望薪资 28K-38K")]),
            ("资质证书", [("", "注册会计师（CPA）  |  税务师")]),
            ("工作经历", [
                ("跨境通科技有限公司 | 财务经理", "2022.05 - 至今", [
                    "负责跨境电商业务全面财务管理，年交易额3亿+",
                    "搭建多币种核算体系（CNY/USD/EUR/IDR），汇率风险自动化对冲",
                    "主导VAT合规项目，完成英国、德国、法国三国VAT注册和申报",
                    "对接PingPong、连连支付等跨境收款平台，资金到账T+3优化到T+1",
                ]),
                ("安永会计师事务所 | 高级审计师", "2019.03 - 2022.04", [
                    "负责多家跨境电商和外贸企业的审计工作",
                    "深度参与某头部跨境电商IPO项目，精通US GAAP和IFRS准则",
                ]),
            ]),
            ("教育背景", [
                ("", "上海财经大学 | 硕士 | 会计学 | 2015-2017"),
                ("", "西南财经大学 | 本科 | 财务管理 | 2011-2015"),
            ]),
            ("自我评价", [("", "四大背景+跨境企业实战，能独当一面处理跨境财务合规问题。")]),
        ],
    },
    {
        "name": "吴嘉琳",
        "sub": "海外客服主管 · 5年经验 · 多语言团队 / Zendesk / NPS",
        "email": "wujialin@email.com", "phone": "13800008888",
        "tags": ["Zendesk", "客户成功", "多语言团队管理", "NPS", "SLA管理", "Knowledge Base", "英语专八", "印尼语"],
        "secs": [
            ("求职意向", [("", "海外客服主管 / 客户成功经理，期望薪资 25K-35K")]),
            ("工作经历", [
                ("赛兔科技 | 客户成功经理", "2022.08 - 至今", [
                    "带领8人多语言客服团队（英语/印尼语/泰语），服务2000+海外企业客户",
                    "搭建Zendesk工单系统，SLA达标率从82%提升到96%，NPS从32提升到56",
                    "建立Knowledge Base（300+篇文章），自助解决率从15%提升到45%",
                    "与产品团队建立客户反馈闭环，推动30+产品改进需求落地",
                ]),
                ("Shopee跨境 | 大客户服务专员", "2020.02 - 2022.07", [
                    "处理平台大卖家售后问题，日均处理工单50+，年度优秀员工，好评率98%",
                ]),
            ]),
            ("教育背景", [("", "北京外国语大学 | 本科 | 英语（国际商务方向）| 2014-2018")]),
            ("语言能力", [("", "英语：专业八级（母语级商务沟通）  |  印尼语：商务水平（读写流利）")]),
        ],
    },
    {
        "name": "黄凯文",
        "sub": "高级数据分析师 · 4年经验 · 机器学习 / AB实验 / 用户画像",
        "email": "huangkaiwen@email.com", "phone": "13800009999",
        "tags": ["SQL", "Python", "Pandas", "Machine Learning", "Tableau", "AB实验", "时间序列预测", "用户画像"],
        "secs": [
            ("求职意向", [("", "高级数据分析师 / 数据产品经理，期望薪资 30K-42K")]),
            ("工作经历", [
                ("数据脉科技 | 数据分析负责人", "2023.04 - 至今", [
                    "跨境电商数据平台搭建，日处理数据量10亿+条",
                    "RFM+Cohort用户行为分析模型，高价值用户留存率提升35%",
                    "Prophet+LSTM商品销量预测模型，准确率85%+，指导采购决策",
                    "搭建AB实验平台，支撑产品和运营团队的日常实验分析",
                ]),
                ("字节跳动（内部创业）| 数据分析师", "2021.06 - 2023.03", [
                    "国际化电商项目数据分析：用户增长/交易转化/供应链效率",
                    "搭建指标体系（北极星指标→一级→二级），对齐业务目标与数据口径",
                ]),
            ]),
            ("教育背景", [
                ("", "北京大学 | 硕士 | 应用统计 | 2017-2019"),
                ("", "复旦大学 | 本科 | 数学与应用数学 | 2013-2017"),
            ]),
            ("自我评价", [("", "擅长从海量数据中提取业务洞察，用数据驱动决策。")]),
        ],
    },
    {
        "name": "苏雨薇",
        "sub": "海外社交媒体运营 · 3年经验 · TikTok / Instagram / KOL合作",
        "email": "suyuwei@email.com", "phone": "13800000000",
        "tags": ["TikTok运营", "Instagram Reels", "YouTube Shorts", "短视频策划", "KOL合作", "CapCut", "Canva", "英语流利"],
        "secs": [
            ("求职意向", [
                ("", "海外社交媒体运营 / 内容营销经理，期望薪资 22K-30K"),
                ("", "作品链接：tiktok.com/@出海创意"),
            ]),
            ("工作经历", [
                ("出海创意 | 内容营销负责人", "2024.01 - 至今", [
                    "负责3个品牌在TikTok/Instagram/YouTube的社交媒体运营",
                    "策划TikTok系列内容累计播放量2亿+，单条最高1200万播放",
                    "搭建500+海外KOL合作网络，CPM成本低于行业平均30%",
                    "主导UGC活动产生10万+用户原创内容，品牌话题页浏览5000万+",
                ]),
                ("某跨境电商公司 | 社媒运营专员", "2022.06 - 2023.12", [
                    "独立运营品牌TikTok账号，6个月涨粉80万，带动独立站流量提升200%",
                    "策划的「开箱挑战」活动成为TikTok当周热门话题",
                ]),
            ]),
            ("教育背景", [("", "中国传媒大学 | 本科 | 网络与新媒体 | 2017-2021")]),
            ("自我评价", [("", "深谙海外社交媒体算法和用户心理，擅长用内容讲故事驱动增长。")]),
        ],
    },
]


def build(data, out):
    doc = fitz.open()
    p = new_page(doc)

    header(p, data["name"], data["sub"], data["email"], data["phone"])
    y = 90

    p.draw_rect(fitz.Rect(0, y, PAGE_W, 34), color=None, fill=BG)
    y = tags(p, y + 5, data["tags"])
    y += 6

    for s_title, items in data["secs"]:
        if y > PAGE_H - 40:
            p = new_page(doc)
            y = 30
        y = stitle(p, y, s_title)

        for item in items:
            if y > PAGE_H - 25:
                p = new_page(doc)
                y = 30
            if len(item) == 3 and isinstance(item[2], list):
                role, date_str, bullets = item
                y = brow(p, y, role, date_str)
                for b in bullets:
                    if y > PAGE_H - 20:
                        p = new_page(doc)
                        y = 30
                    y = bul(p, y, b)
            else:
                _, text = item
                y = bline(p, y, text)
            y += 1
        y += 6

    # Footer
    txt(p, PAGE_W - M - 120, PAGE_H - 18, "AI招聘系统自动生成 · 跨境通科技", size=6.5, color=GRAY_LT)

    doc.save(str(out))
    doc.close()


for i, r in enumerate(resumes):
    fname = f"resume_{i+1:02d}_{r['name']}.pdf"
    path = OUTPUT_DIR / fname
    build(r, path)
    print(f"[{i+1}/10] {fname}")

print(f"\nDone! Files in: {OUTPUT_DIR}")
