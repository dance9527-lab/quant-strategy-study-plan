# 数据缺口总结与获取方向可行性研究

> 日期：2026-05-01
> 审计依据：quant_strategy_plan.md、quant_strategy_research_plan_detailed.md、DATA_USAGE_GUIDE.md、WAREHOUSE_README.md、external_data_sources.csv

---

## 一、数据缺口清单

### 阻塞S1启动（missing — 需从现有warehouse生成，非外部数据）

| # | 缺口 | 当前状态 | 影响 |
|---|---|---|---|
| 1 | walk_forward_calendar_v1 | 未生成 | S1训练的日期网格不存在 |
| 2 | holdout_access_log.tsv | 未生成 | 无法追踪holdout污染状态 |
| 3 | test_family_registry | 未生成 | 无法执行FDR多重比较校正 |
| 4 | execution_label_audit | 未生成 | 无法验证标签与执行对齐 |
| 5 | track_registry_v1 | 未生成 | track定义和参数hash不存在 |
| 6 | universe_daily_construction_audit | 未生成 | universe构建逻辑未审计 |
| 7 | WalkForwardCalendarValidator | 未生成 | 日历校验器不存在 |
| 8 | valuation_coverage_audit | 未生成 | 估值字段覆盖未审计 |
| 9 | 停牌推断precision/recall验证 | 未生成 | is_suspended_inferred准确性未验证 |
| 10 | 估值available_at抽样审计 | 未生成 | 估值PIT未验证 |

**注**：以上10个缺口均为内部治理工件，需从现有warehouse数据生成，不依赖外部数据源。

### 阻塞S1 keep（blocked_by_source_gap — 需外部数据源）

| # | 缺口 | 当前状态 | 影响 |
|---|---|---|---|
| 11 | 完整公司行为主表 | AkShare sanity reference 5675行 | 无法做total-return accounting |
| 12 | 沪/北历史ST事件 | 只有深市2023年以来 | 历史ST过滤不完整 |
| 13 | 完整停复牌历史 | 只有2023年以来提醒 | 停牌推断precision无法验证 |
| 14 | 历史PIT指数成分权重 | 只有最新快照 | 指数增强策略无法历史回测 |
| 15 | orders_audit | 未生成 | 执行审计不闭合 |
| 16 | 冻结模型registry | 未生成 | 模型版本管理不闭合 |
| 17 | SQLite WAL实验台账 | 未生成 | 实验记录无法持久化 |
| 18 | daily_turnover_capacity_report | 未生成 | 容量评估不闭合 |

### 阻塞P1/P1.5增强（candidate_etl — 仅source registered，无ETL脚本）

| # | 缺口 | 用途 | 数据量级 |
|---|---|---|---|
| 19 | 融资融券 | 杠杆资金、拥挤监控 | 日频，~5000只×6000天 |
| 20 | 北向资金 | 风格切换、行业资金流 | 日频，~5000只×3000天 |
| 21 | 限售解禁 | 供给压力 | 事件级，~10万条 |
| 22 | 市场宽度/涨跌停 | 风险开关、拥挤踩踏 | 日频，~6000天 |
| 23 | ETF申赎 | 被动资金影响 | 日频，~500只×6000天 |
| 24 | 股指期货basis/OI | 对冲成本、风格去杠杆 | 日频，4合约×6000天 |
| 25 | 筹码分布 | 筹码动量候选 | 日频，~5000只×6000天 |
| 26 | GMSL完整数据 | 外生冲击 | 日频，~20指标×10000天 |
| 27 | limit_events | 盘中涨跌停信号 | 事件级，~50万条 |
| 28 | 分钟/集合竞价 | 精细执行审计 | 分钟级，海量数据 |

### P2-P4候选（不阻塞近期工作）

| # | 缺口 | 用途 | 优先级 |
|---|---|---|---|
| 29 | 财报/业绩预告 | 基本面解释力 | P2 |
| 30 | 分析师预期 | 预期修正因子 | P2 |
| 31 | 股东户数/质押/龙虎榜/大宗 | 事件解释力 | P2-P3 |
| 32 | 期权分钟 | 波动率策略 | P4 |
| 33 | 新闻事件 | 事件驱动 | P4 |

---

## 二、获取方向可行性研究

### Tier 1：免费可获取，低难度，可立即开始（7个）

| # | 缺口 | 免费渠道 | API接口 | 稳定性 | ETL复杂度 |
|---|---|---|---|---|---|
| 19 | 融资融券 | AkShare | `stock_margin_detail_sse/szse` | ★★★★★ | 简单 |
| 20 | 北向资金 | AkShare | `stock_hsgt_north_net_flow_in_em` | ★★★★★ | 简单 |
| 22 | 市场宽度 | AkShare | `stock_zt_pool_em`/`stock_dt_pool_em` | ★★★★★ | 简单 |
| 24 | 股指期货 | AkShare | `futures_main_sina` | ★★★★★ | 简单 |
| 11 | 公司行为 | AkShare + Tushare | `stock_history_dividend_detail`/`dividend` | ★★★★☆ | 中等（需遍历个股） |
| 21 | 限售解禁 | AkShare + Tushare | `stock_restricted_release_detail` | ★★★★☆ | 中等 |
| 23 | ETF申赎 | AkShare + Tushare | `fund_etf_hist_em`/`fund_share` | ★★★★☆ | 中等 |

