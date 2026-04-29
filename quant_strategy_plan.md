# A股量化策略研究与落地总纲（2026-04-30 版）

> 本文件是后续策略研究的短总纲。详细执行规则以 `quant_strategy_research_plan_detailed.md` 为准。  
> Canonical 数据源：`D:\data\warehouse`。旧 `processed`、旧 qant cache、旧随机验证结果只能作为历史对照或反例，不作为策略有效性证据。
> 2026-04-30 已吸收 `三方审计报告_20260430.md`、`consensus_audit_report_20260430.md`、`consensus_audit_round2.md`、`consensus_audit_r3.md`、`consensus_audit_r4.md` 和 `consensus_audit_r5.md`：采纳其对执行可成交性、因子 PIT、walk-forward 固化、过拟合审计、S1 执行分层、IC 显著性修正、股票池审计、数据缺口处理和 concept shift 诊断的核心批评；R5 后废弃双轨、动态 alpha 和在线 Track B 作为近期执行路径，改为单轨指数衰减候选与数据驱动告警；不采纳未经本地验证的收益承诺。

---

## 1. 当前证据状态

### 1.1 已经可用的数据底座

`D:\data\warehouse` 已完成重构、六轮修正和 P1 数据前置。最近一次检查：

- `D:\data\warehouse\audit_reports\leakage_check_report.json`
- `checked_at=2026-04-29 10:38:49`
- 15 类目录全部 PASS

当前可直接用于日频股票研究的核心表：

| 表 | 规模和范围 | 主要用途 |
|---|---:|---|
| `prices_daily_unadjusted` | 17,599,789 行，1990-12-19 至 2026-04-27 | 未复权成交价、成交额、涨跌停和容量判断 |
| `prices_daily_returns` | 17,599,789 行 | `return_adjusted_pit` 用于收益、动量、标签和绩效 |
| `valuation_daily` | 16,642,794 行，2000-01-04 至 2026-04-27 | 市值、估值、股本、换手率 |
| `tradability_daily_enriched` | 18,177,689 行 | 停牌推断、涨跌停约束、上市年龄、风险警示 |
| `universe_daily` | 18,177,689 行，默认因子 universe 16,586,748 行 | 第一版研究股票池 |
| `benchmarks` | 31,229 行 | 全 A 代理、沪深300、中证500、中证1000 |
| `reference_rates` | 55,964 行 | 国债收益率、Shibor、固定 fallback |
| `industry_classification` | PIT 行业区间 53,925 行 | PIT 行业中性和行业轮动候选 |
| `risk_warning_daily` | 8,973,264 行 | 风险警示过滤，深市历史较完整 |
| `trading_costs` | 23 行 | 印花税、佣金、过户费、规费、滑点研究假设 |

这些表足够启动第一批日频股票研究：因子 IC、分层收益、保守组合回测、容量压力测试、风险状态和 PIT 行业研究。

### 1.2 必须披露的数据缺口

以下缺口不阻塞第一批日频研究，但必须写入每份回测报告：

- 完整交易所官方停复牌公告库仍缺失；`is_suspended_inferred=True` 是工程推断，不是官方公告。
- 沪/北历史 ST、摘帽、摘星带日期源仍缺；`risk_warning_daily` 主要来自深交所简称变更。
- `valuation_daily` 与收益表 key 不完全一致，2026-01-05 至 2026-02-05 存在估值覆盖缺口。
- `index_membership` 只是当前成分和最新月末权重快照，不能倒灌为历史 PIT 指数成分。
- `exchange_calendar` 是 SH/SZ/BJ 统一 A 股交易日历代理，不是三所官方历史差异日历。
- 成本模型中佣金、滑点、冲击成本和部分规费仍含研究假设。
- `chip_daily`、`limit_events`、`prices_minute`、`option_minute`、`features`、`labels` 当前仍未形成可审计入仓主表。

### 1.3 qant 实验结论的使用方式

此前 qant warehouse 实验只能作为边界证据：

