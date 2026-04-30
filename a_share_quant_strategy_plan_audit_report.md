# 中国 A 股量化策略实验设计与数据体系独立审计报告

**审计对象**：`quant_strategy_plan.md`、`quant_strategy_research_plan_detailed.md`
**数据依据**：`DATA_USAGE_GUIDE.md`、`WAREHOUSE_README.md`、`external_data_sources.csv`、`validation_params.json`
**审计日期**：2026-04-29
**审计角色**：量化策略 / 金融工程 / 机器学习与深度学习独立评估

---

## 0. 审计摘要

本轮规划的总体质量显著高于一般量化研究计划。它已经把 A 股策略最常见的失败点——未来信息、幸存者偏差、涨跌停不可成交、停牌、成本低估、naive random split、过拟合和 benchmark 选择污染——作为 P0/P1 约束写入流程。当前规划可以启动 **日频多因子强基线 Phase A**，但不应直接进入“可部署策略”或“高收益低风险”叙事。

我的独立结论如下：

| 维度 | 评分 | 裁决 |
|---|---:|---|
| 数据时点与 PIT 意识 | 8.5/10 | 已有较强框架，但估值、ST、停复牌、行业、公司行为仍有未闭环源。 |
| 回测可成交性 | 8.0/10 | 涨跌停、停牌、T+1、容量已被前置；还需补真实开盘/集合竞价、券商级执行和合规约束。 |
| 验证与防过拟合 | 8.0/10 | purge/embargo、HAC、bootstrap、FDR、DSR/PBO 基本正确；仍需降低 24-step 误用风险，明确测试族与 holdout 治理。 |
| 数据落地可用性 | 7.0/10 | 当前 warehouse 足以做 S1，但参考资料之间有版本不一致，外部源登记滞后于策略优先级。 |
| concept shift 应对 | 6.5/10 | 已避免动态泄漏，但目前偏“诊断/告警”，不足以应对 2023-2025 机制性定价变化。建议重构为“结构性 regime 协议 + 日期均衡样本权重 + 拥挤度/流动性风险层 + 嵌套选择”。 |
| 未来实际部署准备度 | 6.5/10 | 研究纪律强，但距离实盘还缺订单路由、实时风控、合规限额、数据延迟监控、券商回报闭环和 shadow/live-small 协议。 |

**最重要的审计意见**：现有 R5 concept shift 方案“废弃双轨/动态 alpha/在线 Track B，改为单轨 5 年 rolling + 指数衰减权重 + 成熟 IC yellow/red 告警”是一个正确的反泄漏修正，但不足以覆盖用户补充背景中的机制性变化。应保留其反泄漏精神，同时新增一个不会使用当前 OOT 标签的 **结构性变迁适配层**，把 A 股制度变化、量化拥挤、流动性踩踏和监管变化显式纳入验证与风险预算，而不是只作为报告切片。

---

## 1. 本次审计范围和材料完整性

### 1.1 文件完整性

| 文件 | 行数 | SHA256 |
|---|---:|---|
| `quant_strategy_plan.md` | 366 | `acf2bdcca8f640b7db6d18c4bda04a9c9fd5551b726fe5655eae7689a7f72e15` |
| `quant_strategy_research_plan_detailed.md` | 1119 | `0dfaa260b35a08b49712442c26399a183664d92998910168d9b16ed4ce8f77ca` |
| `DATA_USAGE_GUIDE.md` | 308 | `a8c70f553c883935ec750011f7245bc268e41e1501dd4bff7b564563abfbafd1` |
| `WAREHOUSE_README.md` | 230 | `bd6365179e16fbcab979869f6c426684e2293140d2aba8ec75f6ba8a5fbc3876` |
| `external_data_sources.csv` | 10 | `770cf4d457d4be0b48deb0fb719d8242b1ac697ba0aa8317d4dfd45d8d8122a6` |
| `validation_params.json` | 328 | `bf75d38303502ee4acba8d278822d6295d55d1ca3279ec7e689546b6001ae8e9` |

### 1.2 外部数据源登记状态

`external_data_sources.csv` 共登记 8 条外部源，状态分布如下：

| 状态 | 数量 |
|---|---:|
| `akshare_baidu_recent_ingested_partial` | 1 |
| `akshare_china_government_bond_yield_ingested` | 1 |
| `akshare_cninfo_ingested` | 1 |
| `akshare_csindex_ingested` | 1 |
| `planned_p2` | 2 |
| `planned_p3` | 2 |

已接入的源包括 PIT 行业归属、官方中证指数、国债收益率、2023 年以来部分停复牌提醒；仍处于 planned 的包括公司行为、指数成分、融资融券/北向/市场宽度、新闻公告等。这里存在一个优先级滞后问题：策略规划已把融资融券、北向资金、限售解禁列为 P1 candidate ETL 或 P1/P1.5 并行准备，但 `external_data_sources.csv` 仍把 `market_sentiment` 记为 `planned_p3`，应更新为 P1/P1.5 级 source registration。

### 1.3 明确限制

本次审计能够读取上传的策略文档、数据说明和参数文件，但无法直接访问用户本机 `D:\data\warehouse` 中的 Parquet 实表。因此本报告中的数据质量判断以文档披露、参数一致性和可落地性审计为主；正式执行前仍必须跑仓库级和实验级脚本验证。

---

## 2. 外部市场结构核验

