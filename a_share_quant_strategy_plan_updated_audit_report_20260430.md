# A股量化策略实验设计规划更新版独立审计报告

**审计日期**：2026-04-30
**审计对象**：`quant_strategy_plan.md`、`quant_strategy_research_plan_detailed.md` 及其数据依据文件
**重点问题**：concept shift 机制、俄乌/美伊等长期地缘冲击、月频与日频调仓路线、数据可落地性
**审计性质**：文档与数据治理审计、策略研究设计审计、落地可交易性审计；本轮未执行完整回测或重新构建本地仓库。

---

## 0. 被审计文件与版本指纹

本轮使用用户提供的更新版文件，文件名在本地为带 `(1)` 后缀的版本：

| 文件 | SHA256 前 16 位 | 审计用途 |
|---|---:|---|
| `quant_strategy_plan(1).md` | `0151cc76a2cf13d4` | 短总纲、研究路线、近期阶段目标 |
| `quant_strategy_research_plan_detailed(1).md` | `cfaa98155ed97d45` | 执行规范、验证参数、S1/S1.5/S2/S3 规则 |
| `DATA_USAGE_GUIDE(1).md` | `eaf5765738468f88` | 数据口径、warehouse 可用性、缺口说明 |
| `WAREHOUSE_README(1).md` | `d8cd958e419e7ff5` | 仓库结构、使用建议、剩余 source gap |
| `external_data_sources(1).csv` | `9138dbfb03612080` | 外部源登记与可用状态 |
| `validation_params(1).json` | `386e46541e5e423f` | 机器可读验证参数 |
| `warehouse_build_manifest.json` | `42583df79f7e81d9` | 单一事实源、构建与审计 hash |

`external_data_sources(1).csv` 当前共 29 行，其中 `available_now=9`、`candidate_etl=15`、`blocked_by_source_gap=4`、`missing=1`。这个结构比上一版更清晰，但也暴露出一个关键缺口：当前登记的数据源没有覆盖地缘冲突、海外能源、商品、美元/人民币、全球波动率和跨资产风险传导数据。

---

## 1. 总体审计结论

### 1.1 综合评分

我对更新版规划的专业可落地评分为：

> **8.2 / 10：可作为 A 股日频 market-only 研究体系的强启动版本；可启动 S1-M 正式研究；尚不宜直接宣称可部署策略；不建议立即把每日调仓升级为与月频同级的 alpha 主线。**

相比上一轮，更新版有明显进步：

1. **从“找收益曲线”转向“构建可审计研究体系”**。总纲和细则已经把 PIT、manifest/hash、leakage check、walk-forward calendar、holdout access log、测试族台账、attempt_count、Newey-West、block bootstrap、DSR/PBO/FDR、容量和订单失败都纳入强制框架。
2. **S1-M 与 S1-D 的定位更稳健**。新版明确 `S1-M` 是近期唯一正式 alpha 主线，`S1-D` 是日频探索/风控 sidecar，避免了“日频高噪声信号 + 高频换手 + 不完整执行数据”直接冲进收益结论。
3. **concept shift 的“防泄漏”层已经相当成熟**。文档禁止 same-step label feedback、禁止用当前 OOT/holdout/stress slice 选半衰期/阈值/特征，保留 5 年 rolling 等权控制组，并引入 row-equal/date-balanced decay 和成熟 IC 状态机，这是正确方向。
4. **数据事实与策略文档的单一事实源治理明显改善**。文档要求以 `warehouse_build_manifest.json` 和审计报告 hash 为准，不再把手工抄表当权威事实；这是可复现研究体系的关键。

但仍有四个必须修订的方向：

1. **concept shift 框架仍主要面向 A 股内部制度变化和量化拥挤，对外生地缘—能源—汇率—全球风险冲击覆盖不足。** 这在 2022 俄乌冲突、2026 美伊/中东冲突等长期冲击背景下是实质缺陷。
2. **日频 sidecar 目前不应升级为同级 alpha 主线，但应升级为“正式风控与执行主线”。** 换言之，建议形成“双主线”，但不是“两条 alpha 主线”，而是“月频 alpha 主线 + 日频风险/执行主线”。
3. **S1-D 的验证口径还需要独立强化。** 24 个 OOT step 对月频勉强是最低门槛，对日频不够；日频应要求至少 252/504 个成熟交易日、24 个自然月桶和 8 个季度桶，并报告日/周/月三套聚合口径。
4. **执行标签与真实成交标签需要进一步拆分。** 当前 forward adjusted return 标签适合 IC 研究，但如果执行是 T+1 开盘/分批成交，则应补充 execution-aligned labels，否则模型 alpha 与账户 PnL 会出现标签—执行错配。

---

## 2. 一页式核心审计意见

