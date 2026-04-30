# A股量化策略研究执行规范（2026-04-30 版）

> 本文件是后续量化策略实验的执行规范。所有策略实验、回测、模型训练和 review 都必须按本文件执行。  
> 短总纲见 `quant_strategy_plan.md`。  
> Canonical 数据源为 `D:\data\warehouse`。

---

## 1. 总原则

### 1.1 研究目标

本项目的目标不是寻找样本内最高收益曲线，而是建立可审计、可复现、可迭代、可落地的 A 股策略研究体系。

所有策略必须证明：

1. 数据无明显未来信息。
2. 回测交易假设保守。
3. 成本后仍有样本外价值。
4. 年度、市场状态和参数扰动下不过度脆弱。
5. 复杂度增加能被增量收益或风险改善解释。

### 1.2 硬性时点约束

所有特征、标签和交易必须满足：

```text
feature_time <= available_at <= decision_time < execution_time <= label_end_time
```

默认日频规则：

- T 日行情、估值、风险警示等日频字段默认 T 日 16:00 后可见。
- T 日盘后生成信号。
- T+1 执行。
- 普通 A 股不做 T+0。
- 训练、验证、回测中不得使用 OOT 期间才可知道的未来 label。

### 1.2.1 主线和 sidecar 登记

R10 后，S1 阶段采用“一条正式 alpha 主线 + 一个日频探索/风控辅助通道”。`S1-M` 是近期唯一正式主线；`S1-D` 只做短期 IC、alpha 衰减、风险预警、候选接口和离线执行审计。二者仍必须独立登记，且不得把 `S1-D` 的 OOT、holdout 或 stress slice 结果用于选择 `S1-M` 的模型、阈值、半衰期或训练窗口。

| track_id | 名称 | 主标签 | 决策和执行 | 调仓/持有 | 默认重训 | 当前数据状态 |
|---|---|---|---|---|---|---|
| `S1-M` | 月选股正式强基线 | 20 日 forward excess/rank，10 日作稳健性 | T 日盘后信号，T+1 执行 | 约 21 个交易日调仓，持有到下一次月度再平衡 | 63 个交易日；月度重训只作预注册敏感性 | R7 `features/labels` 已支持，仍需 calendar、holdout、测试族台账和实验登记 |
| `S1-D` | 日频探索/风控辅助通道 | 1 日和 5 日 forward excess/rank，10/20 日作稳健性或交叉对照 | 每个交易日盘后重算 candidate score、risk signal 和 alert state，T+1 执行仅用于离线订单审计 | 默认不主动调仓；离线组合模拟不进入 official keep；主动仓位变化需另经 walk-forward 验证 | 63 个交易日；每日重训只作后置敏感性 | R7 `features/labels` 已支持，仍需 daily profile、orders audit、turnover/capacity 报告 |

每个 track 必须独立记录 `track_id`、`label_id`、`calendar_id`、`panel_hash`、`execution_rule_id`、`test_family_id`、`attempt_count` 和 holdout 访问状态。`S1-D` 的任何减仓、停用、止损或主动调仓升级，都必须有预注册 walk-forward 验证，不得使用当前 OOT、holdout 或未成熟标签直接影响仓位。

### 1.3 Canonical 数据源

只以 `D:\data\warehouse` 为策略研究 canonical 数据源。

数据事实、source status 和行数口径以 Git 项目中的 `warehouse_build_manifest.json` 及其引用的 warehouse 审计报告为准。`DATA_USAGE_GUIDE.md`、`WAREHOUSE_README.md` 和 `external_data_sources.csv` 是策略文档随 Git 维护的数据依据镜像；手写行数或 STATUS 文件若与 manifest 冲突，不作为正式实验依据。

允许使用但必须标注用途：

- `D:\data\processed`：旧清洗产物盘点和复核，不直接进入策略。
- `D:\quantum_a0\qant-codex-20260429`：旧模型和反例研究，不作为收益有效性证据。
- AkShare：外部数据候选，接入前必须有 schema、`available_at`、质量检查和 source gap 报告。

---

## 2. 当前可用数据

### 2.1 核心表

| 表 | 行数 | 范围 | 策略用途 | 注意事项 |
|---|---:|---|---|---|
| `prices_daily_unadjusted` | 17,599,789 | 1990-12-19 至 2026-04-27 | 真实成交价、成交额、涨跌停、容量 | 不直接做长期收益标签 |
| `prices_daily_returns` | 17,599,789 | 1990-12-19 至 2026-04-27 | `return_adjusted_pit` 用于收益、标签、绩效 | 禁止全样本前复权 |
| `valuation_daily` | 16,642,794 | 2000-01-04 至 2026-04-27 | 市值、股本、换手率先作市场慢变量；估值/财报派生字段后置审计 | T 日盘后可见，左连接 |
| `tradability_daily` | 18,177,689 | 1990-12-19 至 2026-04-27 | bar 存在、推断停牌、可交易性 | 停牌是工程推断 |
| `tradability_daily_enriched` | 18,177,689 | 1990-12-19 至 2026-04-27 | 涨跌停、买卖阻断、上市年龄、风险警示 | 第一版成交过滤首选 |
| `universe_daily` | 18,177,689 | 1990-12-19 至 2026-04-27 | 基础和因子研究股票池 | 第一版研究首选 |
| `benchmarks` | 31,229 | 1990-12-19 至 2026-04-27 | 全 A 代理、官方中证指数 | 禁止恢复同日成交额加权 |
| `reference_rates` | 55,964 | 1990-12-19 至 2026-04-27 | 国债、Shibor、固定 fallback | 固定 1.5% 仅作 fallback |
| `industry_classification.pit_industry_intervals_akshare` | 53,925 | 1990-01-29 至 2026-04-24 | PIT 行业中性和行业轮动 | 必须固定分类标准 |
| `risk_warning_daily` | 8,973,264 | 1994-01-03 至 2026-04-27 | 风险警示过滤 | 深市历史较完整，沪/北不足 |
| `trading_costs.equity_cost_history` | 23 | 1990-12-19 至 2023-08-28 | 交易成本 | 部分为研究假设 |

正式报告应引用 `warehouse_build_manifest.json` 的 hash，而不是重新手工抄写上表行数。R7 已生成 `features/market_daily_v1` 与 `labels/forward_returns_v1`，各 15,420,654 行，并输出 `feature_label_panel_v1_manifest.json`、PIT feature audit 和 label audit；标签已覆盖 1/5/10/20 日，可支撑 S1-M 月选股正式主线和 S1-D 日频探索/风控辅助验证。R7 只解除面板占位阻塞，S1 训练前仍必须引用对应 track 的 walk-forward calendar、holdout log、benchmark audit、validation hash 和实验登记。临时实验缓存只能作为中间产物，不得直接作为官方 S1 evidence。

### 2.2 数据缺口

每份策略报告必须披露：

- 2026-01-05 至 2026-02-05 的估值覆盖缺口。
- `valuation_daily` 与收益表 key 不完全一致。
- 完整交易所官方停复牌公告缺失。
- 沪/北历史 ST、摘帽、摘星缺 PIT 官方源。
- 历史 PIT 指数成分和权重缺失。
- 三所官方历史差异日历未独立验证。
- 成本中的佣金、滑点、冲击成本仍是研究假设。
- 公司行为、除权除息、分红送配尚未形成独立主表；`return_adjusted_pit` 当前只能声明为 adjusted-return proxy，不能宣称完整 total-return accounting 已闭环。
- 筹码、涨停、分钟、期权、融资融券、北向、ETF flows、股指期货 basis/OI 尚未形成可审计 warehouse 主表。
- `prices_daily_unadjusted`、`prices_daily_returns`、`valuation_daily` 和 `security_master.equity_master` 的必需 source/time/status 字段已由 R7 补齐；后续重建后必须复跑 `source_status_audit_r7.json` 或等价审计。

### 2.3 数据质量门槛

任意策略实验前必须确认：

```powershell
C:\Users\LeoShu\.conda\envs\ptorch\python.exe D:\data\scripts\warehouse\leakage_check.py --warehouse D:\data\warehouse --workers 6
```

最小通过条件：

- `leakage_check` PASS。
- 所用表 `(asset_id, trade_date)` 或业务主键无重复。
- `available_at <= decision_time`。
- benchmark、reference rate、cost model 覆盖回测窗口。
- 回测结束日不得晚于行情最大可用日。

实验层还必须补充三类审计；warehouse 层 `leakage_check` 不能替代它们：

| 审计 | 最小要求 | 产物 |
|---|---|---|
| 数据 manifest | 记录 build_id、最大数据日期、表行数、source status、schema hash、leakage check hash 和 validation hash | `warehouse_build_manifest.json` |
| source registry | 登记每个外部源的状态、字段、available_at 要求和 source gap | `external_data_sources.csv` |
| 因子 PIT 审计 | 检查每个特征的 `source`、`available_at`、`decision_time`、截面成员和复权生效规则 | `pit_factor_audit` 报告或等价表 |
| 验证参数固化 | 引用 Round 5/round2/r3/r4/r5/r6 参数并记录 `validation_params.json` 的 SHA256；机器可读镜像随 Git 维护，但若镜像与本文档冲突，以本文档、`consensus_audit_report_20260430.md`、`consensus_audit_round2.md`、`consensus_audit_r3.md`、`consensus_audit_r4.md`、`consensus_audit_r5.md` 和 `consensus_audit_r6.md` 为准 | `validation_params_hash` |
| benchmark 审计 | 确认 benchmark 来源、可得日、覆盖区间、是否为官方或内部代理，并按时期报告 `coverage_assets` | `benchmark_audit` 报告 |
| 字段级 source status | 检查核心表是否有 `source_status` 或字段 PIT tier；R7 当前 PASS，重建后必须复跑 | `source_status_audit_r7` |

数据缺口处理还必须遵守：

- `valuation_daily` 在 2026-01-05 至 2026-02-05 缺失 24 个交易日，影响 holdout 附近估值类特征。只允许对市值、估值、换手率等慢变量特征按 `asset_id` 做有界 forward-fill，最长 25 个交易日，并保留 `valuation_ffill_flag` 或等价缺口 mask。
- forward-fill 禁止用于收益、标签、成交价、成交量、成交额、执行价格或绩效会计。
- S1 报告必须比较有/无 valuation forward-fill 的 IC、RankIC 和组合结果；若结论依赖该补值，状态只能是 `candidate` 或 `inconclusive`。
- `valuation_daily` 字段必须拆成 `market_derived_pit_candidate` 和 `financial_statement_dependent_unverified_pit` 两类。市值、流通市值、股本、换手率可先进入 market-only baseline；PE/PB/PS/TTM、ROE、利润增速等财报派生字段需公告日和供应商计算时点 PIT 审计后才能进入 keep。
- `tradability_daily_enriched.amount` 可作为 trailing ADV 来源；`listing_age_trading_days < 20` 的样本必须标记为 `adv_insufficient_new_listing`，不得用新股成交额异常值外推容量。
- benchmark 审计必须披露早期覆盖股票数。当前本地证据显示 `CN_A_ALL_EQW_PROXY` 1990 年仅覆盖 1-5 只股票，2005 年中位约 1315 只，2024 年中位约 5342 只；2005 前只作为敏感性检查。