用户补充的 concept shift 背景基本方向正确，但建议不要把“量化基金规模翻 3 倍”作为未经本地来源验证的硬事实写入策略文档。公开报道对规模口径存在差异：Reuters 在 2024 年 3 月称中国量化基金行业约为 2600 亿美元，并称行业三年内翻倍；另有报道引用 2021 年末约 1.26 万亿元人民币的官方口径。应在策略文档中写为“量化规模快速扩张、拥挤度上升，具体规模以登记源为准”，并把规模口径纳入数据源登记。

关键外部事实对策略设计的影响：

1. **全面注册制已是机制性变化**。2023-02-17，中国证监会发布全面实行股票发行注册制相关制度规则，并称注册制推广到全市场和各类公开发行股票行为。这会改变 IPO 供给、壳资源价值、上市公司质量分层和小微盘风险溢价。
2. **壳价值和退市逻辑继续变化**。2024-04-12 国务院“新国九条”要求严格强制退市、完善市值等交易类退市指标、进一步削减壳资源价值，并加强高频量化交易监管。这意味着小市值、ST、低质量壳股的风险收益不应继续按旧周期解释。
3. **程序化交易监管进入强约束**。2024 年证监会发布《证券市场程序化交易管理规定（试行）》，要求报告、监测、风险防控和高频交易差异化监管；2025 年沪深北交易所实施细则进一步明确异常交易与高频交易认定标准。即使当前策略是日频，也会影响高换手、小盘拥挤、开盘集中成交和未来分钟/事件策略。
4. **2024 年 2 月量化拥挤和踩踏是可观测压力事件**。交易所对灵均投资异常交易作出三日限制，Reuters 报道其在 9:30-9:31 一分钟内卖出约 25.7 亿元 A 股，且量化行业被认为与小盘股 boom-bust、市场波动和监管关注有关。2024 年上半年中国量化基金平均亏损、跟踪中证 1000 的产品承压更大，说明小盘/流动性/拥挤尾部风险不能只用普通波动率衡量。

这些事实支持本报告的核心结论：**A 股 2023-2025 的变化不是单纯周期性波动，至少包含发行制度、退市制度、交易监管、资金拥挤、风格容量和尾部流动性的机制性变化。**

---

## 3. 现有规划的主要优点

### 3.1 数据治理方向正确

规划明确 canonical 数据源为 `D:\data\warehouse`，并要求旧 `processed`、旧 qant cache 和随机验证结果只作为历史对照，不作为有效收益证据。数据说明显示当前仓库采用 PIT 思路，包含未复权日 K、PIT 复权收益、逐日可交易性、估值、benchmark、reference rate、PIT 行业、风险警示、成本、指数成分快照等。这个底座足以启动第一批日频股票多因子研究。

尤其值得肯定的是：

- `prices_daily_unadjusted` 用于真实成交价、涨跌停、停牌和容量。
- `prices_daily_returns.return_adjusted_pit` 用于标签、动量、波动率和绩效。
- `tradability_daily` 显式区分 bar 是否存在、推断停牌和可交易性。
- `security_master` 从日 K 文件补入当前列表外历史证券，降低幸存者偏差。
- `industry_classification.current_industry_snapshot` 被明确禁止用于历史 PIT 回测。
- benchmark 删除了旧同日成交额加权代理，避免后验放大当天上涨放量股票。
- `valuation_daily` 被标为 T 日 16:00 后可见，T+1 执行。

### 3.2 验证框架强于常规实践

详细规范把以下内容前置为硬约束或必要报告项：

- `feature_time <= available_at <= decision_time < execution_time <= label_end_time`
- 5 年 rolling walk-forward。
- `purge_days >= max(label_horizon*3, 40)`。
- 10 个交易日 embargo。
- split label audit。
- Newey-West HAC IC t-stat。
- block bootstrap，且报告 10/21/40 日 block 敏感性。
- FDR、多重检验、DSR/PBO、holdout 和参数扰动。
- 禁止 naive random 8/2 作为最终证据。
- 明确 qant random 高收益是 label 泄漏和验证污染下的反例。

这是正确方向。A 股横截面标签高度重叠、IC 自相关明显、市场状态切换频繁，普通 random split 和未 purge 的 OOT 月边界极易制造虚假 alpha。

### 3.3 可成交性前置是关键优点

规划要求 S1 就纳入 T+1、涨跌停、停牌、ST、上市年龄、100 股交易单位、基础成本、保守滑点、开盘 L1 冲击、成交失败、连续锁死、解锁反转和容量压力测试。这一点非常重要。A 股策略中大量纸面 alpha 来自真实无法买入或无法卖出的样本，尤其是涨停板、跌停板、停牌、ST、小微盘和新股。

### 3.4 对复杂模型保持克制

规划把深度时序、NLP、RL 降级到强基线之后，是合理的。当前最优先的不是引入 PatchTST/TFT 或强化学习，而是证明基础因子在 PIT、成本、容量、执行约束和 OOT 体系下是否仍有正向可交易超额。

---

## 4. 主要问题、错误和需修订点

### 4.1 文档版本存在不一致，必须先建立单一 build manifest

当前数据说明之间存在至少三类不一致或滞后：