| 主题 | 当前设计状态 | 审计意见 | 优先级 |
|---|---|---|---|
| S1-M 月选股主线 | 20 日标签、约 21 交易日调仓、63 日重训、5 年 rolling | 设计合理，可作为第一条正式 alpha 主线 | P0 保持 |
| S1-D 日频通道 | 1/5 日标签、每日候选/风险预警、离线订单审计 | 不应立即成为 alpha 主线；建议升级为正式日频风险/执行主线 | P0 修订定位 |
| Concept shift | 5 年 rolling、12/18 月衰减、date-balanced、成熟 IC 告警、结构切片 | 对内部机制变化较好；缺少地缘/能源/汇率/全球波动率外生冲击层 | P0 增补 |
| 外部数据源 | 融资融券、北向、ETF flow、股指期货等已列候选 | 缺少 Brent/WTI、SC 原油、黄金、铜、DXY、USD/CNH、VIX/MOVE、UST、全球股指期货、地缘事件日历 | P0/P1 增补 |
| 日频验证 | 文档已有每日 IC、HAC、bootstrap、日换手和订单失败 | 需要独立日频最低样本门槛，不能沿用月频 24 step | P0 修订 |
| 执行模拟 | T+1、涨跌停、停牌、100 股、成本压力测试已经纳入 | 日频主动调仓若升级，必须等待分钟/集合竞价、limit_events 和真实开盘冲击数据 | P0 阻塞 |
| 数据治理 | manifest/hash、source status、PIT audit、label audit 已要求 | 应补充 external source registry 的 `vendor/license/update_sla/pit_tier/build_hash` 字段 | P1 |
| 成本模型 | 往返 0.206%、1x/2x/3x 敏感性 | 对小微盘和日频仍偏乐观，应引入压力日分档、冲击平方根模型和订单簿不可得惩罚 | P1 |
| Holdout | 最后 12 个月、access log | 若 2026 美伊冲突落在 holdout 内，不能用它调 GMSL 阈值；只能作最终审计或 shadow | P0 |
| 组合约束 | 行业、市值、beta、换手约束后置 | 建议 S1-M 就纳入最小行业/市值/流动性暴露报告，S1.5 才允许优化 | P1 |

---

## 3. 当前规划的主要优点

### 3.1 研究治理已经接近专业机构内部规范

新版总纲与详细规范最大优点是把“策略有效性证据”与“实验缓存、历史反例、旧模型结果”切开了。文档明确旧 `processed`、旧 qant cache、旧随机验证结果不作为策略有效性证据；正式研究必须依赖 canonical warehouse、manifest/hash、PIT audit、label audit 和 walk-forward calendar。这一点非常重要，因为 A 股日频多因子研究最常见的问题并不是模型不够复杂，而是：

- 股票池回填；
- 复权因子未来信息；
- 当前指数成分倒灌历史；
- 同日成交假设过于乐观；
- 未成熟标签进入训练；
- random split 造成横截面泄漏；
- holdout 被反复查看后仍声称未污染。

新版已经把这些问题大多写成硬规则。

### 3.2 S1-M 作为第一条正式 alpha 主线是正确选择

A 股日频股票策略在没有分钟/集合竞价/订单簿数据前，最适合先做 **20 日标签 + 月度或近似月度调仓**：

- 成本和滑点更可控；
- 信号半衰期与数据质量更匹配；
- T+1、涨跌停和停牌造成的订单失败对账户 PnL 的破坏相对小；
- 1/5 日标签的高噪声不会直接转化为高换手；
- 容量验证可以先用 trailing ADV、成交额分档和保守 close/open 代理完成第一轮。

月频主线并不意味着放弃日频信息，而是把日频信息放到风险预警、成交失败监控、alpha 衰减、异常流动性识别和候选池变化监控里，这正是当前 `S1-D` sidecar 的定位。

### 3.3 Concept shift 的反泄漏机制显著增强

新版 `S1.5 Concept Shift Resilience Protocol` 已经包含几个关键设计：

- 保留 5 年 rolling 等权控制组；
- 12 个月半衰期作为默认衰减候选；
- 18 个月作为预注册敏感性；
- 6/24 个月为必报诊断，36 个月仅作可选研究网格；
- row-equal 与 date-balanced decay 同时报告，防止近年股票数量扩张导致隐性双重加权；
- 成熟 OOT IC 状态机只触发 yellow/red 和 revalidation，不直接改当前仓位；
- 禁止用当前 OOT、holdout、stress slice 选模型、半衰期、阈值、特征或 early stopping；
- 禁止恢复 Track A/B、动态 alpha、在线 Track B、same-step label feedback。

这对 A 股 2023-2024 注册制、壳价值变化、量化拥挤、2024Q1 小微盘/量化踩踏等内部结构变化是有效的基础框架。

---

## 4. 关键问题一：Concept shift 仍需升级为“内部机制变化 + 外生宏观冲击”的双层框架

### 4.1 当前 CSRP 的覆盖边界

当前 CSRP 覆盖的是：

1. **A 股制度性变化**：科创板注册制、创业板注册制、北交所、全面注册制、新“国九条”、退市/壳价值变化。
2. **市场微结构变化**：程序化交易监管、量化拥挤、2024Q1 小微盘踩踏、流动性枯竭、涨跌停锁死。
3. **训练分布变化**：row-equal/date-balanced 权重、指数衰减、成熟 IC 状态机、PSI/MMD/断点类报告项。
4. **容量拥挤变化**：因子重叠、成交额占比、左尾 CVaR、跌停未成交、风格去杠杆代理。

这些都是必要的。但在我对新版文件和外部源登记的文本审计中，`俄乌`、`美伊`、`伊朗`、`Ukraine`、`Iran`、`Middle East`、`geopolitical`、`地缘`、`Brent`、`VIX`、`DXY`、`USDCNH`、`原油`、`商品` 等关键词在策略计划和 source registry 中均未出现。这说明当前 concept shift 体系仍没有把外生地缘冲击系统化纳入数据、报告和风控规则。

### 4.2 为什么这不是“普通压力测试”问题

俄乌冲突、美伊/中东冲突、能源运输受阻和全球制裁不是短期噪声，而是会改变定价逻辑的外生状态变量：