- 2019-2026 chronological baseline：总收益 `-8.78%`，Sharpe `0.011`，最大回撤 `-60.65%`，相对中证1000总超额 `-51.54%`。
- random 8/2 曾显示总收益 `+531.43%`，Sharpe `0.988`，但已被 deep dive 判定为 label 泄漏和验证污染下的乐观结果。
- 证据：1,629,101 行训练窗口样本 `target_date_10d` 跨入 OOT 月，random 原始切分中 1,330,446 行进入 train。
- 2022-2024 修正实验中，所有 OOT purge 后版本绝对收益均为负。

因此，后续不得把 `outputs\warehouse_qant_2019_2026_random_val` 当作稳健基线，也不得用 naive random split 结果决定策略优先级。

### 1.4 三方审计后的独立裁决

`三方审计报告_20260430.md` 给早期计划的共识评分为 `6.0-6.5/10`。随后 `consensus_audit_report_20260430.md` 完成 Round 4 参数对齐，`consensus_audit_round2.md` 进一步细化执行层规则，`consensus_audit_r3.md` 补充因子正交化、股票池构造审计、A 股制度风险、Newey-West 显著性修正和 IC 衰减监控，`consensus_audit_r4.md` 聚焦仓库数据对接、估值缺口、真实 walk-forward 步数和 concept shift 替代训练框架，`consensus_audit_r5.md` 进一步复审双轨制可行性并将近期执行口径收敛为单轨指数衰减候选；当前执行口径以两份活跃策略文档和 `validation_params.json` 吸收后的表述为准。