| 问题 | 观察 | 风险 | 建议 |
|---|---|---|---|
| Reference rates 行数不一致 | `DATA_USAGE_GUIDE.md` 当前构建结果写 `Reference rate` 32,921 行；`quant_strategy_research_plan_detailed.md` 写 55,964 行；`WAREHOUSE_README.md` 后续 P1 更新写 Shibor 已新增至 55,964 行。 | 执行人员可能不知道 Shibor 是否已经可用，绩效和无风险利率口径分叉。 | 建立 `warehouse_build_manifest.json`，包含 `build_id`、表行数、最大日期、source status、leakage_check 时间；策略文档只引用 manifest，不手写行数。 |
| Shibor 状态不一致 | `DATA_USAGE_GUIDE.md` 仍写 Shibor 接口失败，后续修复；`WAREHOUSE_README.md` P1 update 写已接入 9 条 Shibor 序列。 | 无风险利率、资金利率和风险状态因子口径混乱。 | 更新 `DATA_USAGE_GUIDE.md` 与 `external_data_sources.csv`，区分国债、Shibor Eastmoney、Shibor Jin10、失败接口。 |
| 外部源优先级滞后 | `external_data_sources.csv` 把 `market_sentiment` 记为 planned_p3，但策略文档要求融资融券、北向资金、限售解禁作为 P1 candidate ETL。 | 任务排期和数据接入优先级冲突。 | 把 `market_sentiment` 拆成 `margin_trading_p1_candidate`、`northbound_p1_candidate`、`market_breadth_p1_5`、`ETF_flow_p1_5`。 |

这是一个治理问题，不一定说明数据本身错误，但会影响未来多人协作和回测可复现性。建议把所有行数和 source status 从策略文档移到 manifest，由策略文档引用 hash。

### 4.2 Concept shift 目前“反泄漏正确，但适配不足”

现有方案的优点是避免了最危险的做法：不再用同一步 OOT 标签做动态 alpha、模型切换、阈值调整或 Track B 在线更新。但它的问题也很明显：

1. **只靠 5 年 rolling + 12 个月半衰期样本权重，无法充分应对机制性断点**。全面注册制、退市规则、程序化交易监管、量化拥挤不是单纯的样本时间衰减问题。
2. **告警状态机只冻结 keep/晋级，不形成已验证的风险响应**。对于生产策略，等连续 6 步成熟 IC 为负再 red quarantine，可能已经经历数月损失。
3. **样本权重按行归一存在上市证券数扩张偏差**。2005 年股票数量和 2024 年股票数量差异巨大。如果每条 `(asset_id, trade_date)` 样本等权，后期日期天然因股票数多而权重大；再叠加指数衰减，会使近期大股票池时期被双重加权。这可能是想要的“近期适配”，但必须显式控制，否则训练目标从“每日横截面学习”变成“证券数加权学习”。
4. **结构性 regime 只作为报告切片，未进入模型选择和风险预算**。2023-2025 切片如果仅作为描述性报告，无法保证最终策略在新机制下稳健。
5. **拥挤度指标不够具体**。当前写了“拥挤度监控”，但没有明确数据、公式、阈值、与容量联动方式。

结论：应保留 R5 的反泄漏纪律，但将 concept shift 从“诊断项”升级为 **生产前必须通过的结构性稳健性层**。它不能改变当前 step 预测，但可以通过预注册、嵌套训练、成熟标签和 ex-ante 风险变量来决定策略是否允许进入生产。

### 4.3 默认股票池把研究 universe 与执行 universe 混在一起

`in_factor_research_universe = can_trade_close_based AND listing_age >= 60 AND NOT is_risk_warning_pit`，其中 `can_trade_close_based = can_buy_close_based AND can_sell_close_based`。这对保守组合回测有意义，但用于因子 IC/RankIC 研究可能过窄，且会隐性删除涨跌停附近的重要风险样本。

建议拆成三层：

| 层 | 用途 | 规则建议 |
|---|---|---|
| `research_observable_universe` | 因子 IC、特征分布、concept shift 诊断 | 已上市、bar 存在、非明显数据异常、满足基础生命周期；不要因为 T 日涨停/跌停直接删除。 |
| `entry_eligible_universe` | 买入候选 | T+1 可买约束、T 日涨停/一字板压力、ST、上市年龄、ADV、容量。 |
| `execution_accounting_universe` | 回测成交和持仓会计 | 订单层记录涨停买不到、跌停卖不出、停牌延迟和解锁后收益。 |

否则策略可能在研究阶段就把最危险的 limit-lock 样本删除，导致 IC 更干净但实盘尾部风险被低估。

### 4.4 估值因子的 PIT 风险仍然偏大

`valuation_daily` 被设置为 T 日 16:00 后可见，这对行情衍生的市值、换手率较合理，但对 PE、PB、PS、TTM 等字段不一定足够。供应商日频估值可能依赖财报披露、追溯调整、口径更正和复权/股本变化。若没有公告日、报告期、财务重述和 vendor calculation time，估值类因子不能被简单等同于 PIT 基本面因子。

建议：

- 将 `valuation_daily` 字段拆成 **市场可得慢变量** 与 **财报派生变量**。
- 市值、流通市值、换手率可先进入 P1。
- PE/PB/PS/TTM、ROE、净利润同比等必须在接入 `financial_disclosures` 后做公告日校验。
- 在 S1 报告中分别给出 `market-only baseline` 和 `valuation/fundamental baseline`，避免基础行情 alpha 与潜在财报时点误差混在一起。
- 对 2026-01-05 至 2026-02-05 估值缺口，保留已有 drop/no-valuation/ffill 三口径，但任何依赖 ffill 才成立的结果不得 keep。