- 能源价格上行会改变 A 股行业利润分布：航空、交运、化工、炼化、公用事业、煤炭、石油、有色、黄金、军工、农业、肥料等板块的盈利敏感性不同。
- 美元、人民币汇率、外资流、港股、商品和全球风险偏好会影响 A 股估值因子、动量因子和小微盘流动性。
- 商品价格与通胀预期会改变利率路径和风险偏好，从而影响成长/价值、大盘/小盘、低估值/高估值的相对收益。
- 地缘冲击通常伴随波动率聚集和跨资产 spillover。此时传统 5 年 rolling 的平均规律可能滞后，短期 1/5 日风险 sidecar 反而更有价值。
- 若外生冲击长期存在，不能只把它作为单日 stress slice，而要把它作为“外生状态层”进入风险审计和生产前风控规则。

因此，当前 CSRP 应升级为：

> **CSRP = Internal Structural Shift Protocol + Geopolitical-Macro Shock Layer（GMSL）**

其中 CSRP 的原有部分继续处理 A 股内部机制变化；新增 GMSL 专门处理外生地缘—能源—汇率—全球风险冲击。

---

## 5. 建议新增：Geopolitical-Macro Shock Layer（GMSL）

### 5.1 GMSL 的定位

GMSL 不应在 S1 阶段直接成为 alpha 特征选择或择时调仓工具。它应先作为：

1. **S1 报告项**：报告外生冲击状态下 IC、RankIC、组合收益、成交失败、行业暴露、容量和左尾风险。
2. **S1.5 生产前审计门槛**：任何“可部署策略”叙事前必须通过 GMSL stress audit。
3. **S3 风控候选**：通过验证后才允许转成仓位、换手、参与率、行业暴露或 no-buy/no-add 风控规则。
4. **早期只能 tighten-only**：未验证前只允许降低风险，不允许因为 GMSL 信号而提高净敞口、放大杠杆、提高日换手或加大单一行业暴露。

### 5.2 建议写入文档的 GMSL 条款

建议在 `quant_strategy_research_plan_detailed.md` 的 S1.5 后新增：

```text
### 9.1.6 Geopolitical-Macro Shock Layer（GMSL）

GMSL 目标是识别外生地缘、能源、汇率、全球风险偏好和跨资产波动冲击对 A 股 alpha、执行和容量的影响。GMSL 不是 S1 alpha 主线，不得用当前 OOT、holdout 或 stress slice 选择模型、阈值、半衰期、特征或仓位规则。

GMSL 在 S1 阶段只作为报告项；S1.5 阶段作为生产前审计；S3 以后若通过 walk-forward、holdout、成本和容量审计，才可转成 tighten-only 风控规则。未通过验证前，GMSL 不得增加净敞口、杠杆、单票权重、日换手或行业集中度。
```

### 5.3 GMSL 最小数据面板

建议在 `external_data_sources.csv` 增加以下 source registry 行，并设为 `candidate_etl` 或 `planned_p1_5`，其中核心市场变量应尽量提前到 P1.5：

| 数据组 | 最小字段 | 用途 | available_at 规则 |
|---|---|---|---|
| 能源 | Brent、WTI、SC 原油、成品油或能源指数，1/5/20 日收益、20 日波动 | 油价冲击、输入成本、通胀压力 | 海外市场未收盘的数据不得用于当日 A 股盘后决策；中国夜盘需定义会话截止 |
| 贵金属 | 黄金、白银 | 避险、通胀、真实利率代理 | 只使用 decision_time 前已完成报价 |
| 工业金属 | 铜、铝、锌、铁矿石 | 全球需求、制造业链条、周期风格 | 同上 |
| 农产品/化肥 | 豆粕、玉米、尿素、化肥价格代理 | 农业、食品、化肥链条冲击 | 同上 |
| 汇率 | USD/CNH、USD/CNY 中间价、DXY | 外资风险偏好、输入通胀、人民币资产重定价 | 中间价按官方发布时间；CNH 按可得报价截止 |
| 全球利率 | UST 2Y/10Y、Fed funds 预期、中国 10Y 国债 | 利率冲击、成长/价值切换 | 海外收盘和时区严格处理 |
| 波动率 | VIX、MOVE、海外股指波动率 | 全球 risk-off | 只使用已收盘或已可见数据 |
| 全球股指/期货 | S&P 500、Nasdaq、MSCI EM、恒生、恒科、A50/HSI 期货 | 全球权益风险和港股联动 | 对夜盘/隔夜信息做严格时点切分 |
| 国内期货 | 股指期货 basis/OI、商品期货主力、夜盘状态 | 对冲成本、风格和商品链条风险 | 主力映射和夜盘归属需 PIT |
| 地缘事件日历 | 俄乌、中东、美伊、红海、制裁、航运中断 | 预注册 stress slice，不作选模窗口 | 事件日历只用于事后分段报告，不能作为未来预测标签 |

### 5.4 GMSL 状态定义

建议先使用低复杂度、可审计、无标签的 shock state：

```text
oil_shock = Brent_5d_return > +10% OR Brent_20d_return > +20% OR Brent_vol_20d in top 5%
fx_shock = abs(USDCNH_5d_return) > pre_registered_threshold OR USDCNH_vol_20d in top 5%
global_risk_off = VIX_5d_change > threshold OR MSCI_EM/SPX/HSI drawdown_5d < threshold
rate_shock = UST10Y_5d_change > threshold OR China10Y_5d_change > threshold
commodity_shock = commodity_basket_20d_return or vol in top 5%
geopolitical_event_window = pre_registered_event_date +/- {1,5,20} trading days
```

阈值应只在训练窗口内部预注册，不允许用当前 OOT/holdout 调参。S1 阶段可使用历史分位阈值，例如训练窗口 top 5%/10%，但必须在每个 walk-forward step 内按 `train_end` 之前的数据计算，不能全样本归一化。