---

## 3. 股票池和交易约束

### 3.1 默认股票池

第一版组合回测和买入候选默认使用 `universe_daily.in_factor_research_universe=True`。但正式研究必须拆分三层 universe，不能把 close-based 可买卖过滤同时当作 IC 研究 universe：

| 层 | 用途 | 最小规则 |
|---|---|---|
| `research_observable_universe` | 因子 IC、特征分布、CSRP/分布漂移诊断 | 已上市、bar 存在、基础生命周期和数据质量通过；不因 T 日涨停/跌停直接删除风险样本。 |
| `entry_eligible_universe` | 买入候选和组合调仓输入 | T+1 可买、ST、上市年龄、ADV、容量、涨跌停压力和交易成本约束。当前 `universe_daily.in_factor_research_universe` 只能视作该层的保守代理。 |
| `execution_accounting_universe` | 回测成交和持仓会计 | 订单层记录涨停买不到、跌停卖不出、停牌延迟、连续锁死、解锁后收益和未成交暴露。 |

当前可确认的默认规则来自 P1 构造脚本和本地 Parquet 抽查：

```text
in_pit_lifecycle_universe = True
in_baseline_tradeable_universe = can_trade_close_based
in_factor_research_universe =
    can_trade_close_based
    AND listing_age_trading_days >= 60
    AND NOT is_risk_warning_pit

can_trade_close_based = can_buy_close_based AND can_sell_close_based
can_buy_close_based = is_tradable AND NOT close_at_limit_up
can_sell_close_based = is_tradable AND NOT close_at_limit_down
is_tradable = bar_present AND price_bar_tradable_flag
is_suspended_inferred = NOT bar_present
```

这条规则只是保守 entry universe 过滤，不是策略信号，也不能覆盖全部研究观察样本。当前可确认它没有直接用 `in_current_stock_list` 筛选历史 factor universe；但不能据此宣称股票池 PIT 审计已完整通过。正式 S1 启动前必须完成 `universe_daily_construction_audit`：

- 复核 `universe_daily` 构造脚本、字段来源、`available_at`、`decision_time` 和年度样本数。
- 确认 ST、停牌、涨跌停、上市年龄和历史证券过滤只使用 T 日或 T-1 日可得信息。
- 确认 `in_current_stock_list`、当前 ST 状态、当前风险警示状态或当前上市状态没有被用于回填历史筛选。
- 确认退市、暂停上市、历史证券没有被幸存者偏差删除。
- 输出规则版本或脚本 hash、字段来源、年度通过率、剔除原因分布、公式 mismatch 检查、`source_status` 分布和已知 source gap。
- 明确披露未闭环缺口：沪/北历史 ST 仍缺带日期官方或授权源，全历史官方停复牌公告库仍缺；这些缺口更可能让股票池偏宽，不得被当作已验证无偏。
- 后续应把 `universe_rule_version` 落到产物或审计报告；若 Parquet 主表暂未持久化该字段，必须记录构造脚本 hash。
- 输出三层 universe 的年度样本数、重叠率、剔除原因和涨跌停/停牌风险样本保留情况。

若自定义股票池，必须从以下字段派生：

- bar 是否存在。
- 是否推断停牌。
- 上市交易日年龄。
- 是否风险警示。
- 是否涨跌停买卖阻断。
- 最近成交额和成交量。
- 是否历史证券，避免幸存者偏差。

禁止直接使用当前股票列表筛历史。

### 3.2 默认成交规则

默认日频组合回测：

- T 日盘后信号。
- T+1 开盘或保守 close-based 价格执行，必须标明。
- 买入：涨停、一字涨停、停牌、无 bar、风险警示排除。
- 卖出：跌停、一字跌停、停牌时成交失败或延迟。
- 买入按 100 股整数手。
- 现金和持仓每日结算。
- T+1 限制：当日买入不可当日卖出。

涨跌停和停牌失败必须进入订单状态，而不是简单删除交易日：

- 买入失败：记录 `limit_up_buy_fail_count`、`suspend_buy_fail_count` 和失败金额。
- 卖出失败：记录 `limit_down_sell_fail_count`、`suspend_sell_fail_count`、延迟天数和持仓继续暴露收益。
- 连续锁死：统计连续 1/2/3+ 个交易日未成交队列、解锁后 1/3/5 日反转收益。
- 未成交订单默认不无限期挂单；超过预设最长延迟后按新信号重新评估。
- 任何因涨跌停或停牌无法变现的纸面 alpha，不得计入可执行 alpha 结论。

开盘冲击采用分层实现：

| 层级 | 当前状态 | 规则 |
|---|---|---|
| L1 日频保守模型 | 立即可用 | 用未复权 `open`、`amount`、成交额参与率、涨跌停状态和滑点假设执行。 |
| L2 开盘成交压力模型 | S1/S2 输出 | 按开盘/非开盘、成交额分位、参与率、涨跌停压力分档设置滑点和成交失败率。 |
| L3 集合竞价/分钟三段模型 | 后置 | 需 `prices_minute` 或集合竞价表入仓后，才区分集合竞价、开盘成交、正常交易。 |

### 3.3 成本和容量

成本必须来自 `trading_costs.equity_cost_history`，并在报告中列出：

- 佣金。
- 印花税。
- 过户费。
- 经手费、证管费等规费。
- 滑点。
- 冲击成本。

容量压力测试至少覆盖：

- 1000 万。
- 5000 万。
- 1 亿。
- 5 亿，如策略表面容量足够。

每档报告：

- 平均参与率。
- 最大参与率。
- 成交失败率。
- 成本拖累。
- 单票集中度。
- 换手。

trailing ADV 规则：

- 默认从 `tradability_daily_enriched.amount` 计算，报告 20/60/120 个交易日窗口。
- `amount` 对有 bar 样本应完整；无 bar、停牌或 `bar_present=False` 行不得被当作真实零成交参与率，需要在报告中区分“无成交 bar 缺失”和“实际成交额为 0”。
- 每个 ADV 窗口必须报告有效成交日数；有效日数不足窗口 80% 或上市交易日龄 < 20 的样本标记为 `adv_insufficient`。
- 自定义股票池或事件策略即使不使用默认 factor universe，也必须执行 `adv_insufficient` 标记，避免新股或缺 bar 样本夸大容量。
- 容量判断以 trailing ADV、参与率、成交失败和成本拖累为主，不能只看当前日成交额。

拥挤容量规则：

- S1 至少报告自有参与率、组合目标成交额 / 全市场成交额、组合目标成交额 / 行业成交额或市值分层成交额。
- S1/S1.5 必须报告因子组合与常见拥挤风格的重叠：小市值、低流动性、高换手、反转、残差动量和微盘。
- 左尾拥挤必须报告因子组合收益 skew、CVaR、最差 1% 日、跌停卖不出占比和解锁后 1/3/5 日收益。
- 风格去杠杆压力可先用市场宽度、涨跌停压力、成交额变化和风格收益代理；融资融券、北向、ETF flows、股指期货 basis/OI 未入仓前只能标记为 source gap。
- 只用自身 1% ADV 参与率不能作为容量安全结论。

分档滑点和冲击成本在 S1 报告中至少给出保守版本，在 S2 中深化：

| 分档维度 | 最小分档 |
|---|---|
| 成交额 | P20/P50/P80 或等价低/中/高流动性 |
| 参与率 | `<1%`、`1%-5%`、`5%-10%`、`>10%` |
| 交易时段 | 开盘执行、非开盘执行、保守 close-based |
| 市场压力 | 正常、涨跌停压力高、流动性枯竭 |

报告必须同时给出基础成本、分档滑点、冲击成本后的指标，避免只用低估成本版本做 keep 决策。

---



## 4. 标签体系

### 4.1 默认标签

| 标签 | 计算 | 用途 | 必须 purge |
|---|---|---|---|
| `excess_ret_1d` | 个股 T+1 收益减 benchmark | S1-D 短期 IC、风险预警和 alpha 衰减监控标签；不单独构成主动调仓 keep 证据 | 1 个交易日 |
| `excess_ret_5d` | 个股未来 5 日超额收益 | S1-D 风控辅助和短 horizon 稳健性标签，用于降低 1 日噪声和换手敏感性 | 5 个交易日 |
| `excess_ret_10d` | 个股未来 10 日超额收益 | qant 对照和中频模型 | 10 个交易日 |
| `excess_ret_20d` | 个股未来 20 日超额收益 | S1-M 月选股主标签 | 20 个交易日 |
| `rank_ret_1d/5d/20d` | 同日横截面未来收益 rank | S1-M 排序模型和 S1-D 风控辅助排序诊断 | 对应 horizon |
| `top_quantile_1d/5d/20d` | 是否进入未来收益 top 分位 | S1-M 分类模型和 S1-D 离线候选诊断 | 对应 horizon |
| `realized_vol_20d` | 未来 20 日波动率 | 风险模型 | 20 个交易日 |
| `max_dd_20d` | 买入后 20 日最大回撤 | 风控标签 | 20 个交易日 |

标签从 `return_adjusted_pit` 计算，成交约束从未复权价格和可交易表计算。

S1-D 日频探索当前只能使用 R7 已审计的 1 日和 5 日 forward adjusted-return 标签。若研究 open-to-open、close-to-open、overnight、intraday、盘中止损或集合竞价成交标签，必须新建 label set，登记 source/available_at/decision_time，并重跑 PIT feature audit、label audit 和 manifest/hash；未入仓前不得进入 official keep，也不得触发主动调仓或风控动作。

### 4.2 禁止标签和特征混用

禁止：

- 在特征表中存入 future return。
- 用 T+1 或未来窗口的高低点做 T 日止盈止损特征。
- 用未来涨跌停状态过滤训练样本。
- 用未来行业、未来 ST、未来停牌状态构造历史股票池。

### 4.3 forward 和 execution label 规则

所有 forward 或 execution label 必须声明：