| 审计意见 | 裁决 | 写入方式 |
|---|---|---|
| 涨跌停执行风险是 P0 | 采纳 | 任何组合回测必须报告涨停禁买、跌停禁卖、连续锁死和反转统计；纸面 alpha 若无法成交则不计为有效 alpha。 |
| 开盘冲击三段模型是 P0 | 部分采纳 | 日频阶段先用 open/amount/participation 做保守冲击和容量惩罚；集合竞价和分钟三段模型需等 `prices_minute`/竞价表入仓后升级。 |
| 因子 PIT 合规是 P0 | 采纳 | 市值/估值/行业/风险警示均需通过实验层 PIT audit；warehouse leakage PASS 不能替代因子层审计。 |
| walk-forward 参数固化 | 采纳并升级 | 官方证据默认 5 年训练、21 个交易日调仓、`purge_days >= max(horizon*3,40)`、embargo 10、至少 24 个 OOT step，并做分年度/市场状态分析。 |
| Deflated Sharpe 和 holdout 默认化 | 采纳 | 所有可 keep 的组合结果必须做过拟合审计和 holdout/稳定性复核。 |
| S1 完成标准量化 | 部分采纳并分层 | Newey-West HAC 调整后 `t>=1.65` 或 block bootstrap `p<0.10` 只是 S1 统计 hard gate；keep/晋级还必须通过 PIT/split/benchmark 审计、最后 12 个月 holdout、FDR、DSR/PBO、成本后超额和容量/成交约束。 |
| 分红送配从 P2 提到 P1.5 | 部分采纳 | 作为 Phase A 并行 ETL，不阻塞首轮价格/收益基线，但阻塞 total-return 和基本面增强结论。 |
| 风险开关 v1 | 采纳但去硬编码 | 放入 S1 通过后的强制风险模块；S3 前只使用 25/25/25/25 均匀权重占位，100/60/30/0 只能作为历史假设或挑战基线，不作为默认候选。 |
| 另类数据和筹码提前 | 部分采纳 | 北向、融资融券、限售解禁和筹码可提前做 source registration、ETL 和 candidate tracking；未通过 PIT/覆盖率/时点审计前不得进入官方 S1 keep。 |
| DeepSeek 收益路径和 alpha 区间 | 不作为承诺采纳 | 只能作为假设队列，所有收益区间必须由本地实验重新验证。 |
| 因子正交化流程 | 采纳但细化 | 单因子和等权基线保留原始因子；复合打分和线性模型前使用训练窗 ICIR 降序确定顺序，再做 Gram-Schmidt 正交化，并输出正交化前后相关矩阵。OOT 数据不得影响排序或处理参数。 |
| 季节性效应处理 | 采纳方案 B | 默认依靠 5 年训练窗口覆盖完整年度周期，不在 S1 默认加入月份哑变量；月份哑变量只能作为预注册 S3 或敏感性分析。 |
| Exploratory Tracking 冷却后处理 | 采纳 | 冷却期满后，如最近 6 个 OOT step 仍至少 4 步方向一致，可重新进入 S1 候选队列；不能直接进入 keep，且计入 `attempt_count`。 |
| `universe_daily` 构造审计 | 采纳 | 当前默认规则来自 `can_trade_close_based`、上市交易日龄和 PIT 风险警示，但 Step 1 必须补交股票池构造审计，确认未用当前股票列表或未来状态回填历史。 |
| A 股制度性风险对照 | 采纳为压力切片 | S1 报告增加涨跌停排除 IC 对比、注册制前后分段、流动性枯竭/拥挤压力日 IC 分析；这些切片用于诊断和风控，不得事后挑选窗口优化收益。 |
| IC 自相关和 bootstrap block | 采纳 | IC t-stat 默认使用 Newey-West HAC 调整；block bootstrap 默认 block=`max(label_horizon, rebalance_interval)`，并在 purge 敏感性中报告 10/21/40 日 block 对 p-value 的影响。 |
| IC 衰减半衰期 | 采纳为报告项 | S1 季度滚动 IC 报告增加半衰期，作为信号持久性风险提示，不作为 S1 hard gate。 |
| walk-forward 起始和总步数 | 采纳并精确化 | 24 步只是最低验收门槛，不是总步数；主窗口从 2005 开始，首个 OOT 约在 2010 年，实际步数按交易日和剔除最后 12 个月 holdout 后计算。 |
| 2026 估值缺口 forward-fill | 部分采纳 | 本地确认 2026-01-05 至 2026-02-05 缺 24 个交易日；只允许对慢变量估值特征做按股票有界 forward-fill，禁止用于标签、收益、成交价或绩效，并必须做有/无 forward-fill 敏感性。 |
| P1 因子可构建性 | 采纳但保留 PIT 缺口 | 9 类 P1 因子均可由现有表构建；沪/北 ST、全历史停复牌、估值缺口和 AkShare 行业源仍需在报告中披露。 |
| trailing ADV 和新股样本 | 采纳 | `tradability_daily_enriched.amount` 可用于 ADV；`listing_age_trading_days < 20` 标记为 ADV 不足，不得用新股异常成交额外推容量。 |
| 早期 benchmark 可靠性 | 采纳并校正事实 | benchmark 审计必须报告 `coverage_assets`；本地全 A 等权代理 1990 年仅 1-5 只，2005 年中位约 1315 只，2024 年中位约 5342 只。2005 前只做敏感性。 |
| R5 Concept Shift 训练替代方案 | 部分采纳并重构 | 采纳对双轨制、动态 alpha 和在线 Track B 的泄漏/过拟合风险批评，废弃这些近期执行路径；采纳单轨 5 年 rolling + 指数衰减 sample weight 作为预注册候选，并强制保留等权 5 年基线对照。不采纳“人工审查”，改为成熟 OOT IC/因子收益驱动的 yellow/red 状态机；任何告警不得改变当前 step 模型、alpha、阈值或特征选择。 |

---

## 2. 独立评估结论

当前最优先的工作不是追求新模型或高收益叙事，而是建立强基线和严格验证体系。

可立即推进的主线：

1. 日频多因子基线：估值、市值、流动性、动量、反转、波动率。
2. 保守可交易回测：T+1、涨跌停、停牌、ST、上市年龄、交易成本、容量。
3. 市场状态和风险开关：指数趋势、市场宽度、波动率、涨跌停压力。
4. PIT 行业中性和行业轮动：只使用 `pit_industry_intervals_akshare`，固定分类标准。
5. qant 小盘模型重审：只用 corrected baseline、OOT purge、blocked validation 和 embargo。
6. 外部数据候选 ETL：北向、融资融券、限售解禁、筹码只做可审计入仓准备和 exploratory tracking，不直接作为官方 alpha 结论。