### 5.5 GMSL 报告指标

每个 S1/S1.5 报告应增加：

| 指标 | 说明 |
|---|---|
| Shock-state IC/RIC | 分 `oil_shock/fx_shock/global_risk_off/rate_shock/commodity_shock` 的 IC、RankIC、ICIR |
| Shock-state PnL | 各冲击状态下成本后收益、超额收益、胜率、回撤 |
| 左尾 | shock-state VaR、CVaR、max drawdown、limit-lock CVaR |
| 成交 | shock-state 成交失败率、涨跌停未成交、停牌延迟、ADV 参与率 |
| 风格 | shock-state 下市值、beta、波动率、动量、估值、流动性暴露 |
| 行业 | 能源链、航空、交运、化工、煤炭、黄金、有色、军工、公用事业等行业暴露和收益 |
| 跨资产 | 油、金、铜、USD/CNH、VIX、全球股指与组合收益的相关/条件相关 |
| 策略稳定性 | shock vs non-shock 的 IC 符号一致性、收益差异、容量差异 |
| 风险响应 | 若 future S3 开启 tighten-only 规则，必须报告触发次数、错杀收益、避免回撤、交易成本变化 |

---

## 6. 关键问题二：月频与日频是否应转成“双主线”

### 6.1 结论：建议“双主线”，但不是“两条 alpha 主线”

我不建议现在把 `S1-D` 升级为与 `S1-M` 同级的正式 alpha 主线。更合理的设计是：

| 主线 | 定位 | 是否进入 alpha keep | 是否允许主动调仓 | 当前建议 |
|---|---|---:|---:|---|
| `S1-M` | 月频选股 alpha 主线 | 是 | 是，按月/21 日 | 保持正式主线 |
| `S1-R` 或 `S1-D-Risk` | 日频风险与执行主线 | 否 | 初期只允许 tighten-only 或报告 | 建议从 sidecar 升级为正式风控/执行主线 |
| `S2-D` 或 `S1-D+` | 日频 alpha 候选 | 仅在满足额外门槛后 | 小资金、小权重、严格限换手 | 后置，不进入当前 S1 keep |

也就是说，应把当前 `S1-D` 从“探索 sidecar”提升为 **正式的日频风险与执行主线**，但不能提升为 **正式日频 alpha 主线**。

### 6.2 为什么不建议立即转成两条 alpha 主线

日频主动调仓在 A 股会显著放大以下风险：

1. **标签噪声高**：1 日标签的横截面排序噪声远大于 20 日标签，IC 的经济含义更容易被微结构噪音、开盘跳空、涨跌停和短期资金流掩盖。
2. **交易成本极敏感**：单边日换手 10% 上限看似严格，但若每日滚动调仓，往返成本、滑点和冲击成本可能迅速吞噬 alpha。
3. **执行数据不足**：当前分钟、集合竞价、limit_events、真实开盘冲击、订单簿和更精细的成交失败数据尚未形成可审计 warehouse 主表。仅用 close-based 代理难以支持日频主动调仓的真实 PnL 结论。
4. **T+1 与涨跌停错配**：日频模型想买的票可能涨停买不到，想卖的票可能跌停卖不出；未成交继续暴露在日频策略中会显著改变收益分布。
5. **容量和拥挤风险更高**：A 股短期 alpha 更容易拥挤；2024Q1 事件说明量化拥挤会在小微盘和流动性压力下形成左尾踩踏。
6. **监管和操作风险更高**：程序化交易监管趋严后，日频高换手、订单频率和异常交易监控都需要纳入生产约束。

### 6.3 月频方案需要的小修订

当前 S1-M 设计合理，但建议补充三点：

#### 6.3.1 固定月末调仓 vs 21 交易日滚动调仓

“约 21 个交易日调仓”适合建模，但实盘中有两个不同语义：

- **固定月末/月初调仓**：更接近真实组合管理和基金月度申赎/风格暴露管理。
- **每 21 个交易日滚动调仓**：更均匀，但会逐渐漂移，不一定对应月末流动性、指数调整、机构换仓等效应。

建议默认：

```text
S1-M default rebalance_calendar = fixed_month_end_or_first_trading_day_after_month_end
S1-M sensitivity = every_21_trading_days_rolling
```

报告必须比较固定月度与 21 日滚动的收益、换手、成交失败和容量。若两者方向冲突，不得直接 keep，只能标为 candidate 或 inconclusive。

#### 6.3.2 月频执行应包含 1/3/5 日分批成交

文档已有分批执行敏感性，建议把它提升为 S1-M 默认必报：

```text
execution_plan:
  single_day_T1_open_or_vwap_proxy
  split_3_days_equal
  split_5_days_equal
```

若单日执行显著优于分批执行，需检查是否依赖开盘价乐观假设或流动性压力低估。

#### 6.3.3 月频组合应明确“持有期重叠”会计

如果每 21 日调仓但模型 63 日重训，预测之间使用冻结模型，则必须记录：

- `model_version`
- `prediction_date`
- `rebalance_date`
- `holding_period_start/end`
- `rebalance_reason`
- `unfilled_order_carryover`
- `residual_position_from_failed_orders`

否则涨跌停/停牌未成交会让月频组合实际持仓偏离目标持仓。

### 6.4 日频方案的合理升级路径

建议把 `S1-D` 拆成四级：

#### D0：当前离线 sidecar

- 输出日度候选分数、risk_signal、alert_state；
- 做每日 IC、周/月汇总、alpha 衰减、订单失败、turnover/capacity；
- 不进入 official keep；
- 不改变真实仓位。