- `track_id`：`S1-M` 或 `S1-D`。
- `label_id` 和 `label_horizon`。
- `label_start`、`label_end` 和 `label_maturity_date`。
- `purge_days`、`embargo_days` 和是否可用于 keep。
- 标签是否使用 adjusted-return proxy，是否受公司行为/total-return source gap 影响。
- 是否为可执行标签；若只用 forward return，不得把它直接写成可执行 PnL。

正式证据仍必须服从 `purge_days >= max(label_horizon*3, 40)`。因此 1 日标签也至少使用 40 个交易日 purge，不能因为 horizon 短就让训练样本贴近预测日。

### 4.4 qant 类 10 日标签特殊规则

任何 10 日 forward label 必须：

- 在 OOT 月边界剔除 `target_date_10d >= oot_start` 的训练候选样本。
- 跑 split label audit。
- 报告 train/validation 中跨 OOT label 行数。
- 诊断性 qant 对照可使用 `--purge-days 10` 或等价逻辑。
- 新的正式策略证据必须服从 Round 5 规则 `purge_days >= max(label_horizon*3, 40)`，除非更窄的历史诊断目的在实验登记中预先声明，且不得进入 keep 决策。

---

## 5. 因子库

### 5.1 P1 核心日频因子

先用已入仓表构建以下因子：

| 类别 | 示例 | 来源 | R4 字段可构建性裁决 |
|---|---|---|---|
| 市值 | `log_total_mv`、`log_circ_mv` | `valuation_daily.total_mv/circ_mv` | 字段存在；2026 估值缺口需 mask/ffill 敏感性 |
| 估值 | EP、BP、SP、股息率代理 | `valuation_daily.pe_ttm/pb/ps_ttm` 等 | 字段存在；财报披露和估值 available_at 仍需 PIT audit |
| 流动性 | 成交额均值、换手率、Amihud illiquidity | `tradability_daily_enriched.amount`、`valuation_daily.turnover_rate`、日 K | 字段存在；ADV 需有效天数和新股不足标记 |
| 动量 | 5/20/60/120 日 PIT 复权收益 | `prices_daily_returns.return_adjusted_pit` | 可构建；禁止全样本复权 |
| 反转 | 1/3/5 日收益 | `prices_daily_returns.return_adjusted_pit` | 可构建；与 T+1 执行约束一起评估 |
| 波动率 | 20/60 日波动、下行波动、振幅 | `prices_daily_returns`、未复权日 K | 可构建；窗口必须只用决策前历史 |
| 风险 | beta、残差波动、最大回撤 | `prices_daily_returns` + `benchmarks` | 可构建；benchmark 早期覆盖和代理口径需审计 |
| 交易约束 | 上市年龄、涨跌停、停牌、ST | `tradability_daily_enriched.listing_age_trading_days`、`close_at_limit_up/down`、`high_hit_limit_up`、`low_hit_limit_down`、`can_buy_close_based`、`can_sell_close_based`、`buy_blocked_close_based`、`sell_blocked_close_based`、`is_risk_warning_pit` | 可构建；沪/北 ST 与停复牌官方源仍有 PIT 缺口 |
| 行业 | PIT 行业哑变量、行业收益、行业动量 | `industry_classification.pit_industry_intervals_akshare` | 可构建；依赖 AkShare 行业源和固定分类标准审计 |

“可构建”只表示当前 warehouse 字段足以计算候选因子，不等于可进入 keep。每个因子仍必须通过字段覆盖率、缺失率、异常值、`available_at`、`decision_time`、PIT 来源和缺口影响审计。

因子 PIT 合规要求：

- 估值、市值、股本和换手因子必须使用当日 `available_at` 与 `decision_time`；估值类字段不能假设财报披露早于实际公告日。
- 2026-01-05 至 2026-02-05 的估值缺口必须生成缺口 mask；若对慢变量估值特征做有界 forward-fill，最长 25 个交易日，并同时报告 drop-gap、no-valuation 和 ffill 三种口径的敏感性。
- 复权收益、动量和标签必须使用 `return_adjusted_pit` 或等价 PIT 调整收益；复权信息默认 T 日盘后可见、T+1 生效。
- 月末或调仓截面必须只包含当时已存在、已上市且通过可交易过滤的证券，不得使用未来成分、当前行业快照或当前风险警示状态。
- 所有新因子进入组合回测前必须通过因子 PIT 审计；未通过的因子只能用于离线诊断，不能进入 keep 决策。

因子正交化执行规范：

- 原始因子先完成缺失处理、winsorize、横截面 z-score，以及预注册的行业/市值中性化。
- 单因子、等权和原始 ICIR 加权必须保留为基线；正交化只作为复合因子和线性模型的预注册对照分支，不替代原始因子主证据。
- Gram-Schmidt 顺序只能由训练窗口内的 ICIR 降序确定；OOT、holdout 或全样本信息不得参与排序、方向选择或参数估计。
- 每个调仓截面输出 `orthogonalized_factor_panel`，并记录 `orthogonalization_order`、输入覆盖率、缺失处理规则和方向约定。
- 必须报告正交化前后因子相关性矩阵、IC/RankIC 变化、因子方向是否保持，以及与原始 ICIR 和 Ridge/ElasticNet 的同口径比较。



### 5.2 P2 外部低频因子

AkShare 接入后再进入：

- 分红、送转、配股、除权除息事件。
- 财报、业绩预告、业绩快报。
- 融资融券。
- 股东户数。
- 质押比例。
- 限售解禁。
- 分析师预期修正、一致预期变化和评级调整，但必须有可审计历史源和披露时间。
- 北向资金。
- 龙虎榜、大宗交易。

### 5.3 P3 特色因子

需先完成入仓和时点验证：

- 筹码成本偏离、成本宽度、胜率、筹码迁移。
- 涨停首板、连板、封单、打开次数、行业涨停宽度。
- 分钟 VWAP、开盘冲击、收盘流动性、滑点曲线。
- 期权 IV、skew、term structure、Greeks、PCR。

---

## 6. 模型体系

### 6.1 基线优先级

模型进入顺序：

1. 单因子。
2. 等权打分。
3. ICIR 加权。
4. 训练窗 ICIR 排序后的 Gram-Schmidt 正交化复合因子。
5. Ridge、ElasticNet。
6. LightGBM / XGBoost。
7. LightGBM Ranker / LambdaRank。
8. CatBoost。
9. 深度时序模型。
10. NLP / RL。

任何复杂模型必须在同一数据、同一股票池、同一成本、同一验证切分下对比强基线。

### 6.1.5 R5 训练权重

R5/R10 后，concept shift 的近期执行方案不再采用双轨、动态 alpha 或在线 Track B，而是在 S1-M 正式主线的单轨 5 年 rolling 框架内加入预注册样本权重；S1-D 仅以同样隔离规则做探索/风控辅助报告：

- 等权 5 年 rolling 是必须保留的控制组。
- 指数衰减主口径使用 `row_equal_decay_weight = 2 ** (-age_trading_days / (half_life_months * 21))`，其中 `age_trading_days` 是样本 `decision_time` 到当前 step `train_end` 的交易日年龄。
- 必须同时报告 `date_balanced_decay_weight = date_weight_t / n_assets_t` 对照，其中 `date_weight_t = 2 ** (-age_trading_days_t / (half_life_months * 21))`，避免近年股票数扩张造成隐性双重加权。
- 默认半衰期为 12 个月；18 个月作为预注册敏感性；R10 的 6/24 个月作为必报诊断，36 个月只作可选研究网格；非默认半衰期全部计入 `attempt_count`，不能进入 keep 决策或用于 OOT/holdout 择优。
- 每个训练 step 内将样本权重归一化到均值 1，并记录权重分布、最大/最小权重、有效样本量、每日股票数、每个日期总权重和 row-equal/date-balanced 结果差异。
- `sklearn`、`LightGBM`、`XGBoost` 使用 `sample_weight`；线性模型必须使用加权回归或显式加权损失。
- 半衰期、重训频率、权重口径和告警阈值不得由当前 OOT 或 holdout 选择。

### 6.2 当前依赖状态

已可用：

- `lightgbm`
- `xgboost`
- `sklearn`
- `qlib`
- `cvxpy`
- `torch`
- `statsmodels`

尚未安装或未验证：

- `arch`
- `vectorbt`
- `riskfolio-lib`
- `PyPortfolioOpt`
- `catboost`
- `darts`
- `neuralforecast`

缺失依赖只在对应阶段确实进入时安装，并记录版本、安装命令和最小 smoke test。

### 6.3 深度模型准入

本地深度模型路线已按 Round 4 共识降级。近期只保留轻量 LSTM 或 1D-CNN 作为 P4 对照；TFT、N-HiTS、PatchTST、iTransformer、Chronos/TimesFM/Moirai 等重模型归档为研究储备或云端实验，不能作为本地近期执行计划。

任何深度模型只有在满足以下条件后才能进入正式对照：

- 日频强基线完成。
- walk-forward 与 purge/embargo 体系稳定。
- 有明确额外收益来源，例如多周期分位数预测、波动率预测、场景生成。
- 训练日志、随机种子、模型版本、输出缓存可复现。
- 与 LightGBM/Ranker 同口径比较。
- 先完成小模型 smoke test，明确硬件、随机种子、训练耗时和失败回滚条件。

深度模型不得以“模型先进”为进入理由。

---

## 7. 验证框架

### 7.1 默认验证

主证据必须使用预注册 walk-forward 参数。当前官方口径以 Round 5 共识和本文档为准；本地机器可读参数镜像必须在执行前与下表一致并记录 hash：