### 4.5 公司行为和 total return 校验应更早

当前使用 `return_adjusted_pit` 作为收益标签和绩效，但公司行为、分红送配、除权除息事件尚未形成独立主表。仅有复权因子并不足以证明 total return 口径正确，因为需要验证：

- 除权除息日和可得日。
- 现金分红是否纳入收益。
- 送转、配股、拆细、合并的处理。
- 停牌/退市期间复权因子晚于最后 bar 的情况。
- 因子重复日期去重是否影响标签。

建议把公司行为从 P1.5 提升为 **P1 数据审计并行项**：不一定作为 alpha 因子，但必须用于标签与绩效会计复核。若没有公司行为表，S1 仍可跑，但报告应标注为“adjusted-return proxy”，不能宣称已经完成 total-return accounting。

### 4.6 容量模型应加入“拥挤容量”，不只看自有参与率

当前容量测试主要基于 trailing ADV、参与率、成交失败率、资金档和滑点。对 A 股量化而言这还不够，因为拥挤通常来自多个管理人持有相似小盘/低流动性/反转/残差动量组合。单一策略的 1% ADV 参与率看似安全，但如果行业同向去杠杆，真实冲击会远超自有参与率。

建议新增 `crowding_capacity` 层：

| 指标 | 计算建议 |
|---|---|
| 因子持仓重叠 | Top decile / bottom decile 与常见风格组合（小市值、低波动、高换手、反转、微盘）的重叠率。 |
| 拥挤交易方向 | 组合换手与因子收益、成交额变化、跌停压力的相关性。 |
| 左尾拥挤 | 因子组合收益的 skew、CVaR、最差 1% 日、跌停卖不出占比。 |
| 流动性共振 | 组合目标成交额 / 当日全市场成交额、行业成交额、市值分层成交额。 |
| 监管敏感 | 开盘/收盘集中成交占比、异常大额成交、撤单和短时冲击代理。 |
| 风格去杠杆压力 | 小盘相对大盘、IC/IM futures basis、融资余额变化、融券/转融通可得性。 |

### 4.7 Benchmark 和 holdout 治理仍需加强

规划已经要求 benchmark 审计，这很好。但还需强调：

- `CN_A_ALL_EQW_PROXY` 和 `CN_A_ALL_MV_WEIGHTED_PROXY` 是研究代理，不是可投资指数。
- 内部代理的 `coverage_assets` 和构成股票池必须与研究 universe 分离，避免“用同一批可交易股票生成 benchmark 又验证策略超额”的内生性。
- 最后 12 个月 holdout 会随着多轮审计和多次实验被“心理污染”。建议建立 `holdout_access_log`：每次读取、每次报告、每次决策都记录；如果 holdout 已被多轮使用，则转为 `readonly benchmark`，未来实盘前需要新增 forward OOS 或 shadow period。

### 4.8 S1 hard gate 过度依赖 IC，需强化可执行组合收益

RankIC 是很好的研究指标，但 A 股可执行性中，IC 与组合收益常被以下因素打断：

- 涨停买不到、跌停卖不出。
- 因子在低流动性股票有效但容量不可用。
- IC 来自大量小权重股票，而组合权重受市值/行业/容量约束。
- 预测排序正确但换手成本吞噬。
- 因子收益左尾巨大，均值 IC 看不出来。

建议把 S1 hard gate 改成“双主门槛”：

1. **统计 alpha 门槛**：HAC RankIC 或 bootstrap 通过。
2. **可执行 PnL 门槛**：成本后、容量后、订单失败后、benchmark 后超额为正，且 tail risk 不出现 fatal。

当前文档已经要求成本后超额为正，但建议把“可执行 PnL”从报告项提升为与 IC 同等地位的主指标。

### 4.9 多重检验的 family 定义不足

文档规定候选因子 >20 时做 FDR，这还不够。真实 data snooping 不只来自因子数量，还来自：

- 同一因子的窗口长度。
- 标签 horizon。
- 中性化方式。
- winsorize 分位。
- 行业分类标准。
- 模型家族。
- 特征选择。
- 资金档和成本版本。
- regime 切片。

建议在实验台账中新增 `test_family_id`、`hypothesis_family`、`num_trials_in_family`、`selection_path`。FDR 和 PBO 的分母应覆盖同一研究主题下所有变体，不只覆盖最终展示的因子名。

---

## 5. Concept shift 专项审计与重构建议

### 5.1 现有方案的裁决

现有方案裁决为：**方向正确，但不充分**。

正确之处：

- 废弃同一步模型切换、dynamic alpha、在线 Track B，避免 OOT 标签反馈泄漏。
- 要求成熟 IC 才能进入状态机。
- 指数衰减半衰期预注册，禁止用 OOT/holdout 择优。
- Chow/ADWIN/BOCPD 只作为报告，不作为“确认 concept shift”的硬证据。

不足之处：

- 没有把已知制度断点纳入模型候选选择协议。
- 没有 date-balanced weighting，近期大股票池可能被双重加权。
- 没有对“壳价值消退 / 小盘拥挤 / 程序化监管 / 退市加速”分别建模。
- 没有定义拥挤风险指标和容量联动。
- 告警只冻结 keep，不定义经过验证后的降仓、熔断、风格降权逻辑。
- 结构性变化切片只是描述性报告，不阻塞生产准入。