这是当前文档基本定位，应保留。

#### D1：正式日频风险/执行主线（建议近期新增）

允许：

- 冻结新增买入；
- 推迟月频再平衡；
- 降低参与率；
- 降低总仓位或单票上限；
- 对涨跌停/流动性枯竭/外生 shock state 做 tighten-only 风控；
- 对 S1-M 持仓做红黄灯报告。

禁止：

- 因日频信号新增 alpha 仓位；
- 因日频信号提高净敞口；
- 因日频信号提高单票权重、行业集中度或换手上限；
- 使用未成熟标签更新当前模型或阈值。

D1 是我建议的“第二主线”：它是正式生产风险主线，而不是正式收益主线。

#### D2：日频 alpha 小仓位候选

只有满足以下条件，才允许作为 `S2-D` 或 `S1-D+` 小仓位候选：

| 条件 | 最低要求 |
|---|---|
| 数据 | 分钟/集合竞价、limit_events、真实开盘/成交代理、融资融券/北向/期货 basis 等关键数据完成 PIT 审计 |
| 样本 | 至少 504 个成熟日度 OOT 决策日，至少 24 个自然月桶和 8 个季度桶 |
| 统计 | 日度 IC/RIC 通过 HAC、block bootstrap 和月桶/季桶稳健性 |
| 成本 | 成本 1x/2x/3x 后仍有正超额，压力日不崩 |
| 容量 | 1000 万和 5000 万通过；1 亿失败时明确容量上限 |
| 换手 | 重叠率 >=85%、单票日变动 <=2%、单边日换手 <=10%，且 3x 成本后仍可接受 |
| 风控 | 不恶化 S1-M 的 MaxDD、CVaR、成交失败和行业集中 |
| 独立性 | 独立 calendar、holdout、attempt_count、test_family_id；不得借用 S1-M 的成功结论 |
| 合规 | 程序化交易报备、订单频率、撤单率、异常交易监控纳入模拟和生产约束 |

#### D3：独立日频 alpha 产品

只有 D2 连续通过多个年度、多个 market regime、真实 shadow/paper trading 后，才考虑独立产品化。当前不应写入近期路线。

---

## 7. S1-D 日频验证的具体修订建议

### 7.1 不要把 24 个 OOT step 当作日频验证充分样本

当前文档已提醒 “S1-D 报告时按交易日和周/月汇总同时披露，不能把 24 步写成全量日频风控验证”。建议进一步写成硬性门槛：

```text
S1-D daily risk/execution mainline minimum evidence:
- matured_daily_decision_days >= 252 for report-only risk monitoring
- matured_daily_decision_days >= 504 for any tighten-only production rule
- calendar_month_bins >= 24
- calendar_quarter_bins >= 8
- each monthly bin reports IC mean, IC sign, turnover, failed order rate, cost drag
- daily IC can be reported, but keep/promotion decisions use monthly/quarterly aggregated evidence
```

### 7.2 日频 block bootstrap 不应退化为 1 日

即使 1 日标签本身 horizon=1，日频策略的持仓、未成交暴露和市场状态有强自相关。因此建议：

```text
S1-D block bootstrap:
- default block_days = 21
- sensitivity = 5 / 10 / 21 / 40
- promotion uses the most conservative conclusion among 10/21/40
```

### 7.3 日频目标字段命名要防止误用

当前 `S1-D_daily_risk_auxiliary_offline` 输出允许 `target_weight` 作为离线模拟字段。建议重命名为：

```text
offline_sim_target_weight
```

并禁止出现在任何生产订单接口中。若未来 D1/D2 需要生产字段，应另建：

```text
risk_overlay_action
risk_overlay_reason
max_allowed_participation
no_buy_flag
defer_rebalance_flag
reduce_only_flag
```

这样可以避免 sidecar 输出被误接成真实交易目标仓位。

---

## 8. 执行标签与收益标签的错配问题

### 8.1 当前标签适合 IC，但不完全适合账户 PnL

当前 `labels/forward_returns_v1` 覆盖 1/5/10/20 日 forward adjusted return、超额、rank/top decile 标签，适合做因子 IC 和排序研究。但若真实策略是：

- T 日盘后出信号；
- T+1 开盘、VWAP 或分批成交；
- 遇涨停买不到、跌停卖不出、停牌延迟；
- 未成交订单继续暴露；

那么 **close-to-close adjusted return 标签不等于可交易账户收益**。

建议新增 execution-aligned label/audit，而不是替代原标签：

| 标签/会计 | 用途 |
|---|---|
| `forward_ret_20d_close_to_close_adjusted` | 因子 IC、历史 alpha 研究 |
| `exec_ret_20d_t1_open_to_next_rebalance` | 月频执行收益主口径 |
| `exec_ret_20d_t1_split_3d` | 分批执行敏感性 |
| `exec_ret_5d_t1_open_or_proxy` | S1-D 短期执行审计 |
| `failed_order_carryover_return` | 涨跌停/停牌未成交后的真实暴露 |
| `unfilled_sell_drawdown` | 跌停卖不出和连续锁死损失 |
| `unlock_reversal_1d/3d/5d` | 解锁后反转风险 |

这些标签或会计字段不一定都要进入模型训练，但必须进入组合 PnL 审计。

---

## 9. 数据改进建议

### 9.1 P0/P1 新增外生冲击数据

当前 source registry 中没有地缘宏观冲击层。建议新增以下行：