| 参数 | 默认值 |
|---|---:|
| 主数据起点 | 2005-01-01 |
| 训练窗口 | 5 年；4/6 年只作 R10 诊断敏感性，5 年是唯一 keep 通道 |
| track profile | `S1-M` 月选股正式启动；`S1-D` 日频探索/风控 sidecar 同步预留接口并离线验证 |
| S1-M 测试/调仓窗口 | 20 日标签，约 21 个交易日调仓/预测 |
| S1-D 测试/调仓窗口 | 1/5 日标签用于短期 IC、风险预警、alpha 衰减和离线执行审计；不作为正式主动调仓证据 |
| 训练权重 | 等权 5 年必须作为对照；R5/R10 指数衰减候选默认半衰期 12 个月，18 个月为预注册敏感性，6/24 个月为必报诊断；row-equal 与 date-balanced 均需报告 |
| 模型重训频率 | 默认每 63 个交易日重训一次；两次重训之间使用最新冻结模型；S1-D 每日预测不等于每日重训 |
| purge | `>= max(label_horizon*3, 40)` 个交易日 |
| embargo | 10 个交易日 |
| OOT 起点 | 由交易日历生成，必须同时满足 5 年训练窗口、`train_end <= oot_start - purge_days` 和 label maturity；通常落在 2010Q1 附近 |
| 最少 OOT step | 24；这是最低验收门槛，不是总步数 |
| IC 显著性 | 默认使用 Newey-West HAC 调整后的 IC t-stat；普通 t-stat 只能作为诊断 |
| bootstrap | Block Bootstrap，组合收益默认 `block_days=max(label_horizon, rebalance_interval)`，至少 5000 次；S1-D 不得让 1 日标签把 block 退化为 1 日，keep/晋级前仍报告 10/21/40 日敏感性 |
| 多重检验 | 候选因子 > 20 个时必须做 FDR 校正 |
| holdout | 最后 12 个月（约 252 个交易日）作为最终验收窗口；不参与调参、特征选择、early stopping、阈值选择或仓位开关选择；通过条件至少为方向一致且 Sharpe > 0 |

必须生成 `walk_forward_calendar_v1.parquet` 或等价表，并在每个预测文件中引用 `step_id` 和 `walk_forward_calendar_hash`。最小字段：

```text
step_id
track_id
calendar_id
prediction_start_date
prediction_end_date
train_start_date
train_end_date
label_horizon
label_definition_id
purge_days
embargo_days
label_maturity_date
decision_frequency
rebalance_interval
holding_period
execution_rule_id
panel_hash
model_refit_flag
frozen_model_version
holdout_flag
```

主证据：

- chronological walk-forward。
- OOT 月、21 个交易日窗口、日度决策窗口或 OOT 年，必须在实验登记中预先声明。
- OOT 总步数必须由实际交易日历、主数据起点、训练窗口、track cadence 和最后 12 个月 holdout 剔除后生成并披露；不得把 24 步写成总步数。
- 24 个 OOT step 原则上在 holdout 窗口之前完成；holdout 只用于最终验收，不参与 OOT 步数计数。
- Purged split。
- Embargo。
- split label audit。

S1-D 日频 sidecar 补充规则：

- 训练和验证必须按 `decision_date` 横截面分组；Ranker 的 group 必须是日期截面，不能做 random row split。
- Early stopping、阈值、特征选择和半衰期选择只能使用训练窗口内部、已 purge 的 validation，不得使用当前 OOT 或 holdout。
- IC/Ranks IC 先按日计算，再形成日度 IC 序列做 HAC/Newey-West、block bootstrap、周/月汇总和 concept shift 状态机。
- 默认不生成主动调仓组合；离线组合模拟必须处理重叠持仓、T+1、100 股整数手、涨跌停/停牌订单失败、未成交继续暴露和每日换手，模拟结果不得直接进入 official keep。
- R10 三层换手控制用于离线审计和未来升级门槛：与前一日持仓重叠率 >=85%、单票日变动 <=2%、单边日换手 <=10%。
- R10 动态 IC 换手公式只能作为 Phase 2 report-only 或 tighten-only 诊断；输入必须是至少滞后一 step 的成熟 trailing IC，验证前不得突破 10% 单边硬上限。

辅助诊断：

- blocked random + purge + embargo。
- Combinatorial Purged CV。
- 参数扰动。
- 分年度、分市场状态、分市值和分行业表现。
- Concept shift 诊断和 R5 训练权重必须分层：
  - S1 主证据链保持 5 年 rolling 单轨框架，并保留等权对照。
  - S1 报告可输出 row-equal/date-balanced 指数衰减 vs 等权、成熟 IC yellow/red 状态、分段描述性表现、分布漂移和拥挤度监控。
  - S1.5 只评估预注册指数衰减半衰期、权重口径和重训频率敏感性，不评估双轨、动态 alpha 或在线 Track B；S1-D 只作为风控 sidecar 参与验证。
  - S3 才把稳定通过验证的告警转成仓位、熔断或降权规则。

禁止把普通 random 8/2 作为最终证据。

硬规则：

- 任何使用未来收益标签的训练、验证、early stopping、阈值选择或调参样本，都必须先做 OOT 边界 purge。
- 所有模型训练截止日都必须满足 `train_end <= oot_start - purge_days`，并同时满足 label maturity 和 embargo；R4 示例中的 `T-21d` 不足以替代正式 purge 规则。
- random 只能作为 blocked random 诊断，且必须同时有 `validation_purge_days` 和 `embargo_days`。
- 未报告 split label audit 的模型结果不得进入 keep、晋级或总纲结论。
- IC 序列、重叠标签或相邻 walk-forward step 的训练窗口重叠率必须在报告中披露；重叠率按实际 `training_window_days` 和 `step_days` 计算，不使用未经核验的固定百分比。
- Newey-West 实现必须估计 IC 序列均值的 HAC 标准误：`se_mean = sqrt(long_run_variance / n)`，`t_hac = mean(IC) / se_mean`；如果库函数已经返回均值标准误，不得再次除以 `sqrt(n)`。默认带宽使用预注册确定性规则 `lag=max(1, floor(4*(n/100)^(2/9)))`，除非实验登记在启动前明确替换为另一条确定性规则。
- 24 个 OOT step 属于小样本，HAC t-stat 与 block bootstrap 都必须报告；keep/晋级时采用更保守的统计结论，不能在 naive、HAC 和不同 block 敏感性之间择优。
- 组合收益 bootstrap 的 `block_days=max(label_horizon, rebalance_interval)`；纯 IC 诊断可预注册 `max(label_horizon, empirical_acf_cutoff)`，但 keep/晋级前必须报告 10/21/40 日敏感性。
- 偏离 Round 5/round2/r3/r4/r5/r6 参数时，必须在实验启动前写明原因，并在报告中列出参数 hash 和实际参数；`validation_params.json` 是 Git 中的机器可读镜像。若镜像与本文档冲突，以本文档为准并先修正镜像后再执行。

Concept shift 硬规则：

- “训练数据滞后评估数据”是 walk-forward 的基本原则，不是缺陷。真正风险是非平稳性、covariate shift 和 concept shift。
- 衰减权重只能重加权决策时点之前已观测并已成熟的数据，不能引入决策时点之后才出现的标签。
- Chow/断点检验在 IC 自相关、异方差、多断点条件下只能作为低功效报告项，不能单独“确认 concept shift”，也不能直接决定当前 OOT 的模型或权重。
- 当前计划不使用 dynamic alpha、在线 Track B 或同一步模型切换；任何重新引入都必须重新立项、预注册，并通过与 S1 相同的审计。
- Step k 的预测必须先落盘并记录 `model_version`、`train_rows_hash`、`params_hash`、`feature_cutoff` 和 `label_cutoff`；Step k 标签成熟后只可用于评分、成熟 IC 状态机和后续 revalidation，不得影响任何未满足 label maturity、purge 和 embargo 的训练窗口。
- 任何同一步用 OOT 标签更新模型、alpha、阈值、early stopping 或特征选择的结果，直接标记为 leakage failure。

### 7.2 最小报告指标

模型指标：

- AUC，如是分类。
- RankIC。
- ICIR。
- top quantile precision。
- top-bottom decile spread。
- Newey-West HAC IC t-stat 和普通 t-stat 诊断值。
- block/bootstrap p-value 及 `block_days` 敏感性。
- feature importance / SHAP。
- best_iteration。

组合指标：

- 总收益。
- CAGR。
- 年化波动。
- Sharpe。
- Sortino。
- Calmar。
- 最大回撤。
- 回撤持续期。
- benchmark return。
- excess return。
- information ratio。
- beta。
- alpha。

交易指标：

- 单边和双边换手。
- 成本拖累。
- 成交失败率。
- 涨停买不到次数。
- 跌停卖不出次数。
- 平均持仓数。
- 参与率和容量。

稳定性：

- 分年度。
- 分月度。
- 牛/熊/震荡。
- 高/低波动。
- 高/低流动性。
- 大盘/小盘。
- 行业分组。
- 季度滚动 IC/RankIC 和告警状态。

因子衰减监控：

- 每个 keep 因子必须维护季度滚动 IC/RankIC。
- 每个 keep 因子报告 IC 衰减半衰期，定义为季度滚动 IC 从峰值下降到 50% 所需季度数。
- 半衰期 < 4 个季度标记高风险，4-8 个季度标记中风险，> 8 个季度标记低风险。
- 若连续 2 个季度 IC 符号反转或 t-stat 低于 1，标记为 yellow。
- 若连续 4 个季度失效、成本后贡献为负或容量恶化，标记为 red，并进入降权/暂停候选。
- 因子恢复必须重新通过同口径 walk-forward，而不是只看最近短期反弹。
- 半衰期是报告要求和风险提示，不单独作为 S1 hard gate。

### 7.3 过拟合审计

过拟合审计分层执行：

- 探索性单次实验可以先不计算完整 DSR/PBO，但状态只能是 `candidate`。
- 任何 `keep`、策略晋级、写入总纲、或声称存在 alpha 的结论，必须包含 Deflated Sharpe Ratio、独立 holdout 复核和参数扰动。
- 多策略、多参数、多模型搜索时，还必须增加 PBO 或同类 data-snooping 检验。

必须报告：

- Deflated Sharpe Ratio。
- Probability of Backtest Overfitting。
- White Reality Check 或同类 data snooping 检验。
- 最后 12 个月 holdout 窗口复核；12 vs 18 个月只可作为 S2 预注册敏感性实验，不得事后择优。
- `attempt_count`、测试族口径和候选数口径。
- `hypothesis_family_id`、`trial_index_in_family`、`total_trials_in_family`、`selection_path` 和 `pre_registered_or_exploratory`。
- `holdout_access_log.tsv`、`holdout_decision_count` 和 `holdout_burned_flag`。若 holdout 已多次参与策略选择，后续只能作为只读 benchmark，生产前必须新增 forward OOS 或 shadow period。
- holdout 不得参与调参、特征筛选、early stopping 或仓位阈值选择。



---

## 8. 回测引擎要求

### 8.1 两层回测

第一层：向量化研究。

- 因子 IC。
- 分层收益。
- Top-Bottom。
- 换手。
- 因子相关性。
- 中性化前后对比。

第二层：事件驱动组合回测。

- 目标权重转订单。
- T+1。
- 交易单位。
- 涨跌停、停牌、ST。
- 成交失败和延迟成交。
- 成本、滑点、冲击。
- 现金和持仓会计。
- 连续未成交订单队列、最长延迟、解锁后反转统计。
- 日频 L1 开盘冲击模型；L2/L3 需要更多成交阶段数据时必须标注为研究假设。