### 5.2 建议的重构框架：Concept Shift Resilience Protocol

建议新增一章或把 9.1.5 扩展为 **Concept Shift Resilience Protocol（CSRP）**。核心是不使用当前 OOT 标签，但允许在预注册和嵌套训练内处理结构性变化。

#### A. 结构性 regime map

先把已知机制变化写成固定日历，不作为事后择优：

| Regime | 日期建议 | 机制含义 | 必做分析 |
|---|---|---|---|
| 科创板注册制后 | 2019-07 起 | 新股定价、涨跌幅、科技板块估值结构变化 | 科创板/非科创板对比。 |
| 创业板注册制后 | 2020-08 起 | 创业板涨跌幅和新股制度变化 | 创业板/主板对比。 |
| 北交所扩容期 | 2021-11 起 | 小微企业与流动性结构变化 | 北交所单独处理，不混入普通 A 股容量结论。 |
| 全面注册制 | 2023-02-17 起 | IPO 供给、壳价值、上市标准和审核机制变化 | 小市值、次新、壳股、低质量因子分段。 |
| 2024 量化踩踏期 | 2024-01 至 2024-03，可细化 2024-02 | 小盘拥挤、流动性尾部、监管关注 | 小盘因子左尾、跌停卖不出、解锁反转。 |
| 新国九条后 | 2024-04-12 起 | 退市、分红、上市公司质量、交易监管强化 | ST/低质量/高股息/壳价值分段。 |
| 程序化交易强监管 | 2024-10-08 及 2025-07-07 起 | 程序化报告、高频监管、异常交易约束 | 高换手、开盘集中、低流动性策略容量压测。 |

#### B. 日期均衡 + 时间衰减样本权重

把当前 `weight = 2 ** (-age / half_life)` 改为两层权重：

```text
date_weight_t = 2 ** (-age_trading_days_t / (half_life_months * 21))
row_weight_{i,t} = date_weight_t / n_assets_t
normalize row_weight within each training step to mean 1
```

或至少预注册两个对照：

- `row_equal_decay`：当前行级指数衰减。
- `date_balanced_decay`：每日权重相同，再分配到当日股票。

正式结论必须报告二者差异。若策略只有在 `row_equal_decay` 下有效，可能只是利用了近年上市证券数增加和小微盘扩容。

#### C. 多窗口候选必须嵌套选择

建议在 S1.5 中加入候选训练窗口，但只能在 nested training 内选择：

| 候选 | 目的 | 选择规则 |
|---|---|---|
| 5Y equal-weight | 控制组 | 必跑。 |
| 5Y 12m decay | 当前默认 | 必跑。 |
| 5Y 18m decay | 预注册敏感性 | 必跑。 |
| 3Y equal/decay | 机制变化更快时的候选 | 只能在每步训练内部 nested CV 选择。 |
| anchored post-2023 | 只用于诊断，不直接 keep | 用于回答全面注册制后是否完全不同。 |
| invariant core factor model | 只保留跨 regime 同号因子 | 生产候选优先。 |

不建议直接恢复双轨 Track A/B。可以做“多候选模型库”，但每个 step 的选择必须只由该 step 训练窗口内部的 nested prequential validation 决定，并落盘选择路径。

#### D. 从“IC 告警”扩展为“结构性风险面板”

至少增加五类监控：

1. **成熟 IC / 因子收益**：已有。
2. **特征分布漂移**：PSI、MMD、KS，使用预测前可得特征。
3. **条件收益漂移**：分市值、行业、流动性、上市年龄、ST 风险、涨跌停压力的 IC 和 PnL。
4. **拥挤度**：组合与常见拥挤因子暴露重叠、换手相关、左尾 CVaR、跌停未成交。
5. **执行/监管压力**：开盘成交集中、订单规模、短时间成交额占比、未来程序化监管阈值敏感性。

#### E. 生产前允许风险响应，但必须先验证

S1/S1.5 阶段仍不得用告警改变当前 step 模型。但进入 S3/生产前，应允许预注册风险响应：

- 暂停新增 keep。
- 降低小市值 / 低流动性 / 高拥挤分组权重。
- 降低目标换手。
- 提高 ADV 门槛。
- 增加现金或指数期货对冲。
- 触发 shadow-only 或 live-small 降级。

这些响应必须在完整 walk-forward 中作为 **风险开关策略** 独立验证，不能由人工主观覆盖。

### 5.3 Concept shift 通过门槛建议

建议新增“生产准入门槛”，不同于 S1 alpha 门槛：

| 门槛 | 建议 |
|---|---|
| 结构性分段 | 全面注册制后、新国九条后、2024 量化冲击后至少不出现不可解释的持续负 alpha。 |
| 左尾改善 | 指数衰减或风险开关相对 5Y equal control 的 MaxDD/CVaR/跌停卖不出暴露改善。 |
| 非 shift 期不恶化 | 非压力期收益、换手、成本不出现显著恶化。 |
| 因子方向稳定 | 核心因子在至少 2/3 预注册 regime 中同号，或反号 regime 有明确禁用规则。 |
| 拥挤容量 | 在 1000 万和 5000 万档通过；1 亿档若失败需给出真实容量上限。 |
| 选择路径可复现 | 每个 step 的训练截止、标签截止、权重、模型版本、选择规则和预测文件可重放。 |

---

## 6. 数据改进建议

### 6.1 P0：不做这些，S1 结论可信度不足