暂不作为第一批核心 alpha 的方向：

- 筹码增强：原始数据有价值，但尚未形成可审计 warehouse 主表，先做 P1/P1.5 并行 ETL、source registration 和 PIT 可用性审计，alpha 结论后置。
- 涨停事件：需先将事件表入仓，并严格区分盘后策略和盘中打板。
- 分钟策略：优先服务执行和滑点建模，不承诺普通 A 股 T+0 alpha。
- 期权策略：数据期短且缺 bid/ask、保证金、盘口深度和真实成交概率，先做研究储备。
- 深度时序、NLP、RL：必须在强基线和 walk-forward 体系稳定后作为增强模型进入。

---

## 3. 策略优先级

| 优先级 | 方向 | 进入条件 | 主要目标 | 当前裁决 |
|---|---|---|---|---|
| P0 | 实验层 PIT/label/validation audit | 策略证据输出前必须通过 | 防止 warehouse PASS 后在实验层重新引入泄漏 | 立即固化 |
| P0 | 涨跌停和开盘执行门槛 | 任何组合回测前必须纳入 | 过滤纸面可得但真实不可成交的 alpha | 立即固化 |
| P1 | 日频多因子强基线 | P0 audit 通过 | 证明 warehouse 下可交易超额是否存在 | 立即启动，使用 Round 5 验证参数 |
| P1 | 基础容量压力测试 | P0 成交规则可运行 | 用 trailing ADV、参与率、成交失败和市值分档量化真实成交边界 | 随 S1 同步输出 |
| P1 | Concept Shift 诊断 | S1 walk-forward 同步运行 | 检测 2023-2025 结构变化、因子拥挤和分布漂移是否破坏基线稳定性 | 不直接作为收益结论 |
| P1.5 | R5 衰减权重稳健性 | 单轨强基线已可运行 | 对比等权 5 年、12 月半衰期指数衰减和预注册 18 月敏感性是否改善结构变化期稳定性 | 数据驱动候选，不使用 OOT/holdout 择优 |
| P1 | 候选另类数据 ETL | source/available_at 先行 | 北向、融资融券、限售解禁只进入 candidate tracking | 不阻塞传统因子 S1 |
| P1.5 | 风险状态和仓位开关 v1 | S1 有正向证据后 | 降低回撤和波动 | S1 通过后强制验证 |
| P1.5 | 筹码 ETL 和 PIT 审计 | source/算法/available_at 先行 | 判断旧筹码数据能否进入 canonical warehouse | 不先作为 alpha 结论 |
| P1.5 | 公司行为/分红送配 ETL | source/available_at 先行 | total-return 和基本面 PIT 校验 | Phase A 并行准备 |
| P2 | PIT 行业中性和行业轮动 | 固定分类标准并验证覆盖 | 约束暴露、研究行业动量和拥挤 | 基线后启动 |
| P2 | qant 小盘模型重审 | 必须 purge/embargo | 判断旧 132 特征是否有可救增量 | 作为反例驱动重审 |
| P2 | AkShare 低频外部数据 | schema、available_at、质量检查先行 | 财务、公司行为、融资融券、解禁等增强 | 单独 ETL 阶段 |
| P3 | 筹码 alpha | `chip_daily` 入仓并验证时点 | A 股特色增量 alpha | ETL/PIT 审计通过后研究 |
| P3 | 涨停事件卫星 | `limit_events` 入仓并验证成交 | 小仓位事件策略 | ETL 后研究 |
| P3 | 分钟执行优化 | 5min/1min 分区表可用 | VWAP、滑点、冲击成本 | 服务执行，不先做 alpha |
| P4 | 期权波动率和保护性对冲 | 期权链、IV、Greeks、流动性模型完成 | 风险对冲和研究储备 | 后置 |
| P4 | 深度时序、NLP、RL | 线性/GBDT/Ranker 基线通过 | 增强预测或执行 | 严格准入 |