**预计完成时间**：5个工作日

### Tier 2：免费但需工程投入，中难度（6个）

| # | 缺口 | 免费渠道 | 付费替代 | 推荐方案 |
|---|---|---|---|---|
| 26 | GMSL数据 | fredapi（免费API key）+ AkShare中国宏观 | Wind宏观数据模块 | fredapi + AkShare |
| 12 | 历史ST事件 | AkShare近期 + Tushare积分 | Wind完整历史 | Tushare 120积分 |
| 13 | 停复牌历史 | AkShare2023年以来 + Tushare积分 | Wind完整历史 | Tushare 120积分 |
| 14 | PIT指数成分 | 聚宽免费API（近5年） | Wind完整历史 | 聚宽 + Wind补充 |
| 29 | 财报/业绩预告 | Tushare 120积分 | Wind PIT质量更好 | Tushare 120积分 |
| 27 | limit_events | AkShare涨跌停池 | Wind盘中数据 | AkShare |

**关键行动**：先确认Tushare积分等级。120积分可解锁4-5个重要缺口（ST/停复牌/财报/限售/分红）。

### Tier 3：几乎必须付费，高难度（5个）

| # | 缺口 | 免费渠道 | 付费渠道 | 推荐方案 |
|---|---|---|---|---|
| 28 | 分钟/集合竞价 | AkShare近1年 | Wind/通联数据/券商Level2 | AkShare近期 + 通联历史 |
| 30 | 分析师预期 | AkShare部分接口（60-70%覆盖） | 朝阳永续/通联/iFinD | AkShare + 朝阳永续 |
| 25 | 筹码分布 | 无可靠免费批量渠道 | Wind/通达信Level2 | DIY近似指标（N日加权平均成本）或Wind |
| 32 | 期权分钟 | 有限免费数据 | 交易所授权/Wind | 日频验证后再考虑 |
| 33 | 新闻事件 | 巨潮公告 | Wind新闻库 | 远期考虑 |

---

## 三、GMSL数据获取详细方案

GMSL当前只有Cboe VIX/OVX/GVZ，FRED全部超时。获取方向：

| 数据 | 免费方案 | 付费方案 | 推荐 |
|---|---|---|---|
| Brent/WTI油价 | fredapi（API key免费）| Wind | fredapi |
| DXY美元指数 | fredapi | Wind | fredapi |
| USD/CNH | AkShare `fx_spot_quote` | Wind | AkShare |
| UST2Y/10Y | 已在reference_rates中 | — | 已有 |
| 全球股指期货 | Yahoo Finance/AkShare | Wind | AkShare |
| MOVE指数 | fredapi | Wind | fredapi |
| SC原油期货 | AkShare期货接口 | Wind | AkShare |

**fredapi注册**：https://fred.stlouisfed.org/docs/api/api_key.html （免费，需邮箱注册）

---

## 四、优先级行动清单

### 第一阶段：治理工件（阻塞S1启动，无需外部数据）
1. walk_forward_calendar_v1
2. holdout_access_log.tsv
3. test_family_registry
4. execution_label_audit
5. track_registry_v1
6. universe_daily_construction_audit

### 第二阶段：免费数据获取（5个工作日）
1. 确认Tushare积分等级
2. 融资融券 + 北向资金 + 市场宽度 + 股指期货（2天）
3. 公司行为分红 + 限售解禁 + ETF申赎（3天）
4. 注册fredapi，获取GMSL替代数据（1天）

### 第三阶段：Tushare积分数据（3个工作日）
1. 历史ST事件
2. 停复牌历史
3. 财报/业绩预告

### 第四阶段：付费数据（按需）
1. PIT指数成分（聚宽免费 + Wind补充）
2. 分钟数据（AkShare近期 + 通联历史）
3. 分析师预期（AkShare + 朝阳永续）

---

## 五、数据源价格参考

| 数据商 | 年费范围 | 覆盖范围 | 适用场景 |
|---|---|---|---|
| AkShare | 免费 | A股基础数据 | Tier 1-2 |
| Tushare | 免费（120积分）/ 付费（更高积分） | A股全面数据 | Tier 1-3 |
| 聚宽 | 免费API / 付费数据 | A股+指数成分 | PIT指数成分 |
| Wind | 5-10万/年 | 全市场全品种 | 完整PIT数据 |
| 通联数据 | 3-8万/年 | A股+分钟数据 | 分钟级历史 |
| 朝阳永续 | 2-5万/年 | 分析师预期 | 预期因子 |
| iFinD（同花顺）| 2-5万/年 | A股全面数据 | 性价比方案 |
| fredapi | 免费 | 全球宏观 | GMSL数据 |

---

*报告生成时间：2026-05-01 17:55 CST*
