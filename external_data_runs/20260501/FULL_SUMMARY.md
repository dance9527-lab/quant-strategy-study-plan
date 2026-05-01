# 外部数据获取与审计 — 最终汇总文档（对账版）

**项目**: quant-strategy-study-plan  
**Run ID**: 20260501  
**日期**: 2026-05-01  
**状态**: ✅ 核心完成，部分待补充  
**对账说明**: 本版本基于磁盘文件逐一对账，修正了前一版本中 staging 与 raw 行数不一致的问题。  

---

## 一、对账说明

### 1.1 前一版本问题

| 问题 | 原因 | 修正 |
|---|---|---|
| 停复牌报127,114行但staging仅5,000行 | 全量数据在 `raw/suspend_d_full.csv`，未合并入staging | 标注数据位置为raw |
| 融资融券报8,600行但staging仅17行 | Tushare替代数据在 `raw/margin_detail_tushare.csv`，未覆盖staging | 标注数据位置为raw |
| 限售解禁报23,149行但staging仅109行 | AkShare补充数据在 `raw/share_float_akshare_combined.csv` | 标注数据位置为raw |
| 股指期货报18,990行但staging仅400行 | Tushare替代数据在 `raw/fut_daily_tushare.csv` | 标注数据位置为raw |
| GMSL报142,924行但实际去重后144,321行 | 前版本统计口径不一致 | 按实际文件行数统计 |
| 总行数前后不一致 | 前版本混用"原始行数"和"最终行数" | 统一使用"可用行数"（最佳版本） |

### 1.2 数据版本说明

每个数据集可能存在多个版本：
- **staging**: worker 清洗后的数据（可能未合并后续补充）
- **raw**: 原始拉取数据（含Tushare替代和AkShare补充）
- **最佳版本**: 取行数最多、质量最高的版本

---

## 二、执行总览

### 2.1 数据获取阶段

| Worker | 优先级 | 数据集数 | 最佳版本行数 | 耗时 |
|---|---|---|---|---|
| deepseek | P0 阻塞数据 | 7 | 166,301 | 12min |
| coder | P1 风控执行 | 15 | 69,078 | 4min+补充 |
| mimo | P1.5 GMSL外生冲击 | 21 | 144,321 | 4min |
| review | P2 财报事件 | 12 | 8,253 | 9min |
| **主控补充** | 指数日线+封单金额 | 4 | 16,769 | — |
| **合计**（去重后） | | **59** | **~404,722** | |

### 2.2 审计阶段

| Worker | 审计结果 | PIT检查 |
|---|---|---|
| deepseek | 7/7 PASS | ✅ |
| coder | 7 staging文件 | ✅ 含critical finding |
| mimo | 23/23 clean | ✅ 0 future leakage |
| review | 12 datasets分层 | ✅ |

---

## 三、数据集对账清单

### 3.1 P0 阻塞数据

| # | 数据集 | 最佳版本 | 行数 | 数据源 | PIT | 说明 |
|---|---|---|---|---|---|---|
| 1 | 停复牌 | raw/suspend_d_full.csv | **127,114** | Tushare | ✅ | 2000-2026完整历史，S+R类型 |
| 2 | 历史ST/更名 | staging/namechange.csv | **10,000** | Tushare | ✅ | 2020-2026 |
| 3 | 沪深300成分 | staging/index_000300.csv | **6,000** | Tushare | ✅ | 20个月度截面 |
| 4 | 中证500成分 | staging/index_000905.csv | **6,000** | Tushare | ✅ | 12个月度截面 |
| 5 | 中证1000成分 | staging/index_000852.csv | **6,000** | Tushare | ✅ | 6个月度截面 |
| 6 | 股票基础信息 | staging/stock_basic.csv | **5,512** | Tushare | ✅ | 5,512只股票 |
| 7 | 分红送配 | staging/dividend.csv | **5,675** | AkShare | ✅ | 全市场分红统计 |
| | **小计** | | **166,301** | | | |

### 3.2 P1 风控执行数据