---

## 4. 模型路线

采用“模型输出分数，组合和风控决定仓位”的路线。

### 4.1 第一阶段模型

- 单因子和等权打分。
- ICIR 加权打分。
- 训练窗 ICIR 排序后的 Gram-Schmidt 正交化复合打分。
- Ridge、ElasticNet、线性横截面回归。
- LightGBM、XGBoost。
- LightGBM Ranker 或 LambdaRank，用于 Top-N 排序。

第一阶段目标是形成强基线，而不是调参追高收益。

Concept shift 处理采用“单轨强基线 + 预注册训练权重 + 数据驱动告警”：

- 单轨 5 年 rolling walk-forward 仍是 S1 主证据框架；不再使用 Track A/B、动态 alpha 或在线 Track B 作为近期候选。
- 等权 5 年 rolling 是必须保留的对照基线，R5 指数衰减加权是单轨训练权重候选。
- 指数衰减默认半衰期为 12 个月，公式为 `weight = 2 ** (-age_trading_days / (half_life_months * 21))`，每个训练 step 内归一化到均值 1。
- 18 个月半衰期只作预注册敏感性；6/24/36 个月只能作为研究项，不能用 OOT 或 holdout 择优。
- 模型默认每 63 个交易日重训一次，21 个交易日调仓/预测；两次重训之间使用最近一次符合 purge 规则的冻结模型版本。
- Concept shift 告警只使用已成熟 OOT IC、因子收益或预测前已可得的分布/拥挤度指标；连续 6 步成熟 IC < 0 触发 red quarantine，最近 6 步中至少 4 步为负触发 yellow。告警不改变当前 step 模型、alpha、阈值、early stopping 或特征选择。

### 4.2 第二阶段模型

在第一阶段通过后再评估：

- CatBoost：用于类别特征和稳健树模型对照。
- GARCH/HAR-RV：用于波动率和风险状态。
- 轻量 LSTM 或 1D-CNN：仅作为 P4 对照，不早于强基线和审计框架稳定后进入。
- TFT、N-HiTS、PatchTST、iTransformer、AutoGluon-TimeSeries、Darts、NeuralForecast：本地路线降级为研究储备或云端实验，不作为近期执行计划。

当前本机已可用：`lightgbm`、`xgboost`、`qlib`、`cvxpy`、`torch`。  
当前尚未安装或未验证：`arch`、`vectorbt`、`riskfolio-lib`、`PyPortfolioOpt`、`catboost`、`darts`、`neuralforecast`。这些依赖应在对应阶段进入前再安装和验证。

---

## 5. AkShare 外部数据裁决

本轮不做大规模外部数据接入。理由：

1. 当前 warehouse 已足够支撑第一批核心日频研究。
2. 外部数据必须先定义 schema、`available_at`、质量检查和回滚策略。
3. 贸然把半审计外部表混入 warehouse，会降低刚完成的数据底座可信度。

已确认 AkShare 1.18.57 可提供以下候选数据：

| 排名 | 数据源 | 价值 | 裁决 |
|---:|---|---|---|
| 1 | 公司行为、分红、送配 | total return、分红因子、复权校验 | P1.5 并行最小 ETL |
| 2 | 财报、业绩预告、业绩快报 | 质量、成长、盈利修正 | P2 优先接入 |
| 3 | 融资融券明细 | 杠杆资金和拥挤度 | P1 candidate ETL，PIT 审计前不进 keep |
| 4 | 股东户数、质押、限售解禁 | 供给压力和风险过滤 | 限售解禁 P1 candidate ETL，其余 P2 |
| 5 | 分析师预期修正 | 预期变化和事件驱动 | P2 候选，需可审计历史源 |
| 6 | 北向资金 | 资金流状态 | P1 candidate ETL，PIT 审计前不进 keep |
| 7 | 龙虎榜、大宗交易 | 事件风险和情绪 | P3 接入 |
| 8 | 公告、新闻、NLP | 潜在高价值但稳定性低 | P4 研究 |