### 8.2 基准选择

默认：

- 全市场研究：`CN_A_ALL_EQW_PROXY`、`CN_A_ALL_MV_WEIGHTED_PROXY`。
- 大盘策略：`CSI_000300_OFFICIAL_AKSHARE`。
- 中盘策略：`CSI_000905_OFFICIAL_AKSHARE`。
- 小盘策略：`CSI_000852_OFFICIAL_AKSHARE`。

禁止：

- 使用旧同日成交额加权 proxy。
- 把当前指数成分倒灌为历史。
- 改 benchmark 来制造超额收益。

benchmark 审计补充要求：

- 每个 benchmark 必须报告 `coverage_assets` 的年度 min/median/max。
- `CN_A_ALL_EQW_PROXY` 和 `CN_A_ALL_MV_WEIGHTED_PROXY` 是内部代理，不等价官方可投资指数。
- 1990-2004 早期代理覆盖不足或市场结构差异较大，只能用于敏感性和历史背景，不支撑 keep。
- S1 主窗口从 2005-01-01 开始；即便如此，2005 年本地全 A 代理覆盖中位数约 1315，只能描述为“覆盖足以启动全市场代理研究”，不能写成 5000+。
- `benchmarks/STATUS.md` 是目录说明文件，不应被数据加载器当作 benchmark 表；是否删除属于仓库卫生项，不阻塞 S1。

---

## 9. 策略模块

### 9.1 S1：S1-M 正式主线 + S1-D 日频 sidecar 的 market-only 多因子框架

目标：回答当前 warehouse 下，月选股和日选股是否分别存在真实、成本后、可交易的 market-only 股票 alpha。

数据窗口：

- 主窗口：2005-01-01 至 2026-04-27。
- 可从 2000 年开始做敏感性检查，但早期市场结构和估值覆盖需单独标注。

track 定义：

| track_id | 主线 | 主标签 | 组合 cadence | 主风险 |
|---|---|---|---|---|
| `S1-M` | 月选股正式主线 | 20 日 forward excess/rank | 约 21 个交易日调仓，低换手持有到下次再平衡 | 月末集中成交、持仓拥挤、长持有期回撤 |
| `S1-D` | 日频探索/风控辅助 | 1 日和 5 日 forward excess/rank | 每日盘后候选、风险预警和离线执行审计；默认不主动调仓 | 高换手、成本拖累、涨跌停/停牌成交失败、短期噪声 |

`S1-M` 是近期唯一正式 alpha 主线；`S1-D` 是探索/风控 sidecar。二者必须各自有独立 `track_id`、calendar、label、orders audit、capacity report 和实验台账，不得把 `S1-D` 的 OOT/holdout 结果作为 `S1-M` 的选择依据。

模型顺序：

1. 单因子。
2. 等权打分。
3. ICIR 加权。
4. 训练窗 ICIR 排序后的 Gram-Schmidt 正交化复合因子。
5. Ridge / ElasticNet。
6. LightGBM。
7. LightGBM Ranker。

S1 启动前置条件：

| 项目 | 要求 | 阻塞级别 |
|---|---|---|
| 数据 manifest/source registry | `warehouse_build_manifest.json`、`external_data_sources.csv`、`DATA_USAGE_GUIDE.md`、`WAREHOUSE_README.md` hash 与实验登记一致 | P0，阻塞正式实验登记 |
| track registry | 固化 `S1-M` 和 `S1-D` 的 `track_id`、label、decision frequency、rebalance/sidecar status、holding period、execution rule 和 primary metric | P0，阻塞正式实验登记 |
| `universe_daily_construction_audit` | 完成公式、字段来源、PIT 输入、幸存者偏差、source gap 和脚本 hash 审计 | P0，阻塞 S1 主证据 |
| 三层 universe 审计 | 输出 research observable、entry eligible、execution accounting 三层样本数、重叠、剔除原因和风险样本保留情况 | P0，阻塞 S1 主证据 |
| walk-forward 日历生成 | 固化 S1-M/S1-D 主窗口起点、首个 OOT 起点、holdout 起点、全量 OOT step 数、每步训练截止日和 `walk_forward_calendar_hash` | P0，阻塞 S1 设计 |
| holdout access log | 建立 `holdout_access_log.tsv`，记录每次读取、报告、决策和污染状态 | P0，阻塞 holdout 作为最终验收 |
| valuation 缺口处理 | 生成缺口 mask，预注册 drop-gap/no-valuation/ffill 三口径敏感性 | P1，阻塞估值类因子 keep |
| 估值字段 PIT 分层 | 市值/股本/换手率与 PE/PB/PS/TTM 等财报派生字段分层，后者需公告日审计 | P1，阻塞 valuation/fundamental keep |
| 公司行为和复权审计 | 公司行为主表或 adjustment factor audit 至少用于 `return_adjusted_pit` sanity check | P1，阻塞 total-return accounting 声明 |
| benchmark 覆盖审计 | 报告每个 benchmark 的年度 `coverage_assets`；2005 前只作敏感性 | P1，阻塞超额收益 keep |
| ADV 新股不足标记 | 按 `amount` 计算 ADV 并标记有效成交日不足或上市 <20 日样本 | P1，阻塞容量结论 |
| validation 参数 hash | `validation_params.json` 版本、来源、`block_unit`、R5 指数衰减权重和告警规则与本文档一致 | P1，阻塞正式实验登记 |
| 指数衰减权重登记 | 固化等权对照、12 月默认半衰期、18 月敏感性、row-equal/date-balanced 权重公式和重训频率 | P1，阻塞正式实验登记 |
| concept shift 诊断 | 预注册切片、成熟 IC 状态机、检测指标和报告模板 | P1，随 S1 输出，不阻塞单轨强基线运行 |
| S1-D 日频 sidecar 执行审计 | 预注册 `S1-D_daily_risk_auxiliary_offline`、`daily_orders_audit`、`daily_turnover_capacity_report`、三层换手控制和成本 1x/2x/3x 敏感性 | P1，阻塞 S1-D 风控通道集成或主动调仓升级，不阻塞 S1-M |

S1 内置最小交易可行性，不能等到 S2：

- T+1、涨跌停、停牌、ST、上市年龄、100 股交易单位必须进入回测。
- 基础成本、保守滑点、开盘 L1 冲击必须进入成本后结果。
- 必须报告涨停买不到、跌停卖不出、连续锁死、成交失败率和解锁后反转。
- 至少报告 1000 万、5000 万、1 亿资金档；若 1 亿失效，应明确容量上限。
- S1-D 必须单独报告日换手、订单失败、短持有期离线持仓会计、成本 1x/2x/3x 敏感性和与 S1-M 的持仓重叠度。月选股通过 1 亿容量不代表日频 sidecar 也通过；未验证前不得触发主动调仓。

S1 完成门槛分三层：

Hard Gate（一票否决，必须全部通过）包含两个主门槛：统计 alpha 门槛和可执行 PnL 门槛。

统计 alpha 门槛：

- 至少 24 个 walk-forward OOT step，且原则上在最后 12 个月 holdout 窗口之前完成。
- 因子 PIT audit、split label audit、benchmark audit 通过。
- RankIC 或核心 IC 均值为正，且 Newey-West HAC 调整后的 t-stat >= 1.65 或 block bootstrap p-value < 0.10（满足其一即可）；若普通 t-stat 与 HAC/block bootstrap 结论冲突，采用更保守口径。
- holdout 为最后 12 个月，方向和主窗口一致，且 holdout Sharpe > 0。
- 候选因子 > 20 个且结果用于 keep/晋级时，FDR 校正后仍通过预注册显著性要求。

可执行 PnL 门槛：

- 成本后、容量后、订单失败后、benchmark 后超额收益为正。
- 最低可执行容量和成交失败不触发 fatal：1000 万资金档必须可解释，涨跌停/停牌导致的成交失败率不得吞噬主要 alpha。
- MaxDD、CVaR、`limit_lock_cvar` 和无法卖出暴露不触发预注册 fatal 条件。
- 订单状态机审计可以区分“模型没有 alpha”和“alpha 在成交层消失”。

Soft Floor（报告并评估，不满足需说明理由）：

- 年化双边换手 < 300%，除非策略明确被标注为高换手且容量/成本仍通过。
- 多数年份或多数市场状态不为单一窗口贡献。
- 相对线性和简单打分有稳定增量。
- 容量和稳定性切片覆盖 trailing ADV、参与率、成交失败、涨跌停压力和市值五档；市值五档按当日 PIT 市值截面 P20/P40/P60/P80 切分，只用于稳定性分析，不替代容量判断。
- 拥挤容量覆盖因子重叠、左尾、跌停未成交、市场成交额占比和风格去杠杆代理。

报告要求（记录不作为 S1 通过条件）：

- 尾部风险报告：Max Drawdown、VaR(95%)、CVaR(99%)、Sortino、Calmar。
- 分年度、分市场状态、分市值、分行业表现。
- 成交失败率、容量指标和各因子类别通过率。
- A 股制度性风险对照：涨跌停排除 IC 对比、注册制阶段分段表现、流动性枯竭日 IC/组合收益表现。科创板注册制、创业板注册制和全面注册制等阶段必须预先定义；2024-02 等极端窗口只能作为预注册压力切片，不得事后择优。
- Concept shift 诊断：预注册结构变化切片、滚动成熟 IC/因子收益、PSI/MMD 或等价分布漂移、因子拥挤度、等权 vs row-equal/date-balanced 指数衰减对照和分段描述性表现。Chow/ADWIN/Page-Hinkley/BOCPD 只能作为成熟序列上的报告项。诊断不放宽 S1 hard gate。
- 因子衰减半衰期和季度滚动 IC 风险等级。
- Exploratory Tracking：方向一致性定义为 24 个 OOT step 中 IC 符号与对应训练窗口 IC 符号相同的窗口数量 / 24 >= 65%，且最近 6 步中至少 4 步一致；冷却期 >= 6 个月，从因子首次进入 Exploratory Tracking 的日期起算，后续 walk-forward step 不重置；不入组合，完整记录并计入 `attempt_count`/候选数口径。冷却期满后，只有新增 OOT 证据仍满足最近 6 步至少 4 步方向一致时，才可重新进入 S1 candidate；否则转为 discard 或 archive tracking。重新进入时不得重置失败历史、FDR 口径或 `attempt_count`。

未通过 Hard Gate 的结果不得进入总纲收益结论，只能保留为 candidate、exploratory_track 或 discard。


### 9.1.5 S1.5：Concept Shift Resilience Protocol