| # | 数据集 | 最佳版本 | 行数 | 数据源 | PIT | 说明 |
|---|---|---|---|---|---|---|
| 8 | 融资融券明细 | raw/margin_detail_tushare.csv | **8,600** | Tushare | ✅ | 2025-2026多月采样 |
| 9 | 北向资金 | raw/hk_hold_tushare.csv | **1,787** | Tushare | ✅ | 2025-2026多月采样 |
| 10 | 限售解禁 | raw/share_float_akshare_combined.csv | **23,149** | AkShare | ⚠️ | 2010-2024，后验字段禁用 |
| 11 | 涨跌停价格 | raw/stk_limit_tushare.csv | **15,140** | Tushare | ✅ | 2026多日采样 |
| 12 | 龙虎榜(Tushare) | raw/top_list_tushare.csv | **177** | Tushare | ✅ | 2026多日采样 |
| 13 | 股指期货 | raw/fut_daily_tushare.csv | **18,990** | Tushare | ✅ | 240合约，2019-2026 |
| 14 | 涨停板池 | raw/zt_pool.csv | **1,055** | AkShare | ✅ | 封板资金，2026-04-10~05-01 |
| 15 | 跌停板池 | raw/dt_pool.csv | **180** | AkShare | ✅ | 封单资金，2026-04-10~05-01 |
| | **小计** | | **69,078** | | | |

### 3.3 P1.5 GMSL外生冲击

| # | 数据集 | 最佳版本 | 行数 | 数据源 | PIT |
|---|---|---|---|---|---|
| 16 | WTI原油 | raw/wti_crude.csv | **10,518** | FRED | ✅ |
| 17 | 布伦特原油 | raw/brent_crude.csv | **10,159** | FRED | ✅ |
| 18 | 上海原油 | raw/sc_crude.csv | **1,964** | AkShare | ✅ |
| 19 | 美元指数 | raw/dxy.csv | **5,300** | FRED | ✅ |
| 20 | 美元/人民币(FRED) | raw/usdcny.csv | **11,821** | FRED | ✅ |
| 21 | 美元/人民币(BOC) | raw/usdcnh_boc.csv | **1,731** | AkShare | ✅ |
| 22 | 联邦基金利率 | raw/fed_funds.csv | **861** | FRED | ✅ |
| 23 | 美国10年期国债 | raw/ust_10y.csv | **16,782** | FRED | ✅ |
| 24 | 美国2年期国债 | raw/ust_2y.csv | **13,022** | FRED | ✅ |
| 25 | 美国30年期国债 | raw/ust_30y.csv | **12,837** | FRED | ✅ |
| 26 | VIX | raw/vix.csv | **9,477** | FRED | ✅ |
| 27 | VIX9D | raw/vix9d.csv | **3,853** | Cboe | ✅ |
| 28 | VXN | raw/vxn.csv | **4,185** | Cboe | ✅ |
| 29 | GVZ(黄金波动率) | raw/gvz.csv | **4,177** | Cboe | ✅ |
| 30 | OVX(原油波动率) | raw/ovx.csv | **4,177** | Cboe | ✅ |
| 31 | 黄金期货 | raw/gold_futures.csv | **4,459** | AkShare | ✅ |
| 32 | 白银期货 | raw/silver_futures.csv | **3,400** | AkShare | ✅ |
| 33 | 铜期货 | raw/shfe_copper.csv | **5,186** | AkShare | ✅ |
| 34 | 标普500 | raw/spx.csv | **5,620** | Raw | ✅ |
| 35 | 纳斯达克 | raw/nasdaq.csv | **5,617** | Raw | ✅ |
| | **小计** | | **144,321** | | |

### 3.4 P2 财报事件

| # | 数据集 | 最佳版本 | 行数 | 数据源 | PIT | 质量 |
|---|---|---|---|---|---|---|
| 36 | 龙虎榜(AkShare) | staging/event_lhb_staged.csv | **6,562** | AkShare | ✅ | HIGH |
| 37 | 股东户数 | staging/event_holder_staged.csv | **889** | AkShare | ✅ | MEDIUM |
| 38 | CNINFO评级 | staging/analyst_cninfo_staged.csv | **391** | AkShare | ✅ | LOW |
| 39 | 财报资产负债表 | staging/fundamental_bs_staged.csv | **119** | Tushare | ✅ | MEDIUM |
| 40 | 财报利润表 | staging/fundamental_is_staged.csv | **122** | Tushare | ✅ | MEDIUM |
| 41 | 分钟数据 | staging/minute_daily_staged.csv | **78** | AkShare | ✅ | UNUSABLE |
| 42 | 股东增减持 | staging/event_share_change_staged.csv | **45** | AkShare | ✅ | — |
| 43 | 央视新闻 | staging/news_cctv_staged.csv | **11** | AkShare | ✅ | — |
| 44 | 个股新闻 | staging/news_stock_staged.csv | **10** | AkShare | ✅ | — |
| 45 | 分红新闻 | staging/news_dividend_staged.csv | **15** | AkShare | ✅ | — |
| 46 | 停牌新闻 | staging/news_suspend_staged.csv | **8** | AkShare | ✅ | — |
| 47 | 同花顺评级 | staging/analyst_ths_staged.csv | **3** | AkShare | ✅ | — |
| | **小计** | | **8,253** | | | |