安全抓取原则：

- 全局 1 worker 起步。
- 慢接口串行，间隔 5-10 秒。
- 日频交易所接口整体不超过约 0.3 req/s。
- 失败指数退避重试 2-3 次。
- 所有中文参数用 UTF-8 脚本或 Unicode escape，避免 PowerShell 管道乱码。
- 所有披露类特征至少 T+1 生效，不得使用当前快照字段回填历史。

---


## 5.5 三方审计共识改进（2026-04-30）

三方独立审计（Main/Review/DeepSeek）达成以下共识，已写入执行规范：

### 验证框架参数调整（Round 5 + round2/r3/r4/r5 执行细化）
- **embargo**：5日 → **10日**（基于A股因子自相关实证数据）
- **purge**：max(horizon,20) → **max(horizon*3,40)**
- **训练窗口**：**5年**（保持）
- **训练权重**：R5 后新增单轨指数衰减候选；默认半衰期 12 个月，等权 5 年 rolling 必须作为对照，18 个月作为预注册敏感性，不得用 OOT/holdout 择优。
- **模型重训频率**：默认 63 个交易日重训，21 个交易日调仓/预测；非重训 step 使用最近一次冻结模型。
- **OOT steps**：最少**24步（每步21日）+ 分年度分析**（覆盖2年，40%训练/测试比）
- **walk-forward 起始和总步数**：主窗口从 2005-01-01 开始，首个 OOT 起点约为 2010 年；24 步只是最低验收门槛，实际总步数按交易日历和最后 12 个月 holdout 剔除后计算并披露。
- **S1门槛分层**：Hard Gate 包括审计通过、Newey-West HAC 调整后的 IC t-stat **≥1.65** 或 bootstrap p **<0.10**、最后 12 个月 holdout Sharpe > 0、成本后超额为正、基础容量和成交失败不触发 fatal；Soft Floor 包括换手、年度/市场状态稳定性和复杂模型相对简单基线增量；尾部风险和分层通过率先作为报告要求
- **IC显著性**：IC t-stat 默认使用 **Newey-West HAC** 调整；未调整 t-stat 只能作为诊断值。
- **bootstrap方法**：**Block Bootstrap, block=max(label_horizon, rebalance_interval)**，当前 20 日标签 + 21 日调仓默认 block=21 日，≥5000次重抽样；purge 敏感性中报告 10/21/40 日 block 对 p-value 的影响。
- **多重检验**：候选因子>20个时，必须报告FDR校正后的显著性；进入 keep/晋级时 FDR 为硬约束
- **尾部风险**：S1报告模板必须记录MaxDD/VaR/CVaR/Sortino/Calmar（不作为门槛，S2引入）
- **Exploratory Tracking机制**：方向一致性≥65%（OOT 24步中IC与对应样本内IC同号的步数/24，辅助：最近6步中4步一致） + 冷却期≥6个月（从首次进入Exploratory Tracking日起算） + 不入组合 + 完整记录；冷却期满后若最近6步仍至少4步方向一致，只能重新进入 S1 候选队列，不能直接 keep。
- **holdout定义**：最后12个月（约252个交易日）作为最终验收窗口，不参与调参、特征选择、early stopping、阈值选择或仓位开关选择；12 vs 18个月只在S2预实验中验证
- **Concept Shift 分层**：S1 保留 5 年 rolling 单轨强基线；R5 后废弃双轨自适应、在线 Track B 和动态 alpha 近期路径；concept shift 诊断随 S1 报告输出，并通过成熟 IC 驱动的 yellow/red 状态机进入 quarantine/revalidation，不放宽 hard gate。
- 若机器可读参数镜像与本节冲突，以本文档、`consensus_audit_report_20260430.md`、`consensus_audit_round2.md`、`consensus_audit_r3.md`、`consensus_audit_r4.md` 和 `consensus_audit_r5.md` 为准；执行前必须校验一致的参数 hash。