目标：在 S1-M 正式强基线已经完成、可复现并通过主审计后，评估低复杂度时间衰减权重、结构性 regime 稳健性和拥挤容量是否能降低回撤、左尾和执行失败；S1-D 可作为风控 sidecar 参加 CSRP 验证。S1.5 不是替代训练轨，不改变当前 step 预测或仓位，不替代 S1-M 主证据，也不阻塞 S1 启动；但它阻塞“可部署策略”或“生产准备完成”的叙事。

候选方案：

- Equal-weight control：5 年 rolling 等权训练，必须始终保留。
- Row-equal exponential decay default：5 年 rolling，默认半衰期 12 个月，`row_equal_decay_weight = 2 ** (-age_trading_days / (half_life_months * 21))`，每个训练 step 内归一化到均值 1。
- Date-balanced exponential decay control：5 年 rolling，默认半衰期 12 个月，`date_balanced_decay_weight = date_weight_t / n_assets_t`，每个训练 step 内归一化到均值 1。
- Exponential decay sensitivity：18 个月为预注册敏感性；R10 的 6/24 个月为必报诊断，36 个月只能作为可选研究网格，进入 `attempt_count`，不得用 OOT/holdout 事后择优。
- Refit frequency：默认每 63 个交易日重训一次；S1-M 约 21 个交易日调仓/预测，S1-D 每日预测候选和风险告警但不默认每日重训；月度重训或每日重训只能作为预注册敏感性。
- Alert state machine：最近 6 个已成熟 OOT step 中至少 4 步 IC < 0 标记 yellow；连续 6 步 IC < 0 标记 red quarantine。状态机只冻结新 keep/晋级或触发 revalidation 报告，不直接改变当前 step 预测、仓位、阈值、特征或 early stopping。
- Dynamic IC turnover：R10 公式 `0.10 * min(max(0.5, trailing_matured_ic / 0.03), 1.5)` 只作为 Phase 2 report-only 或 tighten-only 诊断；输入必须是至少滞后一 step 的成熟 IC，验证前 `max_effective_cap <= 0.10`。
- Structural regime map：科创板注册制、创业板注册制、北交所、全面注册制、新国九条、2024Q1 量化拥挤压力和程序化交易监管作为预注册诊断/生产前审计段，不作为选模窗口。
- Crowding capacity panel：因子重叠、成交额占比、左尾 CVaR、跌停未成交、解锁反转、流动性枯竭和风格去杠杆代理。

禁止：

- 用当前 OOT 或 holdout 结果选择半衰期、重训频率、阈值、窗口、特征或 early stopping。
- 用当前 OOT 或 holdout 结果在 row-equal 与 date-balanced 之间择优。
- 用 Step k 尚未成熟的 label 训练任何会影响 Step k 或未满足 purge/embargo 的后续 step 的模型。
- 把 `p<0.05` 的 Chow 检验、ADWIN/Page-Hinkley/BOCPD 告警或 PSI/MMD 漂移写成 concept shift 已被确认；它们只能作为报告项和状态机辅助证据。
- 用人工主观判断覆盖状态机、keep、discard、quarantine 或 revalidation 规则；人工只能检查数据质量问题，不能改变策略结论。
- 恢复 Track A/B、动态 alpha、在线 Track B、anchored post-2023 keep 或 same-step label feedback。
- 把 stress slice 作为优化窗口。

S1.5 通过条件：

- 成本后主指标相对 equal-weight control 改善，且 12/18 月半衰期之间不存在明显不稳定或方向冲突。
- Row-equal 与 date-balanced 结论不存在“只靠近年股票数扩张才有效”的不可解释分叉。
- 在预注册 shift 切片中 MaxDD、CVaR、左尾或成交失败暴露改善，且非 shift 期没有不可接受恶化。
- 拥挤容量在 1000 万和 5000 万档通过；1 亿档若失败，必须给出真实容量上限。
- 通过与 S1 相同的 PIT、split label、benchmark、holdout、DSR/PBO、FDR、容量和交易约束审计。
- 模型版本、训练截止、标签截止、半衰期、重训锚点、参数 hash 和预测文件均可复现。


### 9.2 S2：交易可行性和容量压力测试

目标：在 S1 最小交易可行性通过后，深化真实可交易边界。S2 不再替代 S1 的成交约束；它只负责更精细的容量、分档滑点、冲击成本和组合约束优化。

必须覆盖：

- T+1。
- 涨跌停买卖失败。
- 停牌和无 bar。
- ST 和上市年龄。
- 成交额参与率。
- 手续费、印花税、过户费、规费、滑点、冲击。
- 资金规模敏感性。
- 开盘/非开盘分段滑点。
- 低/中/高流动性分档。
- 涨跌停压力和市场流动性枯竭日的额外惩罚。

S2 启动条件：

- S1 通过量化门槛。
- S1 报告中最小交易约束已经生效。
- 容量或成本是当前策略晋级的主要不确定性。

S2 通过条件：

- 1000 万、5000 万、1 亿资金档均给出参与率、成交失败率、成本拖累和容量上限。
- 若 1 亿档失效，不得按小资金收益外推。
- 分档滑点和冲击成本后仍保留可解释的成本后超额。

### 9.3 S3：市场状态与风险开关

目标：降低回撤和波动，不以提高收益为唯一目标。

候选变量：

- 中证300/500/1000 趋势。
- 全 A 等权和市值加权代理趋势。
- 全市场波动率。
- 市场宽度。
- 涨停、跌停、炸板压力。
- 成交额和换手。
- 小盘相对大盘强弱。
- Shibor、国债利率变化。

输出：

- 仓位开关 v1 候选：S3 研究前使用均匀权重（25/25/25/25）占位，S3 验证后替换为数据驱动的仓位比例。
- 因子权重倾斜。
- 风险熔断。

规则：

- 市场状态定义必须预注册，不能用全样本调参得到。
- 触发指标可包括指数趋势、市场宽度、全市场波动率、跌停压力、成交额枯竭和组合回撤。
- 熔断必须有冷却期和恢复条件。
- 风险开关必须在 walk-forward 中独立验证；若只降低收益不降低回撤或尾部风险，不得 keep。

### 9.4 S4：PIT 行业中性和行业轮动

目标：控制行业暴露并测试行业动量/拥挤是否有价值。

规则：

- 只用 `pit_industry_intervals_akshare`。
- 必须固定 `classification_standard_code`。
- 报告行业覆盖率、缺失率和退市证券映射率。
- 不使用 `current_industry_snapshot` 做历史回测。

### 9.5 S5：qant 小盘模型重审

目标：判断旧 qant 思路是否存在可救的真实增量。

要求：

- 使用 warehouse canonical 数据。
- 历史诊断可使用 `--purge-days 10` 对齐旧 10 日标签 deep dive。
- 新的正式证据使用 `purge_days >= max(label_horizon*3, 40)`。
- 禁止 naive random 作为最终证据。
- 必须复跑 split label audit。
- 对比 corrected chronological baseline，而不是 random 高收益。

优先检查：

- 标签定义是否符合真实交易目标。
- 132 特征是否经过未来信息筛选。
- 小盘池是否过度暴露流动性和风格。
- 成本和容量是否吞噬收益。
- RankIC 与组合收益是否一致。

### 9.6 S6：AkShare 外部低频数据

目标：补齐基本面、公司行为和风险事件，提升 robust 和可解释性。

接入顺序：

1. 公司行为、分红、送配。
2. 融资融券、北向资金、限售解禁。
3. ETF flows、市场宽度/涨跌停压力、股指期货 basis/OI。
4. 财报、业绩预告、业绩快报。
5. 股东户数、质押、龙虎榜、大宗交易。
6. 分析师预期修正和一致预期变化。
7. 公告、新闻和 NLP。

其中 2-3 项先做 source registration 和 candidate ETL，用于 concept shift、拥挤容量、风险开关和对冲成本研究；未通过 PIT、覆盖率、披露时点和 source gap 审计前，不得进入官方 S1 keep 或可部署结论。

任意接入必须先写 source registration，再写 ETL，再跑质量检查。

### 9.7 S7：筹码、涨停、分钟和期权储备

这些方向仅在对应表入仓并通过验证后进入 alpha 研究：

- `chip_daily`：筹码字段、时点、异常值、供应商算法解释。
- `limit_events`：当前仍是 candidate ETL；入仓后需区分盘后事件字段和盘中可见字段。
- `prices_minute` 和集合竞价/开盘成交明细：5min 优先，用于日选股执行优化、开盘冲击和盘中成交可行性；未入仓前 S1-D 只能使用日频 L1 保守执行，不能宣称开盘三段成交模型闭环。
- `option_minute`：P4 研究储备；合约、流动性、IV、Greeks、保证金、bid/ask 缺口说明。

---

## 10. AkShare 数据接入规范

### 10.1 抓取原则

- 全局 1 worker 起步。
- 慢接口串行，间隔 5-10 秒。
- 交易所日频接口整体不超过约 0.3 req/s。
- 失败指数退避重试 2-3 次。
- 中文参数使用 UTF-8 脚本或 Unicode escape。
- 每个源先 smoke test，再小窗口，再全量。

### 10.2 目标 schema

| 表 | 主键和核心字段 |
|---|---|
| `corporate_actions/dividend_allotment_events` | `asset_id, report_period, plan_announcement_date, registration_date, ex_right_dividend_date, cash_dividend, bonus_share, transfer_share, progress, available_at` |
| `financial_disclosures/earnings_quarterly` | `asset_id, report_period, announcement_date, eps, revenue, revenue_yoy, net_profit, net_profit_yoy, roe, gross_margin, available_at` |
| `margin_trading/equity_margin_detail_daily` | `asset_id, exchange, trade_date, margin_buy, margin_repay, margin_balance, short_sell_volume, short_balance_qty, short_balance_amount, available_at` |
| `northbound/stock_connect_holding_daily` | `asset_id, trade_date, holding_shares, holding_value, net_buy_value, available_at` |
| `fund_flows/etf_flow_daily` | `fund_id, trade_date, shares_outstanding, estimated_flow, nav, premium_discount, available_at` |
| `index_futures/basis_oi_daily` | `contract, trade_date, close, basis, open_interest, volume, roll_cost, available_at` |
| `market_breadth/breadth_limit_pressure_daily` | `trade_date, advancers, decliners, limit_up_count, limit_down_count, dry_up_flag, available_at` |
| `shareholder_structure/shareholder_households_quarterly` | `asset_id, stat_date, holders, holders_prev, holders_change_pct, avg_holding_qty, avg_holding_mv, announcement_date, available_at` |
| `risk_pressure/pledge_ratio_snapshot` | `asset_id, trade_date, pledge_ratio, pledged_shares, pledge_mv, pledge_count, available_at` |
| `event_supply/restricted_release_events` | `asset_id, release_date, release_shares, release_mv, holder_type, announcement_date, available_at` |
| `execution_audit/orders_audit` | `run_id, step_id, asset_id, trade_date, side, target_weight, intended_order_value, blocked_reason, filled_value, unfilled_value, delay_days, limit_lock_chain_length, unlock_date, post_unlock_return_1d/3d/5d` |