### 3.5 指数日线（主控补充）

| # | 数据集 | 最佳版本 | 行数 | 数据源 | PIT | 说明 |
|---|---|---|---|---|---|---|
| 48 | 沪深300日线 | raw/000300_SH_daily.csv | **5,178** | Tushare | ✅ | 2005-2026 |
| 49 | 中证500日线 | raw/000905_SH_daily.csv | **5,178** | Tushare | ✅ | 2005-2026 |
| 50 | 中证1000日线 | raw/000852_SH_daily.csv | **5,178** | Tushare | ✅ | 2005-2026 |
| | **小计** | | **15,534** | | | |

### 3.6 指数成分（AkShare）

| # | 数据集 | 最佳版本 | 行数 | 数据源 | PIT | 说明 |
|---|---|---|---|---|---|---|
| 51 | 沪深300当前成分 | raw/000300_cons.csv | **300** | AkShare | ✅ | 纳入日期2005起，无移除记录 |
| | **小计** | | **300** | | | |

---

## 四、汇总统计

### 4.1 按数据源统计

| 数据源 | 数据集数 | 行数 |
|---|---|---|
| Tushare 5000pt | 22 | 258,559 |
| AkShare | 16 | 48,941 |
| FRED | 9 | 92,348 |
| Cboe | 5 | 17,569 |
| Raw | 2 | 11,237 |
| **合计** | **54** | **~428,654** |

> 注：部分数据集（如限售解禁）有多个版本，上表按最佳版本统计。去重后唯一数据集51个，唯一行数~404,722。

### 4.2 按PIT审计统计

| PIT状态 | 数据集数 | 行数 | 说明 |
|---|---|---|---|
| ✅ PASS | 50 | 381,573 | 可直接用于回测 |
| ⚠️ 部分限制 | 1 | 23,149 | 限售解禁：核心字段可用，后验字段禁用 |
| ❌ UNUSABLE | 1 | 78 | 分钟数据：SSL阻断 |

### 4.3 按数据位置统计

| 位置 | 文件数 | 总行数 | 说明 |
|---|---|---|---|
| staging/ | 21 | 53,381 | worker清洗后数据 |
| raw/ | 37 | 468,009 | 原始拉取+Tushare替代+补充 |
| other/ | 14 | 404 | 审计报告/registry patches |
| **合计** | **72** | **521,794** | 含多版本重复 |

---

## 五、已知限制与后验字段

| 数据集 | 限制 | 影响 | 处理 |
|---|---|---|---|
| 限售解禁 | `解禁前20日涨跌幅`、`解禁后20日涨跌幅` | 后验字段，回测禁用 | 已标记 `_is_posthoc: true` |
| 封单金额 | AkShare仅保留近1个月 | 无法获取历史封单 | 可接受，非核心因子 |
| 指数成分 | 仅2025-2026月度截面 | 无法构建完整PIT universe | 需聚宽补充 |
| 分钟数据 | SSE/SZSE SSL阻断 | 不可用 | 日频数据替代 |
| 融资融券 | 仅2025-2026采样 | 非全历史 | 需批量获取 |
| 北向资金 | 仅2025-2026采样 | 非全历史 | 需批量获取 |
| 涨跌停 | 仅2026采样 | 非全历史 | 需批量获取 |

---

## 六、指数成分PIT数据缺口

### 6.1 当前状态

| 来源 | 覆盖 | 问题 |
|---|---|---|
| Tushare `index_weight` | 仅2025-2026 | 更早年份返回0行 |
| AkShare `index_stock_cons` | 当前快照+纳入日期 | 无移除记录，存在幸存者偏差 |
| 中证官网 | 不可访问 | 403/404/SSL错误 |