### 因子库扩展
- P1阶段同步做3-5个另类数据源的 source registration 和 candidate ETL（北向资金、融资融券、限售解禁优先）
- 筹码数据ETL从P3提前到P1/P1.5并行准备；PIT、覆盖率、算法解释和异常值审计通过前不进入官方 S1 keep

### 新增验证项
- 因子正交化流程：单因子、等权和原始 ICIR 先保留为基线；随后在 ICIR 复合和 Ridge/ElasticNet 前，用训练窗 ICIR 降序确定 Gram-Schmidt 顺序，并输出正交化前后相关矩阵。
- 多重检验校正（FDR，因子>20个时）
- 尾部风险指标（VaR 95%、CVaR 99%）
- regime断裂检测和保护：S1阶段使用20日滚动IC告警，先只作为报告/yellow标记/暂停跟踪候选；减仓或停用必须经walk-forward验证
- `universe_daily` 构造逻辑审计：确认默认股票池不使用未来股票列表、未来 ST、未来停牌或未来涨跌停状态筛历史。
- 季节性效应处理：默认依靠 5 年训练窗口覆盖完整年度周期；月份哑变量仅作预注册敏感性或 S3 研究。
- A 股制度性风险对照：涨跌停排除 IC、注册制阶段、流动性枯竭/拥挤压力日。
- 因子 IC 衰减半衰期：写入 S1 季度滚动 IC 报告，报告风险等级但不作为 hard gate。
- 估值缺口处理：2026-01-05 至 2026-02-05 估值缺口只允许慢变量特征有界 forward-fill，并做缺口 mask 和敏感性报告。
- concept shift 诊断：预注册 2023-2025 结构变化切片、滚动成熟 IC/因子收益、分布漂移和拥挤度监控；Chow/ADWIN/Page-Hinkley/BOCPD 只可作为成熟序列上的报告项，不作为 keep gate 或自动切换依据；诊断不放宽 S1 hard gate。

### 深度模型降级
- 放弃PatchTST/TFT，改用轻量LSTM或1D-CNN
- 或定位为云端实验，本地只做推理

### 容量测试前移
- S1阶段增加最简容量过滤（日均成交额>1000万）
- S1同步报告 trailing ADV、参与率、成交失败率、涨跌停压力和市值分档 IC；S2做精细容量分析（分档滑点/冲击/参与率）

### S1 启动前补充验证
- purge 敏感性：在相同因子和窗口下对比 40/60/80 个交易日 purge；该实验不阻塞面板构建，但阻塞正式 keep/晋级结论。
- R5 S1 前置条件：
  - P0：`universe_daily` 构造审计、walk-forward 日历固化、每步训练截止日满足 purge/embargo。
  - P1：valuation 缺口三口径敏感性、benchmark 覆盖审计、ADV 新股不足标记、validation 参数 hash。
  - P1：concept shift 诊断和成熟 IC yellow/red 状态机预注册，随 S1 输出但不放宽 hard gate。
  - 非阻塞 S1：ADWIN/BOCPD 等额外变点诊断、6/24/36 月半衰期研究网格；均不得进入 keep 决策。
- 24 步仅是最低验证规模和快速 smoke；完整 R5 主证据按交易日历生成全量 OOT step，需单独估算耗时。

详细共识报告见：consensus_audit_report_20260430.md
执行层补充审计见：consensus_audit_round2.md
第三轮执行深化见：consensus_audit_r3.md
第四轮数据和 concept shift 审计见：consensus_audit_r4.md
第五轮 concept shift 训练方案复审见：consensus_audit_r5.md

## 6. 禁止事项

后续所有实验禁止：