| 数据/产物 | 原因 | 具体建议 |
|---|---|---|
| `warehouse_build_manifest` | 文档行数和 source status 不一致。 | 每次构建输出 manifest，策略报告只引用 manifest hash。 |
| `universe_daily_construction_audit` | 默认股票池是策略证据入口。 | 必须审计是否使用未来当前列表、当前 ST、当前停牌和退市推断。 |
| 公司行为与复权审计 | 标签和绩效依赖 adjusted returns。 | 接入分红、送转、配股、除权除息事件，至少用于复权因子验证。 |
| 沪/北 ST 历史事件 | 当前风险警示覆盖偏深市。 | 接入交易所简称变更、风险警示公告、摘帽摘星日期。 |
| 完整官方停复牌事件 | 推断停牌不能替代公告。 | 从交易所公告、巨潮或授权源补历史事件；短期至少校验 2023+。 |
| Historical PIT index membership | 指数增强、风格归因、benchmark 审计必需。 | 中证指数历史成分/权重、调样公告、可得日。 |
| 成本模型源分层 | 成本中佣金、滑点、冲击仍是研究假设。 | 区分交易所费率、券商佣金、交易税费、模型滑点、真实回报滑点。 |

### 6.2 P1/P1.5：为了 concept shift 和拥挤度必须提前

| 数据源 | 价值 | 建议优先级 |
|---|---|---|
| 融资融券明细 | 杠杆资金、拥挤、做空/融券可得性。 | P1 candidate。 |
| 北向资金 | 大盘/行业资金流、风格切换和政策交易。 | P1 candidate。 |
| ETF 申赎与宽基 ETF 资金流 | 2023-2025 A 股被动资金和政策资金影响大。 | P1.5。 |
| 股指期货 IF/IC/IH/IM 基差、持仓、成交 | 对冲成本、风格去杠杆、小盘拥挤。 | P1.5。 |
| 限售解禁 | 供给压力、注册制后流通冲击。 | P1 candidate。 |
| 大宗交易、龙虎榜 | 情绪、流动性和事件风险。 | P2/P3。 |
| 市场宽度、涨跌停宽度、跌停压力 | 风险开关和拥挤踩踏监控。 | P1.5。 |
| 分钟/集合竞价数据 | 开盘冲击和 limit-lock 可成交性。 | P2，服务执行先于 alpha。 |

### 6.3 P2：基本面增强和解释性

财报、业绩预告、业绩快报、股东户数、质押、分析师预期修正应在 P2 接入。它们可能提供更抗拥挤的基本面 alpha，但必须以公告日和可得日为核心，不得用当前快照回填历史。

---

## 7. 模型与机器学习建议

### 7.1 样本构造

- 对横截面模型，优先使用 **date-balanced objective**，避免近年股票数量更多导致训练目标偏向近年。
- 对 Ranker，必须以 `trade_date` 为 group/query，不允许跨日期混排。
- 对分类 top-quantile 标签，必须控制同日正负样本比例，避免年份和股票数变化改变类别先验。
- 对回归标签，建议同时测试：
  - benchmark excess return；
  - 行业/市值/beta 中性 residual return；
  - rank return。
- 若目标是可执行收益，最终模型选择应以组合 PnL、RankIC 和尾部风险共同决定，不只看 AUC 或 IC。

### 7.2 因子工程

- 原始单因子、等权、ICIR 必须保留，这是正确的。
- 正交化建议只作为复合模型对照，不替代原始因子证据，这也正确。
- 建议新增“跨 regime 同号因子”标签：若因子在全面注册制后或 2024 量化冲击后反号，应默认降级为 exploratory，除非有明确机制解释。
- 对风格因子要显式区分：小市值 alpha、壳价值 alpha、低流动性 alpha、反转 alpha、波动率 alpha、质量/分红 alpha。不要把所有有效性都归到模型。

### 7.3 模型路线

当前顺序“单因子 → 等权 → ICIR → 正交化 → Ridge/ElasticNet → LightGBM/XGBoost → Ranker → 深度模型”合理。建议补充：

- LightGBM/XGBoost 的 `sample_weight` 要有 date-balanced 版本。
- `best_iteration` 不能由 OOT 或 holdout 选；early stopping 只能使用训练窗口内 nested validation。
- SHAP/feature importance 必须按年度和 regime 报告稳定性，不能只报全样本平均。
- 对复杂模型新增“复杂度惩罚”：只有在相同成本、容量、PIT、OOT 下稳定击败线性/ICIR 基线，才允许 keep。
- 深度模型只作为 P4 对照是正确的；在 A 股日频横截面 alpha 中，深度模型最大的风险是把市场状态、股票池扩张、流动性和数据缺口编码成伪 alpha。

---

## 8. 验证和过拟合审计建议

### 8.1 Walk-forward 日历

文档已经要求实际交易日历生成 OOT 总步数，且 24 步只是最低门槛。建议进一步固化为产物：

```text
walk_forward_calendar_v1.parquet
columns:
step_id
prediction_start_date
prediction_end_date
train_start_date
train_end_date
label_horizon
purge_days
embargo_days
label_maturity_date
model_refit_flag
frozen_model_version
holdout_flag
```

每个模型预测文件必须引用 `step_id` 和 `walk_forward_calendar_hash`。

### 8.2 Holdout 使用治理

最后 12 个月 holdout 不能在多轮实验中反复“看结果后调整文档”。建议新增：