### 10.3 外部数据质量检查

必须检查：

- 主键唯一。
- `asset_id` 映射率。
- 非 A 股资产过滤。
- 公告日、统计日、可得日关系合理。
- 披露类特征至少 T+1 生效。
- 数值单位统一。
- 非负约束。
- 极端值。
- 覆盖率。
- 字段漂移。
- source URL 或 source name。

禁止使用“最新价”“当前排名”“当前状态”等快照字段回填历史。

---

## 11. 实验台账

所有实验记录到 `D:\quantum_a0\autoresearch_results.tsv` 或其扩展版。Git 项目中的正式策略维护应同步保留台账 schema。建议字段：

```tsv
run_id	track_id	label_id	calendar_id	panel_hash	execution_rule_id	baseline_run_id	hypothesis	commit	changed_files	warehouse_build_manifest_hash	source_registry_hash	walk_forward_calendar_hash	validation_params_hash	data_window	validation_mode	decision_frequency	rebalance_interval	holding_period	purge_days	validation_purge_days	embargo_days	validation_block_days	holdout_window	holdout_access_count	holdout_burned_flag	test_family_id	hypothesis_family	trial_index_in_family	total_trials_in_family	selection_path	pre_registered_or_exploratory	date_weighting_scheme	half_life_months	universe_rule_version	command	primary_metric	guardrails	attempt_count	total_return	CAGR	Sharpe	deflated_sharpe	pbo	max_drawdown	holdout_total_return	holdout_sharpe	holdout_max_drawdown	excess	turnover	cost_drag	capacity_tier	crowding_risk_score	limit_lock_cvar	execution_fail_rate	limit_up_buy_fail_count	limit_down_sell_fail_count	orders_audit_path	best_iteration_mean	rank_ic_mean	ic_t_stat	bootstrap_p	leak_audit_status	split_label_audit_status	pit_factor_audit_status	benchmark_audit_status	status	decision	notes
```

### 11.1 Keep 规则

只有同时满足以下条件才可 keep：

- 通过 leakage audit。
- 通过因子 PIT audit、split label audit 和 benchmark audit。
- 相对 corrected baseline 改善主指标。
- 回撤、换手、成本、容量不明显恶化。
- IC t-stat 或 block bootstrap p、最后 12 个月 holdout、FDR（如适用）和 Deflated Sharpe 满足预注册门槛。
- 年度表现不过度集中。
- 模型排序指标方向一致。
- 不依赖改变 benchmark、费用、股票池或窗口取胜。
- 不依赖 stress slice、holdout、多权重口径或近期股票数扩张择优取胜。
- 可执行 PnL 门槛通过，且 `orders_audit` 能解释成交层影响。
- 实现复杂度与收益改善匹配。

### 11.2 Discard 规则

直接 discard 或标记 inconclusive：

- 依赖 naive random uplift。
- purge/embargo 后失效。
- 标签跨 OOT 月。
- 只在弱基准短窗口有轻微相对收益但绝对收益为负。
- best_iteration 异常顶格且 OOS 无收益。
- 通过改变评估规则获得改善。
- 成本或容量敏感性不可接受。
- 未报告 `attempt_count` 或验证参数 hash。
- holdout 参与过调参、特征选择、early stopping 或阈值选择。
- 未报告 `test_family_id`、完整尝试次数、manifest hash、source registry hash 或 holdout access count。
- 只在 row-equal decay 下有效，date-balanced 对照显示收益来自近年股票数扩张且无法解释。
- 拥挤容量、limit-lock 左尾或订单失败 fatal。

---

## 12. Review 清单

提交给独立专家 review 前必须逐项自查：

### 12.1 数据

- 是否只使用 `D:\data\warehouse` canonical 表。
- 是否引用 `warehouse_build_manifest.json`、`external_data_sources.csv`、`validation_params.json` 和 `walk_forward_calendar_v1` hash。
- 每个字段是否有 source、`available_at`、`decision_time`。
- 缺 `source_status` 的核心字段是否已在 manifest 或 `source_status_audit` 中明确标记。
- 是否运行最新 `leakage_check`。
- 是否完成因子 PIT audit，尤其是估值、财报派生、市值、复权、行业和风险警示字段。
- 是否有重复键。
- 是否使用未来股票池、未来行业、未来 ST 或未来停牌。
- 是否披露外部源缺口。
- 三层 universe 是否分离，`research_observable_universe` 是否没有静默删除涨跌停/停牌风险样本。

### 12.2 标签和验证

- 标签 horizon 是否明确。
- purge 天数是否不小于 label horizon。
- 官方证据 purge 天数是否满足 `>= max(label_horizon*3, 40)`。
- embargo 是否为 10 个交易日，且 OOT step 是否不少于 24 个。
- OOT 边界是否无跨月/跨期 label。
- 是否使用 chronological walk-forward。
- 是否报告主窗口起点、首个 OOT 起点、holdout 起点、全量 OOT step 数和 24 步最低门槛的区别。
- 若有 random，是否 blocked + purge + embargo。
- 是否有 split label audit、真正 holdout、DSR/PBO 或等价过拟合审计。
- holdout 是否完全未参与调参、特征选择、early stopping 或阈值选择。
- 是否有 `holdout_access_log.tsv`、`holdout_access_count` 和 `holdout_burned_flag`。
- 若有指数衰减权重、半衰期敏感性或告警状态机，是否证明所有输入都在预测前已成熟，且当前 OOT/holdout 标签没有参与同一步选择、半衰期选择、权重口径选择、重训频率选择、early stopping 或阈值选择。
- Stress slice 是否只作预注册诊断和风险审计，没有用于选模、选阈值或晋级 keep。

### 12.3 回测

- 成交价是否来自未复权可成交价。
- 收益、动量、标签是否使用 PIT 复权收益。
- T+1、涨跌停、停牌、ST、上市年龄、交易单位是否处理。
- 成本、滑点、冲击和容量是否进入。
- 是否报告成交失败、连续锁死、解锁后反转、成本拖累和容量上限。
- 是否报告拥挤容量、factor overlap、左尾 CVaR、跌停未成交和市场成交额占比。
- 是否区分日频 L1 开盘冲击模型与尚未具备数据的集合竞价/分钟三段模型。

### 12.4 模型

- 是否先比较简单基线。
- 特征重要性是否集中在可疑字段。
- 参数扰动是否稳定。
- 是否存在调参后只展示最好窗口。
- 是否记录随机种子、命令、输出路径。
- 是否记录 `attempt_count`、参数文件 hash、依赖版本和代码提交。
- 是否记录 `test_family_id`、完整试验族大小、`selection_path`、`date_weighting_scheme` 和 `universe_rule_version`。

### 12.5 结果解释

- 是否同时报告模型指标和组合指标。
- 是否报告分年度、分市场状态。
- 是否避免承诺未经验证的收益。
- 是否明确 qant random 8/2 只是验证污染反例。
- 是否把审计报告中的收益路径只作为假设队列，而不是结论或承诺。
- 是否没有用人工主观判断覆盖状态机、keep、discard、quarantine 或 revalidation 规则。

---

## 13. 近期执行顺序

### Step 0：S1 启动前审计和日历固化

输出：

- `warehouse_build_manifest.json`、`external_data_sources.csv`、`validation_params.json` 和数据依据文档 hash。
- `track_registry_v1`：登记 `S1-M` 正式主线与 `S1-D` sidecar 的标签、决策频率、调仓/sidecar 状态、持有期、执行规则、容量规则和主指标。
- `universe_daily_construction_audit` 报告。
- 三层 universe 审计：research observable、entry eligible、execution accounting。
- walk-forward 日历：`walk_forward_calendar_S1M_v1` 和 `walk_forward_calendar_S1D_v1` 或带 `track_id` 的统一 `walk_forward_calendar_v1`；记录主窗口起点、首个 OOT 起点、holdout 起点、全量 OOT step 数、每步训练截止日、`step_id` 和参数 hash。
- `holdout_access_log.tsv` 和测试族台账 schema，必须包含 `track_id`、`label_id`、`calendar_id`、`panel_hash` 和 `execution_rule_id`。
- `source_status_audit_r7`：R7 已补齐核心表 `source_status`、估值字段 PIT tier 和 `security_master` 时点字段；后续重建后复跑。
- valuation 缺口处理方案：drop-gap、no-valuation、ffill 三口径实验登记。
- 公司行为/复权审计登记：没有独立公司行为表前，S1 只声明 adjusted-return proxy。
- benchmark 覆盖审计：年度 `coverage_assets` 和 2005 前敏感性标记。
- ADV 新股不足规则和 `block_unit=trading_days` 校验。
- R5/R10/CSRP 指数衰减权重登记：等权对照、row-equal/date-balanced、12 月默认、18 月预注册敏感性、6/24 月诊断、63 日重训锚点、成熟 IC 状态机、结构性 regime map、拥挤容量和参数 hash。
- S1-D sidecar 执行登记：`S1-D_daily_risk_auxiliary_offline`、`daily_orders_audit`、`daily_turnover_capacity_report`、三层换手控制、动态 IC report-only/tighten-only 规则、成本 1x/2x/3x 敏感性和短持有期离线持仓会计。

### Step 1：构建日频研究面板 v1

R7 当前状态：`features/market_daily_v1` 与 `labels/forward_returns_v1` 已入仓，各 15,420,654 行，覆盖 2005-2026；`feature_label_panel_v1_manifest.json`、`pit_feature_audit_market_daily_v1.json` 和 `label_audit_forward_returns_v1.json` 已生成并 PASS。后续 Step 1 的重点从“从零生成面板”转为复核面板 hash、补 S1-M walk-forward calendar 绑定、为 S1-D sidecar 预留独立 calendar/ledger、补 benchmark audit 和正式实验登记。

输入：

- 三层 universe 入仓产物或已登记、可复现、带 hash 的实验面板
- `prices_daily_returns`
- `valuation_daily` 的 market-derived 字段；财报派生字段只进单独 valuation/fundamental 分支
- `tradability_daily_enriched`
- `benchmarks`
- `reference_rates`
- `trading_costs`
- PIT 行业表