1. 使用全样本最新前复权价格作为历史训练特征或决策输入。
2. 使用未来股票列表、未来行业、未来 ST、未来停牌状态筛选历史样本。
3. 使用 naive random 8/2 作为最终验证证据。
4. 用 OOT 月内 future label 参与训练、验证或 early stopping。
5. 用当前指数成分或权重快照构造历史指数增强股票池。
6. 把缺 bar 推断停牌当作交易所官方停牌公告。
7. 把当前行业快照当作 PIT 历史行业。
8. 只报告毛收益，不报告成本、换手、成交失败和容量。
9. 在没有基线对照的情况下引入深度学习、NLP 或 RL。
10. 在文档中承诺未经实证的高收益、Sharpe 或胜率。
11. 把双轨 Track A/B、动态 alpha 或在线 Track B 作为 S1/S1.5 近期执行路径。
12. 让人工主观判断决定模型切换、参数选择、候选 keep 或告警处置；所有处置必须来自预注册数据规则。

---

## 7. 近期行动路线

### Phase A：日频强基线

目标：建立可复现、可审计的日频股票多因子基线。

产出：

- Round 5 固化的 walk-forward 参数、指数衰减权重参数和本地参数 hash。
- 实验层 PIT audit、split label audit、benchmark audit。
- `universe_daily` 构造审计报告。
- 2026 估值缺口 mask、forward-fill 敏感性和受影响样本报告。
- benchmark 覆盖股票数审计，2005 前 benchmark 仅作敏感性说明。
- 涨跌停禁买/跌停禁卖、连续锁死、开盘冲击和成交失败报告。
- 因子覆盖率和质量报告。
- 单因子 IC、RankIC、ICIR。
- Newey-West HAC IC t-stat、block bootstrap 和 10/21/40 日 block 敏感性。
- 分层收益、制度性风险切片和 IC 衰减半衰期报告。
- Concept shift 诊断：预注册压力段、成熟 IC yellow/red 状态机、指数衰减 vs 等权对照、拥挤度指标和分布漂移监控。
- 基础组合回测：等权、ICIR、正交化复合因子、线性、LightGBM/Ranker。
- 成本、换手、成交失败、容量报告。

### Phase B：风险状态和组合约束

目标：减少回撤，约束风格和行业暴露。

产出：

- 市场状态变量库。
- 仓位开关对照实验。
- R5 衰减权重稳健性：等权 5 年、12 月半衰期指数衰减、18 月半衰期敏感性和成熟 IC 状态机对照；必须同口径击败等权控制且通过全部审计才可晋级。
- 风险开关 v1：S3 前使用 25/25/25/25 均匀权重占位；S3 验证后替换为数据驱动仓位比例。100/60/30/0 只保留为可选历史假设或挑战基线，不作为默认事实。
- 熔断规则：组合回撤、市场宽度崩塌、跌停压力和流动性枯竭触发降仓。
- 行业、市值、beta、换手、容量约束组合。

### Phase C：外部低频数据 ETL

目标：补齐基本面、公司行为和风险事件。

优先顺序：

1. 公司行为和分红送配。
2. 财报、业绩预告、业绩快报。
3. 融资融券。
4. 股东户数、质押、限售解禁。

### Phase D：特色 alpha 和高级模型

目标：在强基线基础上验证增量。

候选：

- 筹码增强。
- 涨停事件卫星。
- 分钟执行优化。
- 期权波动率和保护性对冲。
- 深度时序、NLP、RL。

---

## 8. 活跃文档

后续只维护 Git 项目中的两份活跃策略文档：

1. `D:\quantum_a0\quant-strategy-study-plan\quant_strategy_plan.md`：短总纲，记录方向、证据、优先级和禁用结论。
2. `D:\quantum_a0\quant-strategy-study-plan\quant_strategy_research_plan_detailed.md`：详细执行规范，记录数据口径、标签、验证、回测、台账、验收和 review 清单。

`D:\data\strategy\` 下的旧副本只作为迁移前来源；后续若需要保留副本，必须从 Git 项目同步回写，不得双向分叉维护。

`量化时间序列模型调研和选择.md` 与 `量化策略设计调研与建议.md` 作为参考材料，不作为直接执行规范。