| source_name | availability_bucket | status | fields | available_at_required | notes |
|---|---|---|---|---|---|
| `global_energy_prices_p1_5` | `candidate_etl` | `planned_p1_5` | Brent, WTI, SC crude, energy index, returns, vol | yes | GMSL oil shock; overseas close/timezone audit required |
| `global_fx_rates_p1_5` | `candidate_etl` | `planned_p1_5` | USD/CNH, USD/CNY fixing, DXY | yes | FX shock and imported inflation |
| `global_volatility_indices_p1_5` | `candidate_etl` | `planned_p1_5` | VIX, MOVE, global equity vol proxies | yes | global risk-off |
| `global_rates_p1_5` | `candidate_etl` | `planned_p1_5` | UST2Y/10Y, China 10Y, yield changes | yes | rate shock and style rotation |
| `commodity_metals_agri_p1_5` | `candidate_etl` | `planned_p1_5` | gold, copper, aluminum, iron ore, agriculture/fertilizer proxies | yes | commodity chain and inflation shock |
| `global_equity_futures_p1_5` | `candidate_etl` | `planned_p1_5` | SPX/Nasdaq/MSCI EM/HSI/HSTECH/A50 futures | yes | global equity risk |
| `geopolitical_event_calendar_p2` | `candidate_etl` | `planned_p2` | pre-registered event windows | yes | only for stress reporting; not model selection |

### 9.2 A 股落地数据仍需优先补齐

现有文档已经列出很多缺口，我建议按策略价值重新排序：

#### P0：阻塞正式 S1 训练或部署叙事

1. `walk_forward_calendar_v1.parquet`
2. `holdout_access_log.tsv`
3. 测试族台账与 `attempt_count`
4. `benchmark_audit`
5. `orders_audit`
6. `daily_orders_audit` 与 `daily_turnover_capacity_report`
7. `valuation_gap_mask` 与 drop/no-valuation/ffill 三口径敏感性
8. `execution_label_audit` 或 `execution_pnl_accounting`

#### P1：阻塞日频升级、基本面增强或可部署叙事

1. 独立公司行为/分红送配/除权除息主表；
2. 完整官方/授权停复牌；
3. 沪/北历史 ST、摘帽、摘星；
4. 历史 PIT 指数成分和权重；
5. 分钟/集合竞价/开盘成交数据；
6. limit event 主表；
7. 融资融券、北向、ETF flow、股指期货 basis/OI；
8. 市场宽度、涨跌停压力、limit-lock 状态；
9. GMSL 外生冲击数据。

#### P2：增强 alpha 或解释力

1. 财报公告日与基本面 PIT；
2. 股东户数、质押、龙虎榜、大宗交易；
3. 新闻公告和事件数据；
4. 分析师预期；
5. 期权分钟数据。

### 9.3 source registry 字段建议扩展

`external_data_sources.csv` 当前字段为：

```text
source_name, availability_bucket, status, fields, available_at_required, notes
```

建议扩展为：

```text
source_name
availability_bucket
status
fields
available_at_required
source_vendor
license_status
raw_location
warehouse_table
pit_tier
time_zone
session_cutoff_rule
build_script
schema_hash
quality_report
coverage_start
coverage_end
update_sla
known_gaps
usage_allowed_stage
notes
```

尤其是 `time_zone`、`session_cutoff_rule`、`pit_tier` 对 GMSL 很关键。海外资产数据如果未处理时区，极容易把美股/原油夜盘的未来信息倒灌到 A 股 T 日盘后信号中。

---

## 10. 验证参数与实现细节修订

### 10.1 purge 参数命名有误用风险

`validation_params.json` 中同时有 `purge_days=40` 和 `purge_multiplier=3`。文档写的是：

```text
purge >= max(label_horizon * 3, 40)
```

建议机器参数中不要用 `purge_days` 作为固定字段，改成：

```json
{
  "base_purge_days": 40,
  "purge_multiplier": 3,
  "computed_purge_days_rule": "max(label_horizon_trading_days * purge_multiplier, base_purge_days)"
}
```

并在生成 `walk_forward_calendar_v1` 时逐 horizon 明确：

| horizon | computed purge |
|---:|---:|
| 1 | 40 |
| 5 | 40 |
| 10 | 40 |
| 20 | 60 |

否则 20 日标签可能被错误地只 purge 40 日，而文档要求应是 60 日。

### 10.2 dynamic IC turnover 公式仍需消歧

文档写道：

```text
0.10 * min(max(0.5, trailing_matured_ic / 0.03), 1.5)
```

同时又写验证前 `max_effective_cap <= 0.10`，且仅 report-only 或 tighten-only。这个公式在 trailing IC 较高时会给出 15% 上限，容易被实现者误用。建议改成：

```text
pre_validation_effective_turnover_cap =
    min(0.10, 0.10 * min(max(0.5, trailing_matured_ic / 0.03), 1.5))

If trailing_matured_ic <= 0:
    cap_tighten_only = min(current_cap, pre_registered_lower_cap)
If trailing_matured_ic > 0:
    no loosening before S3 validation
```

并明确：S1/S1.5 阶段该公式不能放宽换手，只能作为报告或收紧上限。

### 10.3 Holdout 通过条件不应只看 Sharpe > 0

当前 holdout 至少方向一致且 Sharpe > 0 是很低的下限。建议增加：

```text
holdout_minimum:
- excess_return_after_cost > 0
- Sharpe > 0
- max_drawdown not materially worse than benchmark or equal-weight control
- CVaR(99%) not materially worse than equal-weight control
- no single month accounts for > 50% of holdout profit
- order failure/cost/capacity within pre-registered bounds
```