- `holdout_access_log.tsv`
- `holdout_decision_count`
- `holdout_burned_flag`
- 若 holdout 已被多次用于策略选择，则后续必须新增 forward OOS / shadow period 才能生产。

### 8.3 FDR/PBO 的测试族

建议把 FDR 从“候选因子数 > 20”扩展为“同一研究假设族的所有尝试”。新增字段：

```text
hypothesis_family_id
trial_index_in_family
total_trials_in_family
selection_path
pre_registered_or_exploratory
```

### 8.4 Stress slice 不得变成优化窗口

注册制阶段、2024-02 踩踏、流动性枯竭、政策反弹等压力段必须预注册。其用途是诊断和风控，不是选择最优窗口。正式报告应同时给出全期、非压力期、压力期，并说明若压力期失败是否触发降级。

---

## 9. 回测、执行和容量建议

### 9.1 订单状态机

文档已经要求涨停买不到、跌停卖不出、停牌延迟和连续锁死。建议把订单状态持久化为独立表：

```text
orders_audit:
run_id
step_id
asset_id
trade_date
target_weight
current_weight
intended_order_value
side
execution_price_rule
blocked_reason
filled_value
unfilled_value
delay_days
limit_lock_chain_length
unlock_date
post_unlock_return_1d/3d/5d
```

这样才能区分“模型没有 alpha”和“alpha 在成交层消失”。

### 9.2 开盘执行

日频阶段可先用未复权 `open` + ADV + 参与率做 L1 模型，但要显式保守：

- 开盘价并不代表任意资金规模都可成交。
- 开盘集合竞价和开盘后连续竞价的可成交量不同。
- 对小盘和涨跌停压力日，应额外增加失败率和滑点。
- 若未来进入分钟/涨停事件策略，必须用分钟或集合竞价数据重建执行，不能沿用 L1。

### 9.3 对冲和风险

若目标是“较高收益 + 低风险”，仅做 long-only 多因子可能不够。建议加入可选风险预算层：

- Long-only alpha + CSI futures beta hedge。
- 市值/行业/beta 中性组合。
- 不同资金档下的 hedge cost、futures basis、保证金和滚动成本。
- IF/IC/IM 对冲匹配误差。
- 极端行情下 futures basis 扩大和限仓影响。

这部分需要股指期货数据，不应在无数据情况下承诺市场中性收益。

---

## 10. 对两份策略文档的逐项修订建议

### 10.1 `quant_strategy_plan.md`

建议改动：

1. 在“独立评估结论”中增加一句：
   **“Concept shift 不仅作为报告诊断；生产准入前必须通过结构性 regime 稳健性和拥挤容量审计。”**

2. 在“模型路线”中将样本权重公式改为双口径：
   - `row_equal_decay` 保留当前公式；
   - `date_balanced_decay` 作为必须对照，正式结论需说明采用何者及原因。

3. 在“策略优先级”中新增 P1.5：
   **结构性变迁稳健性协议 CSRP：全面注册制、新国九条、2024 量化踩踏、程序化交易监管四类 regime 的强制验证。**

4. 在“AkShare 外部数据裁决”中把 `融资融券明细`、`北向资金`、`限售解禁`、`ETF flows` 和 `股指期货 basis` 提前到 concept shift/crowding 数据源，而不是普通 P2/P3 alpha 源。

5. 在“禁止事项”中新增：
   - 禁止把 stress slice 作为选模窗口。
   - 禁止用行级样本数量扩张造成的近期股票数偏差冒充 concept shift 适配。
   - 禁止只用自有参与率判断拥挤容量。

### 10.2 `quant_strategy_research_plan_detailed.md`

建议改动：

1. 第 3.1 默认股票池拆成三层 universe：`research_observable_universe`、`entry_eligible_universe`、`execution_accounting_universe`。
2. 第 6.1.5 增加 date-balanced sample weight，并要求报告有效样本量、日期权重分布、每期股票数权重贡献。
3. 第 7.1 增加 `walk_forward_calendar_v1` 固化字段。
4. 第 7.3 过拟合审计增加 `hypothesis_family_id` 与完整尝试次数。
5. 第 9.1 hard gate 改为“双主门槛”：统计 IC + 可执行 PnL。
6. 第 9.1.5 改名为 `S1.5 Concept Shift Resilience`，并增加结构性 regime map、拥挤容量、date-balanced 权重和嵌套多窗口候选。
7. 第 10 外部数据 schema 中新增：
   - `fund_flows/etf_flow_daily`
   - `index_futures/basis_oi_daily`
   - `market_breadth/breadth_limit_pressure_daily`
   - `margin_trading/equity_margin_detail_daily` 提前到 P1 candidate
8. 第 11 实验台账新增：
   - `walk_forward_calendar_hash`
   - `warehouse_build_manifest_hash`
   - `hypothesis_family_id`
   - `test_family_size`
   - `date_weighting_scheme`
   - `crowding_risk_score`
   - `limit_lock_cvar`
   - `holdout_access_count`

---

## 11. 建议的近期落地路线

### Step 0：先做文档与 manifest 修复

- 统一 reference rates、Shibor、行数、source status。
- 输出 `warehouse_build_manifest.json`。
- 更新 `external_data_sources.csv` 优先级。
- 将策略文档中的表行数改为“引用 manifest”。

### Step 1：S1 启动前 P0 审计