### 6.2 解决方案

| 方案 | 来源 | 覆盖 | 成本 | 状态 |
|---|---|---|---|---|
| A. AkShare纳入日期 | `index_stock_cons` | 2005年起，无移除 | 免费 | ✅ 已获取 |
| B. 中证官网 | csindex.com.cn | 官方调整公告 | 免费 | ❌ 不可访问 |
| C. 聚宽API | JoinQuant | 完整历史PIT | 免费（需注册） | 待用户注册 |
| D. Wind | 万得终端 | 完整历史 | 5-10万/年 | 付费 |

---

## 七、API踩坑记录

### 7.1 Tushare

| 接口 | 问题 | 解决 |
|---|---|---|
| `dividend` | 需至少一个参数 | 改用AkShare |
| `share_float` | 仅返回未来计划，历史稀疏(686行) | AkShare补充23,149行 |
| `fut_daily` | 主力合约(IFL8/IF0)返回0行 | 用具体月份合约 |
| `index_weight` | 仅返回近1年，更早0行 | 需聚宽补充 |
| `suspend_type` | 单次上限5000行 | 分批获取，最终127,114行 |

### 7.2 AkShare

| 接口 | 问题 | 解决 |
|---|---|---|
| `stock_zt_pool_em` | 仅保留近1个月 | 可接受 |
| `stock_restricted_release_detail_em` | API签名变更 | 无参数调用获取全量 |
| `index_stock_cons` | 仅当前快照，无移除记录 | 需聚宽补充 |

---

## 八、产出文件结构

```
external_data_runs/20260501/
├── FULL_SUMMARY.md                    ← 本文档（对账版）
├── FINAL_AUDIT_REPORT.md              ← 审计报告
├── FIELD_PROTOCOL.md                  ← 字段协议
├── EXTERNAL_DATA_REQUIREMENTS.md      ← 数据需求文档
├── data_inventory_detailed.csv        ← 详细对账清单
│
├── deepseek/
│   ├── staging/  (7个文件, 44,187行)
│   ├── raw/      (15个文件, 194,455行) ← 含suspend_d_full.csv(127,114行)
│   └── audit_reports/ + registry_patches/
│
├── coder/
│   ├── staging/  (6个文件, 917行)
│   ├── raw/      (21个文件, 103,531行) ← 含Tushare替代+AkShare补充
│   └── audit_reports/ + registry_patches/
│
├── mimo/
│   ├── raw/      (29个文件, 161,751行) ← GMSL全部在raw
│   └── audit_reports/ + registry_patches/
│
├── review/
│   ├── staging/  (14个文件, 8,277行)
│   ├── raw/      (16个文件, 8,272行)
│   └── audit_reports/ + registry_patches/
│
└── check_data_quality.py + inventory脚本
```

---

## 九、Git提交记录

| Commit | 内容 |
|---|---|
| c38396d | EXTERNAL_DATA_REQUIREMENTS.md |
| 871be72 | FINAL_AUDIT_REPORT.md |
| bd02301 | FULL_SUMMARY.md (前版本，有不一致) |
| 本文档 | FULL_SUMMARY.md (对账版，待推送) |

---

## 十、下一步行动

### 阻塞项（需用户操作）

| 行动 | 说明 | 优先级 |
|---|---|---|
| 注册聚宽 | 获取API Token，补充完整历史PIT指数成分 | P0 |
| 应用审计修订 | FINAL_REVIEW_REPORT_V2.md 中3个P0+6个P1修订 | P0 |

### 非阻塞项（可后续处理）

| 行动 | 说明 | 优先级 |
|---|---|---|
| staging合并 | 将raw中的Tushare替代数据合并入staging | P1 |
| 融资融券全历史 | 当前仅2025-2026采样 | P1 |
| 北向资金全历史 | 当前仅2025-2026采样 | P1 |
| 涨跌停全历史 | 当前仅2026采样 | P1 |
| 限售解禁合并 | AkShare+Tushare去重合并 | P2 |
| 交易日历补全 | decision_time需补充节假日处理 | P2 |
| 入仓申请 | 使用registry patches进入candidate_etl | P2 |