如果 holdout 包含大型地缘冲击（例如 2026 美伊/中东冲击），不能在看完 holdout 后调 GMSL 阈值或行业规则；只能形成下一轮预注册规则。

### 10.4 IC 门槛应避免过硬的经验值误杀

如果文档或机器参数中存在 `RankIC >= 0.06` 类字段，建议将其标记为“参考目标”而非一票否决。A 股大样本横截面因子，长期 RankIC 0.03 已可能有经济价值，0.06 通常是很强的信号。更合理的硬门槛应以：

- HAC t-stat；
- block bootstrap p；
- 成本后可执行 PnL；
- 多年度/多状态稳定性；
- capacity/cost/turnover；
- DSR/PBO/FDR；

共同判断，而不是单一 IC 绝对数。

---

## 11. 组合构建与风险控制建议

### 11.1 S1-M 先做稳健低复杂度组合

第一阶段不建议复杂优化器过早介入。推荐顺序：

1. 等权 Top-N；
2. score-weighted Top-N；
3. 行业/市值/beta 中性化后的 Top-N；
4. 简单风险预算；
5. shrinkage covariance + robust optimizer；
6. 加入 CVaR/turnover/liquidity 约束。

### 11.2 最小组合约束应前置到 S1 报告

即使不做优化，也应报告：

- 行业暴露；
- 市值分层暴露；
- beta 暴露；
- 波动率暴露；
- 流动性分层；
- ST/退市风险暴露；
- 涨跌停压力暴露；
- 单票权重与前十大集中度；
- 与 benchmark 和中证 500/1000/2000 代理的风格偏差。

### 11.3 强制平仓和赎回压力模拟

2024Q1 量化踩踏说明，组合风险不只是日常 alpha 衰减，还包括“多人同向、流动性下降、赎回、限售/限价约束”叠加。建议加入：

```text
forced_deleveraging_stress:
- reduce gross exposure by 20/40/60% over 1/3/5 trading days
- sell orders blocked by limit_down/suspension
- unfilled exposure carried forward
- market impact multiplied by 2x/3x
- report liquidation shortfall, residual risk, CVaR, and drawdown
```

对日频策略尤其重要。

---

## 12. 针对高收益与低风险目标的实际路线

### 12.1 不要在 S1 阶段追求高收益叙事

当前规划的正确目标应是：

1. 证明数据和验证框架可信；
2. 证明 market-only 因子有稳定成本后边际价值；
3. 证明执行和容量不把 alpha 吃掉；
4. 证明 concept shift 和拥挤不会造成不可接受左尾；
5. 在此基础上逐步引入外部数据和更复杂模型。

如果 S1-M 的绝对收益不高但稳定、低回撤、低换手、容量好，应优先保留；如果 S1-D 日频收益高但依赖 close-based 执行、1 日标签和低估成本，应先降级为探索。

### 12.2 未来真正提高收益的优先方向

| 方向 | 预期价值 | 前置条件 |
|---|---|---|
| 市场宽度/涨跌停压力 | 提升风控和左尾控制 | limit pressure 数据入仓 |
| 融资融券/北向/ETF flow | 改善资金流与风险偏好判断 | PIT ETL 与 available_at |
| 股指期货 basis/OI | 风格、对冲成本、风险偏好 | 主力映射和夜盘时点 |
| 分钟/集合竞价 | 改善执行、日频策略验证 | 高质量分钟数据与订单模拟 |
| GMSL 外生冲击层 | 降低能源/汇率/全球风险冲击下左尾 | 全球宏观/商品/FX/vol 数据 |
| 公司行为/total return | 提升收益会计可信度 | 独立 corporate action 主表 |
| 基本面公告 PIT | 中长期 alpha 增强 | 公告日与供应商时点审计 |

---

## 13. 建议直接修改的文档条款

### 13.1 总纲中新增“双主线”表述

建议把“第一阶段采用一条正式主线 + 一个日频探索/风控 sidecar”修改为：

```text
第一阶段采用“月频 alpha 主线 + 日频风险/执行主线”的双主线治理，但只有 S1-M 是近期正式 alpha keep 主线。S1-R/S1-D 负责短期 IC、alpha 衰减、风险预警、订单失败、流动性、GMSL 外生冲击和执行审计；未通过独立 walk-forward、成本、容量、分钟/集合竞价与 holdout 审计前，不得升级为主动日频 alpha 主线。
```

### 13.2 详细规范中新增日频升级门槛

```text
S1-D promotion gate:
- report-only: matured_daily_days >= 252, month_bins >= 12
- tighten-only production: matured_daily_days >= 504, month_bins >= 24, quarter_bins >= 8
- alpha sleeve: requires audited minute/auction/limit_events, independent holdout, costs 1x/2x/3x pass, capacity >= 50m or explicit cap, and no deterioration of S1-M tail risk
```

### 13.3 新增 execution-aligned label audit

```text
execution_label_audit:
- compare close-to-close adjusted labels with T+1 open/VWAP/split execution PnL
- report correlation, sign agreement, PnL drift, cost drag, and failed-order carryover
- if model IC is positive but execution-aligned PnL is negative, status can only be candidate or inconclusive
```

### 13.4 新增 GMSL

将第 5 节建议条款直接纳入 S1.5/S3 之间。

---

## 14. 修订后的优先级路线图

### Phase A0：立即修订，不跑模型前完成