输出：

- `features/labels` 入仓表 hash 复核；实验缓存仅作中间产物，不能直接训练官方 S1。
- 字段覆盖率报告。
- 缺失和异常值报告。
- valuation 缺口 mask、`ffill_age`、forward-fill 敏感性输入。
- market-only baseline panel 与 valuation/fundamental candidate panel 分离。
- ADV 有效成交日数和 `adv_insufficient` 标记。
- `pit_factor_audit` 报告。
- Round 5/round2/r3/r4/r5/r6 参数和本地参数镜像 hash。
- `benchmark_audit` 报告。
- S1-M 面板绑定：20 日标签、月度调仓 calendar、月度组合规则和对应 hash。
- S1-D sidecar 面板绑定：1/5 日标签、日度 decision calendar、daily risk auxiliary schema、日度订单审计规则和对应 hash。

### Step 2：单因子和分层验证

输出：

- S1-M 输出正式 IC / RankIC / ICIR；S1-D 输出探索/风控辅助 IC / RankIC / ICIR，不得混成一个 S1 指标或用 S1-D 选择 S1-M。
- Newey-West HAC IC t-stat、普通 t-stat 诊断值和 block/bootstrap p-value；S1-D 先按日计算 IC，再按周/月汇总。
- 10/21/40 日 `block_days` 敏感性；S1-D 不得因 1 日标签而使用 1 日 block 作为唯一证据。
- Top-Bottom。
- 分年度稳定性。
- 季度滚动 IC 衰减监控。
- 涨跌停排除 IC、注册制阶段、流动性枯竭日切片。
- Concept shift 诊断：预注册结构变化切片、成熟 IC yellow/red 状态机、PSI/MMD 或等价分布漂移、拥挤容量指标、等权 vs row-equal/date-balanced 指数衰减对照和描述性分段报告。
- 因子相关性。
- 中性化前后对比。
- S1-D sidecar 额外输出：日度候选数量、日度行业/市值暴露、与 S1-M 候选重叠度、冲突买卖统计、短期反转风险和 risk alert 覆盖率。

### Step 3：保守组合基线

输出：

- `S1-M_monthly_rebalance_baseline`：20 日标签、月度调仓、等权、ICIR、线性、LightGBM/Ranker 对照。
- `S1-D_daily_risk_auxiliary_offline`：1/5 日标签、每日候选、risk signal、alert state、离线滚动组合模拟、等权、ICIR、线性基线；非线性模型只作后续对照，结果不进入 official keep。
- 成本后收益，按 S1-M 和 S1-D 离线 sidecar 分开报告；S1-D 仅作诊断。
- 成交失败、连续锁死和解锁后反转，按 S1-M 和 S1-D 离线 sidecar 分开报告。
- S1 最小容量：1000 万、5000 万、1 亿；月选股通过的容量不得自动转给日选股。
- `orders_audit` 或等价订单状态机产物；S1-D sidecar 必须有 `daily_orders_audit`，但独立 `limit_events` 未入仓前只能使用 close-based 代理字段。
- 拥挤容量、limit-lock CVaR 和成交额占比；S1-D sidecar 必须额外报告日换手、三层换手控制、成本 1x/2x/3x、日度参与率和未成交继续暴露。
- 资金规模敏感性。
- Deflated Sharpe、holdout 和 split label audit。

### Step 4：风险状态和组合约束

输出：

- S1.5 CSRP：等权 5 年、row-equal/date-balanced 12 月半衰期、18 月半衰期、R10 6/24 月诊断、可选 36 月研究网格、4/6 年训练窗口诊断、结构性 regime map、拥挤容量和 63 日重训频率对照。6/24/36 月网格和 4/6 年窗口只作研究记录，计入 `attempt_count`，不得进入 keep/晋级，不得替代 5 年单轨主证据。
- 风险开关报告。
- 回撤改善报告。
- S3 前 25/25/25/25 均匀权重占位和数据驱动仓位开关实验；100/60/30/0 只作为可选历史假设或挑战基线。
- 行业、市值、beta、换手约束对比。

### Step 5：公司行为和外部低频数据 ETL

公司行为、分红送配在 Phase A 期间可并行做最小 ETL，用于 total-return 和复权校验；作为 alpha 因子使用仍需等 source/available_at 审计通过。融资融券、北向、限售解禁、ETF flows、市场宽度/涨跌停压力和股指期货 basis/OI 先做 source registration 和 candidate ETL；未通过 PIT/覆盖率/缺口审计前不得进入 keep。其他外部低频数据只有当 Step 1-4 证明基线稳定，且 review 同意数据质量、合规和资源排期后启动；review 不得主观改变 keep/discard、模型切换、参数选择或告警处置。

输出：

- source registration。
- ETL 脚本。
- schema registry 增量。
- leakage check 增量。
- source gap report。

---


## 13.5 三方审计共识改进（2026-04-30）

### 新增验证项

1. **因子正交化流程**：单因子、等权和原始 ICIR 先作为基线；随后按训练窗口 ICIR 降序做 Gram-Schmidt 正交化，作为 ICIR 复合和 Ridge/ElasticNet 前的可复现对照分支，产物为正交化前后因子相关性矩阵、排序规则和覆盖率报告。
2. **regime断裂检测**：在 walk-forward 每个 OOT step 中单独报告 regime 断裂期表现，增加成熟 IC/因子收益的 yellow/red 状态机。IC 告警先只作为报告、quarantine 和重新验证触发；暂停交易、降权或减仓必须经 walk-forward 验证后才能成为实际规则。实时风险开关应优先使用 ex-ante 市场宽度、波动率、跌停压力和成交额等变量。
3. **尾部风险指标**：S1验证中增加VaR 95%、CVaR 99%、最大回撤持续期。
4. **多重检验校正**：候选因子>20个时，必须报告FDR校正后的显著性。
5. **季节性效应**：默认采用方案 B，即 5 年 walk-forward 训练窗口覆盖完整年度周期；S1 不默认加入月份哑变量，月份哑变量只能作为后续 S3 或敏感性分析的预注册候选。
6. **IC 自相关调整**：IC t-stat 默认使用 Newey-West HAC 调整；相邻 walk-forward step 的训练窗口重叠率按实际窗口计算并披露，不固定写死审计报告中的估算比例。
7. **A 股制度性风险对照**：S1 增加涨跌停排除 IC、注册制阶段和流动性枯竭日切片，所有压力窗口需预注册，不得用于事后择优。
8. **Concept Shift 诊断和 R5 衰减权重候选**：S1 输出成熟 IC 状态机、分段描述性表现、分布漂移和拥挤度诊断；S1.5 只评估等权 5 年、row-equal/date-balanced 指数衰减、半衰期敏感性和重训频率，不评估双轨、自适应 alpha 或在线 Track B。所有诊断严格滞后，当前 OOT 标签不得影响同一步预测。

### 因子库扩展

- P1阶段同步做3-5个另类数据源的 source registration 和 candidate ETL：北向资金净流入、融资余额变化率、限售解禁压力优先。
- 筹码数据ETL从P3提前到P1/P1.5并行执行，P2前完成可审计主表或明确放弃。
- 另类数据和筹码的 PIT、覆盖率、披露时点、映射率审计未通过前，只能标记为 candidate，不得进入官方 S1 keep。

### 深度模型降级

- 放弃PatchTST/TFT在Arc B390上的执行计划。
- 替代方案：轻量LSTM（hidden=64, 1层）或1D-CNN。
- 或定位为云端实验（Colab A100），本地只做推理。

### 容量测试前移

- S1阶段增加最简容量过滤：日均成交额>1000万。
- S1报告中包含基础容量指标：trailing ADV、持仓市值/日均成交额比值、参与率、成交失败率、涨跌停压力和市值分档 IC。
- 市值五档按当日 PIT 市值截面 P20/P40/P60/P80 切分，只用于稳定性切片；容量判断仍以 trailing ADV、参与率和成交失败率为主。
- 精细容量分析（分档滑点/冲击/参与率）保留在S2。

### 数据缺口影响量化（S1启动前必做）

| 对比实验 | 目的 | 预计耗时 |
|---------|------|---------|
| 有/无ST过滤的因子IC对比 | 量化ST PIT缺口影响 | 2小时 |
| 有/无停牌推断的可交易universe对比 | 量化停牌推断精度 | 1小时 |
| valuation缺口三口径（drop/no-valuation/ffill） | 验证2026估值缺口对估值因子和holdout的影响 | 2-4小时 |
| benchmark覆盖率分期审计 | 量化早期全A代理覆盖不足和2005主窗口合理性 | 1小时 |
| ADV新股不足标记检查 | 确认capacity报告不被新股异常成交额污染 | 1小时 |
| 不同embargo值（5/10/15）的OOT结果对比 | 敏感性报告，不择优；默认仍为 10 日 | 3小时 |
| purge敏感性（40/60/80日） | 验证隔离阈值稳健性，阻塞正式keep/晋级 | 8-16小时 |
| block bootstrap block敏感性（10/21/40日） | 验证 p-value 对 block_days 的稳健性，不得择优 | 2-4小时 |
| concept shift预注册诊断 | 输出成熟 IC 状态机、描述性分段、分布漂移、拥挤容量和等权 vs row-equal/date-balanced 指数衰减对照；不放宽S1 hard gate | 4-8小时 |

预备诊断的 24 步只作为最低验证规模和快速 smoke；完整 R5 主证据必须按交易日历生成全量 OOT step，单独估算耗时，不得用 24 步耗时代表最终 S1 全量运行成本。

## 14. 文档治理

Git 项目中的活跃文档只有两份：

- `quant_strategy_plan.md`：总纲。
- `quant_strategy_research_plan_detailed.md`：执行规范。

参考文档：

- `量化时间序列模型调研和选择.md`
- `量化策略设计调研与建议.md`

这些参考文档提供模型和方法论候选，但不覆盖本执行规范中的数据约束、验证约束和回测约束。

数据依据文档和机器可读参数也必须随 Git 同步维护：

- `DATA_USAGE_GUIDE.md`
- `WAREHOUSE_README.md`
- `external_data_sources.csv`
- `warehouse_build_manifest.json`
- `validation_params.json`

每轮专家 review 后，如有采纳意见，优先修改 Git 项目中的两份活跃策略文档和上述数据依据文档；`task_plan.md`、`findings.md`、`progress.md` 只作为本地工作区规划文件，不提交 Git。`D:\data\strategy\` 下旧副本不得与 Git 项目分叉维护。