- `universe_daily_construction_audit`
- `walk_forward_calendar_v1`
- `validation_params_hash`
- `benchmark_audit`
- `pit_factor_audit`
- `valuation_gap_sensitivity`
- `ADV_new_listing_flags`
- `corporate_action_adjustment_sanity_check`

### Step 2：市场-only 强基线

先不混入高风险财报派生字段：

- 市值、流动性、动量、反转、波动率、beta、行业中性。
- 单因子、等权、ICIR、正交化、Ridge/ElasticNet、LightGBM/Ranker。
- 三层 universe 对照。
- 可执行组合回测和容量报告。

### Step 3：Concept Shift Resilience

在 S1 结果基础上跑：

- 5Y equal control。
- 5Y 12m/18m decay。
- row-equal vs date-balanced decay。
- 结构性 regime 分段。
- 拥挤容量面板。
- 小盘/低流动性/涨跌停压力/2024-02 stress。
- S3 风险开关候选，但不使用当前 OOT 标签动态切换。

### Step 4：外部数据候选 ETL

优先级：

1. 公司行为 / 除权除息 / 分红送配。
2. 融资融券、北向资金、限售解禁。
3. ETF flows、股指期货 basis/OI。
4. 财报披露和业绩预告。
5. 股东户数、质押、龙虎榜、大宗交易。
6. 新闻/NLP。

### Step 5：Shadow / paper / live-small

任何 keep 策略在真实部署前至少需要：

- 冻结参数和特征。
- 只读 forward OOS。
- shadow 订单不成交模拟。
- paper 或最小资金 live-small。
- 实盘成交回报与回测执行模型对齐。
- 风险 kill switch 和恢复条件。

---

## 12. 最终裁决

### 12.1 可立即执行

- P0 审计和 walk-forward 日历固化。
- 市场-only 日频强基线。
- 单因子和分层 IC。
- 可执行组合基线。
- 容量和成交失败报告。
- Concept shift 诊断面板。

### 12.2 可并行准备，但不能直接进入 keep

- 公司行为和 total return 校验。
- 融资融券、北向、限售解禁。
- 筹码 ETL。
- 分钟数据用于执行优化。
- 行业轮动和中性化。

### 12.3 暂不建议投入主力

- 深度时序作为 alpha 主线。
- NLP/新闻 alpha。
- 普通分钟 T+0 alpha。
- 期权策略。
- 未经 PIT 审计的筹码、涨停事件、分析师预期。

### 12.4 总体判断

这份规划已经具备“严肃量化研究体系”的雏形。它的最大价值不是某个模型或某个因子，而是强制把数据时点、成交约束、验证、防过拟合和审计产物写成流程。当前最需要修正的是：

1. 统一数据文档版本和 manifest。
2. 拆分研究 universe 与执行 universe。
3. 提升公司行为和复权审计优先级。
4. 将 concept shift 从诊断项升级为结构性稳健性协议。
5. 引入 date-balanced training weights 和拥挤容量模型。
6. 强化可执行 PnL 与尾部风险在 S1 中的主门槛地位。

完成这些修订后，计划会更贴近当前 A 股的数据现实、交易制度和未来实盘落地要求，也更有机会在不牺牲风险控制的前提下找到可持续 alpha。

---

## 13. 参考来源

### 附件和本地文档

- `quant_strategy_plan.md`
- `quant_strategy_research_plan_detailed.md`
- `DATA_USAGE_GUIDE.md`
- `WAREHOUSE_README.md`
- `external_data_sources.csv`
- `validation_params.json`

### 外部资料

[^csrc_reg]: 中国证监会，《全面实行股票发行注册制制度规则发布实施》，2023-02-17。https://www.csrc.gov.cn/csrc/c100028/c7123213/content.shtml

[^state_council_2024]: 国务院，《关于加强监管防范风险推动资本市场高质量发展的若干意见》，2024-04-12。https://www.csrc.gov.cn/csrc/c100028/c7473562/content.shtml

[^csrc_prog]: 中国证监会，《证券市场程序化交易管理规定（试行）》发布说明，2024-05-15。https://www.csrc.gov.cn/csrc/c100028/c7480577/content.shtml

[^xinhua_prog_2025]: 新华社，《沪深北交易所发布程序化交易管理实施细则》，2025-04-03。https://www.news.cn/fortune/20250403/33b74c7420fe4ec7b7c07963c311a917/c.html

[^gov_lingjun]: 中国政府网英文版，《China's securities regulator pledges improved supervision standards, malpractice crackdown》，2024-02-23。https://english.www.gov.cn/news/202402/23/content_WS65d7d7ebc6d0868f4e8e441c.html

[^reuters_lingjun]: Reuters, “China restricts quant fund Lingjun in effort to boost market”, 2024-02-20/21。https://www.reuters.com/markets/asia/shenzhen-exchange-punishes-hedge-fund-lingjun-investment-abnormal-trading-2024-02-20/

[^reuters_quant_quake]: Reuters, “China's ‘quant’ funds conform as regulators crack down after crash”, 2024-03-15。https://www.reuters.com/world/china/chinas-quant-funds-conform-regulators-crack-down-after-crash-2024-03-15/

[^reuters_quant_losses]: Reuters, “China's quant funds suffer deep losses amid crackdown”, 2024-07-24。https://www.reuters.com/business/finance/chinas-quant-funds-suffer-deep-losses-amid-crackdown-2024-07-24/