1. 固化 `walk_forward_calendar_v1`，按 horizon 生成 `computed_purge_days`。
2. 建立 `holdout_access_log.tsv`。
3. 建立 `test_family_registry` 与 `attempt_count`。
4. 建立 `benchmark_audit`。
5. 建立 `execution_label_audit` 模板。
6. 把 GMSL 数据源加入 `external_data_sources.csv`。
7. 把 S1-D 改名或标注为 `S1-R Daily Risk/Execution Mainline`，避免被误解为 active alpha 主线。
8. 把 dynamic IC turnover 改成明确的 pre-validation tighten-only 规则。

### Phase A-M：S1-M 正式月频强基线

1. 20 日标签；
2. 固定月末调仓默认，21 日滚动敏感性；
3. T+1 单日、3 日分批、5 日分批；
4. 成本 1x/2x/3x；
5. 1000 万、5000 万、1 亿容量；
6. 行业/市值/beta/流动性暴露报告；
7. 内部制度切片 + GMSL 初版冲击切片；
8. holdout 前不得调参。

### Phase A-R：日频风险/执行主线

1. 每日候选分数；
2. 每日 IC、周/月/季度汇总；
3. risk_signal/alert_state；
4. daily_orders_audit；
5. daily_turnover_capacity_report；
6. GMSL shock state；
7. 与 S1-M 持仓重叠和冲突交易；
8. 仅 report-only，后续通过 504 日以上成熟样本再进入 tighten-only。

### Phase B：S1.5 CSRP + GMSL 生产前审计

1. 等权 5 年 vs row-equal/date-balanced 12/18 月；
2. 6/24/36 月诊断；
3. 内部 regime map；
4. 2024Q1 量化拥挤；
5. 2022 俄乌、2026 美伊/中东等外生冲击分段；
6. 拥挤容量与 forced deleveraging；
7. S3 风控规则候选。

### Phase C：日频 alpha 小仓位候选

只有当分钟/集合竞价/limit_events 和日频执行 PnL 审计完成后再立项。

---

## 15. 最终审计裁决

### 15.1 可以保留的设计

- S1-M 月选股作为近期唯一正式 alpha 主线；
- S1-D 不进入 official keep；
- 5 年 rolling 单轨；
- 等权控制组；
- 12/18 月指数衰减候选；
- row-equal/date-balanced 对照；
- 成熟 IC yellow/red 状态机；
- purge/embargo/holdout/attempt_count/DSR/PBO/FDR；
- 三层 universe；
- S1 内置交易可行性和容量压力测试；
- 公司行为和 total return 审计分层阻塞；
- manifest/source registry/hash 治理。

### 15.2 必须修订后再跑正式实验的内容

1. 明确 `computed_purge_days`，避免 20 日标签 purge 被错误写成 40 日。
2. 把 GMSL 外生冲击层加入 CSRP 和 source registry。
3. 把 S1-D 升级为正式“日频风险/执行主线”，但禁止升级为 alpha keep 主线。
4. 增加 S1-D 独立日频样本门槛：252/504 成熟日、24 月桶、8 季度桶。
5. 增加 execution-aligned label / PnL audit。
6. 固定月末调仓作为 S1-M 默认，21 日滚动为敏感性。
7. 修正 dynamic IC turnover 为验证前 tighten-only。
8. 对 holdout 中的 2026 地缘冲击严格防污染。

### 15.3 不建议采纳的方向

- 立即恢复双轨 Track A/B；
- 立即把日频 `S1-D` 变成同级 alpha 主线；
- 允许 dynamic alpha 根据成熟 IC 放宽仓位；
- 用 2024Q1、post-2023、2026 美伊冲击窗口做选模；
- 在分钟/集合竞价/limit_events 未入仓前给出日频主动调仓收益承诺；
- 用外生冲击规则增加风险敞口；
- 用人工判断覆盖状态机或 keep/discard 规则。

---

## 16. 简明结论

新版规划已经从“策略想法”升级为“可审计研究工程”。当前最优路线不是追求更复杂模型，而是：

1. **先跑稳 S1-M 月频 alpha 主线**；
2. **把 S1-D 正式化为日频风险/执行主线，而非 alpha 主线**；
3. **新增 GMSL，补齐地缘—能源—汇率—全球波动率外生冲击层**；
4. **把 execution-aligned PnL、容量、订单失败和 forced deleveraging 提前纳入 S1/S1.5**；
5. **等待分钟/集合竞价/limit_events 和至少 504 个成熟日频 OOT 决策日后，再考虑日频 alpha 小仓位候选。**

按上述修订执行后，该计划将更贴近 A 股可用数据与真实交易约束，并能更好应对 2023-2024 的内部机制性变化以及 2022-2026 以来持续强化的外生地缘宏观冲击。它不保证高收益，但会显著提高“发现真实 alpha、避免伪 alpha、控制左尾和容量风险”的概率。

---

## 参考资料清单

### 内部文件

- `quant_strategy_plan(1).md`
- `quant_strategy_research_plan_detailed(1).md`
- `DATA_USAGE_GUIDE(1).md`
- `WAREHOUSE_README(1).md`
- `external_data_sources(1).csv`
- `validation_params(1).json`
- `warehouse_build_manifest.json`

### 外部公开资料

- World Bank, Commodity Markets Outlook press release, 2026-04-28.
- IMF, “War Darkens Global Economic Outlook and Reshapes Policy Priorities”, 2026-04-14.
- Reuters, reports on China quant funds, Lingjun trading restriction, and 2024 quant quake.
- Reuters/AP and international financial press reports on 2026 Middle East/Iran energy shock.
- CSRC and legal/regulatory summaries on registration-based IPO reform, new delisting/market-quality rules, and program trading supervision.
- Academic literature on Russia-Ukraine conflict and volatility spillovers across stock, currency, commodity and energy markets.
