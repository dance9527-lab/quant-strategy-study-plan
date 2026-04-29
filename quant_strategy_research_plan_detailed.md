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

### 1.3 Canonical 数据源

只以 `D:\data\warehouse` 为策略研究 canonical 数据源。

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
| `valuation_daily` | 16,642,794 | 2000-01-04 至 2026-04-27 | 市值、估值、股本、换手率 | T 日盘后可见，左连接 |
| `tradability_daily` | 18,177,689 | 1990-12-19 至 2026-04-27 | bar 存在、推断停牌、可交易性 | 停牌是工程推断 |
| `tradability_daily_enriched` | 18,177,689 | 1990-12-19 至 2026-04-27 | 涨跌停、买卖阻断、上市年龄、风险警示 | 第一版成交过滤首选 |
| `universe_daily` | 18,177,689 | 1990-12-19 至 2026-04-27 | 基础和因子研究股票池 | 第一版研究首选 |
| `benchmarks` | 31,229 | 1990-12-19 至 2026-04-27 | 全 A 代理、官方中证指数 | 禁止恢复同日成交额加权 |
| `reference_rates` | 55,964 | 1990-12-19 至 2026-04-27 | 国债、Shibor、固定 fallback | 固定 1.5% 仅作 fallback |
| `industry_classification.pit_industry_intervals_akshare` | 53,925 | 1990-01-29 至 2026-04-24 | PIT 行业中性和行业轮动 | 必须固定分类标准 |
| `risk_warning_daily` | 8,973,264 | 1994-01-03 至 2026-04-27 | 风险警示过滤 | 深市历史较完整，沪/北不足 |
| `trading_costs.equity_cost_history` | 23 | 1990-12-19 至 2023-08-28 | 交易成本 | 部分为研究假设 |

### 2.2 数据缺口

每份策略报告必须披露：

- 2026-01-05 至 2026-02-05 的估值覆盖缺口。
- `valuation_daily` 与收益表 key 不完全一致。
- 完整交易所官方停复牌公告缺失。
- 沪/北历史 ST、摘帽、摘星缺 PIT 官方源。
- 历史 PIT 指数成分和权重缺失。
- 三所官方历史差异日历未独立验证。
- 成本中的佣金、滑点、冲击成本仍是研究假设。
- 筹码、涨停、分钟、期权尚未形成可审计 warehouse 主表。

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
| 因子 PIT 审计 | 检查每个特征的 `source`、`available_at`、`decision_time`、截面成员和复权生效规则 | `pit_factor_audit` 报告或等价表 |
| 验证参数固化 | 引用并记录 `validation_params.json` 的 SHA256；任何偏离都要预先声明 | `validation_params_hash` |
| benchmark 审计 | 确认 benchmark 来源、可得日、覆盖区间、是否为官方或内部代理 | `benchmark_audit` 报告 |

---

## 3. 股票池和交易约束

### 3.1 默认股票池

第一版研究默认使用 `universe_daily.in_factor_research_universe=True`。

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
| `excess_ret_1d` | 个股 T+1 收益减 benchmark | 快速 IC | 1 个交易日 |
| `excess_ret_5d` | 个股未来 5 日超额收益 | 周频选股 | 5 个交易日 |
| `excess_ret_10d` | 个股未来 10 日超额收益 | qant 对照和中频模型 | 10 个交易日 |
| `excess_ret_20d` | 个股未来 20 日超额收益 | 月频选股 | 20 个交易日 |
| `rank_ret_5d/20d` | 同日横截面未来收益 rank | 排序模型 | 对应 horizon |
| `top_quantile_5d/20d` | 是否进入未来收益 top 分位 | 分类模型 | 对应 horizon |
| `realized_vol_20d` | 未来 20 日波动率 | 风险模型 | 20 个交易日 |
| `max_dd_20d` | 买入后 20 日最大回撤 | 风控标签 | 20 个交易日 |

标签从 `return_adjusted_pit` 计算，成交约束从未复权价格和可交易表计算。

### 4.2 禁止标签和特征混用

禁止：

- 在特征表中存入 future return。
- 用 T+1 或未来窗口的高低点做 T 日止盈止损特征。
- 用未来涨跌停状态过滤训练样本。
- 用未来行业、未来 ST、未来停牌状态构造历史股票池。

### 4.3 qant 类 10 日标签特殊规则

任何 10 日 forward label 必须：

- 在 OOT 月边界剔除 `target_date_10d >= oot_start` 的训练候选样本。
- 跑 split label audit。
- 报告 train/validation 中跨 OOT label 行数。
- 诊断性 qant 对照可使用 `--purge-days 10` 或等价逻辑。
- 新的正式策略证据必须服从 `purge_days >= max(label_horizon, 20)`，除非在实验登记中预先声明更保守或更窄的诊断目的。

---

## 5. 因子库

### 5.1 P1 核心日频因子

先用已入仓表构建以下因子：

| 类别 | 示例 | 来源 |
|---|---|---|
| 市值 | `log_total_mv`、`log_circ_mv` | `valuation_daily` |
| 估值 | EP、BP、SP、股息率代理 | `valuation_daily` |
| 流动性 | 成交额均值、换手率、Amihud illiquidity | 日 K、估值 |
| 动量 | 5/20/60/120 日 PIT 复权收益 | `prices_daily_returns` |
| 反转 | 1/3/5 日收益 | `prices_daily_returns` |
| 波动率 | 20/60 日波动、下行波动、振幅 | 日 K、收益 |
| 风险 | beta、残差波动、最大回撤 | benchmark、收益 |
| 交易约束 | 上市年龄、涨跌停、停牌、ST | `tradability_daily_enriched` |
| 行业 | PIT 行业哑变量、行业收益、行业动量 | PIT 行业表 |

因子 PIT 合规要求：

- 估值、市值、股本和换手因子必须使用当日 `available_at` 与 `decision_time`；估值类字段不能假设财报披露早于实际公告日。
- 复权收益、动量和标签必须使用 `return_adjusted_pit` 或等价 PIT 调整收益；复权信息默认 T 日盘后可见、T+1 生效。
- 月末或调仓截面必须只包含当时已存在、已上市且通过可交易过滤的证券，不得使用未来成分、当前行业快照或当前风险警示状态。
- 所有新因子进入组合回测前必须通过因子 PIT 审计；未通过的因子只能用于离线诊断，不能进入 keep 决策。



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
4. Ridge、ElasticNet。
5. LightGBM / XGBoost。
6. LightGBM Ranker / LambdaRank。
7. CatBoost。
8. 深度时序模型。
9. NLP / RL。

任何复杂模型必须在同一数据、同一股票池、同一成本、同一验证切分下对比强基线。

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

TFT、N-HiTS、PatchTST、iTransformer、Chronos/TimesFM/Moirai 等只能在满足以下条件后进入：

- 日频强基线完成。
- walk-forward 与 purge/embargo 体系稳定。
- 有明确额外收益来源，例如多周期分位数预测、波动率预测、场景生成。
- 训练日志、随机种子、模型版本、输出缓存可复现。
- 与 LightGBM/Ranker 同口径比较。

深度模型不得以“模型先进”为进入理由。

---

## 7. 验证框架

### 7.1 默认验证

主证据必须使用预注册 walk-forward 参数。默认配置见 `validation_params.json`，当前版本为：

| 参数 | 默认值 |
|---|---:|
| 训练窗口 | 5 年 |
| 测试/调仓窗口 | 21 个交易日 |
| purge | `>= max(label_horizon, 20)` 个交易日 |
| embargo | 5 个交易日 |
| 最少 OOT step | 12 |
| holdout | 必须保留，不参与调参、特征选择、early stopping 或阈值选择 |

主证据：

- chronological walk-forward。
- OOT 月、21 个交易日窗口或 OOT 年，必须在实验登记中预先声明。
- Purged split。
- Embargo。
- split label audit。

辅助诊断：

- blocked random + purge + embargo。
- Combinatorial Purged CV。
- 参数扰动。
- 分年度、分市场状态、分市值和分行业表现。

禁止把普通 random 8/2 作为最终证据。

硬规则：

- 任何使用未来收益标签的训练、验证、early stopping、阈值选择或调参样本，都必须先做 OOT 边界 purge。
- random 只能作为 blocked random 诊断，且必须同时有 `validation_purge_days` 和 `embargo_days`。
- 未报告 split label audit 的模型结果不得进入 keep、晋级或总纲结论。
- 偏离 `validation_params.json` 时，必须在实验启动前写明原因，并在报告中列出参数文件 hash 和实际参数。

### 7.2 最小报告指标

模型指标：

- AUC，如是分类。
- RankIC。
- ICIR。
- top quantile precision。
- top-bottom decile spread。
- IC t-stat。
- block/bootstrap p-value。
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
- 若连续 2 个季度 IC 符号反转或 t-stat 低于 1，标记为 yellow。
- 若连续 4 个季度失效、成本后贡献为负或容量恶化，标记为 red，并进入降权/暂停候选。
- 因子恢复必须重新通过同口径 walk-forward，而不是只看最近短期反弹。

### 7.3 过拟合审计

过拟合审计分层执行：

- 探索性单次实验可以先不计算完整 DSR/PBO，但状态只能是 `candidate`。
- 任何 `keep`、策略晋级、写入总纲、或声称存在 alpha 的结论，必须包含 Deflated Sharpe Ratio、独立 holdout 复核和参数扰动。
- 多策略、多参数、多模型搜索时，还必须增加 PBO 或同类 data-snooping 检验。

必须报告：

- Deflated Sharpe Ratio。
- Probability of Backtest Overfitting。
- White Reality Check 或同类 data snooping 检验。
- holdout 窗口复核。
- `attempt_count` 和候选数口径。
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

---

## 9. 策略模块

### 9.1 S1：日频多因子强基线

目标：回答当前 warehouse 下是否存在真实、成本后、可交易的日频股票 alpha。

数据窗口：

- 主窗口：2005-01-01 至 2026-04-27。
- 可从 2000 年开始做敏感性检查，但早期市场结构和估值覆盖需单独标注。

模型顺序：

1. 单因子。
2. 等权打分。
3. ICIR 加权。
4. Ridge / ElasticNet。
5. LightGBM。
6. LightGBM Ranker。

S1 内置最小交易可行性，不能等到 S2：

- T+1、涨跌停、停牌、ST、上市年龄、100 股交易单位必须进入回测。
- 基础成本、保守滑点、开盘 L1 冲击必须进入成本后结果。
- 必须报告涨停买不到、跌停卖不出、连续锁死、成交失败率和解锁后反转。
- 至少报告 1000 万、5000 万、1 亿资金档；若 1 亿失效，应明确容量上限。

S1 完成门槛：

- 至少 12 个 walk-forward OOT step。
- RankIC 或核心 IC 均值为正，且 t-stat > 1.5 或 bootstrap p-value < 0.10（满足其一即可）。
- 增加"弱alpha候选"路径：IC方向一致 + 分年度正率 > 70% + 成本后不为负 → 标记为 candidate。
- 候选因子 > 20 个时，必须报告 FDR 校正后的显著性。
- 成本后超额收益为正。
- 年化双边换手 < 300%，除非策略明确被标注为高换手且容量/成本仍通过。
- holdout 不失效，方向和主窗口一致。
- 多数年份或多数市场状态不为单一窗口贡献。
- 相对线性和简单打分有稳定增量。
- 未通过上述门槛不得进入总纲收益结论，只能保留为 candidate 或 discard。


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

- 仓位开关 v1 候选：牛市 100%、震荡 60%、熊市 30%、极端 0%。
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
- 新的正式证据使用 `purge_days >= max(label_horizon, 20)`。
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
2. 财报、业绩预告、业绩快报。
3. 融资融券。
4. 股东户数、质押、限售解禁。
5. 分析师预期修正和一致预期变化。
6. 北向资金。
7. 龙虎榜、大宗交易。
8. 公告、新闻和 NLP。

任意接入必须先写 source registration，再写 ETL，再跑质量检查。

### 9.7 S7：筹码、涨停、分钟、期权

这些方向仅在对应表入仓并通过验证后进入 alpha 研究：

- `chip_daily`：筹码字段、时点、异常值、供应商算法解释。
- `limit_events`：盘后事件字段和盘中可见字段分离。
- `prices_minute`：5min 优先，用于执行优化。
- `option_minute`：合约、流动性、IV、Greeks、保证金、bid/ask 缺口说明。

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
| `shareholder_structure/shareholder_households_quarterly` | `asset_id, stat_date, holders, holders_prev, holders_change_pct, avg_holding_qty, avg_holding_mv, announcement_date, available_at` |
| `risk_pressure/pledge_ratio_snapshot` | `asset_id, trade_date, pledge_ratio, pledged_shares, pledge_mv, pledge_count, available_at` |
| `event_supply/restricted_release_events` | `asset_id, release_date, release_shares, release_mv, holder_type, announcement_date, available_at` |

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
run_id	hypothesis	baseline_run_id	commit	changed_files	data_window	validation_mode	validation_params_hash	purge_days	validation_purge_days	embargo_days	validation_block_days	holdout_window	command	primary_metric	guardrails	attempt_count	total_return	CAGR	Sharpe	deflated_sharpe	pbo	max_drawdown	holdout_total_return	holdout_sharpe	holdout_max_drawdown	excess	turnover	cost_drag	capacity_tier	execution_fail_rate	limit_up_buy_fail_count	limit_down_sell_fail_count	best_iteration_mean	rank_ic_mean	ic_t_stat	bootstrap_p	leak_audit_status	split_label_audit_status	pit_factor_audit_status	benchmark_audit_status	status	decision	notes
```

### 11.1 Keep 规则

只有同时满足以下条件才可 keep：

- 通过 leakage audit。
- 通过因子 PIT audit、split label audit 和 benchmark audit。
- 相对 corrected baseline 改善主指标。
- 回撤、换手、成本、容量不明显恶化。
- IC t-stat、bootstrap p、holdout 和 Deflated Sharpe 满足预注册门槛。
- 年度表现不过度集中。
- 模型排序指标方向一致。
- 不依赖改变 benchmark、费用、股票池或窗口取胜。
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

---

## 12. Review 清单

提交给独立专家 review 前必须逐项自查：

### 12.1 数据

- 是否只使用 `D:\data\warehouse` canonical 表。
- 每个字段是否有 source、`available_at`、`decision_time`。
- 是否运行最新 `leakage_check`。
- 是否完成因子 PIT audit，尤其是估值、财报派生、市值、复权、行业和风险警示字段。
- 是否有重复键。
- 是否使用未来股票池、未来行业、未来 ST 或未来停牌。
- 是否披露外部源缺口。

### 12.2 标签和验证

- 标签 horizon 是否明确。
- purge 天数是否不小于 label horizon。
- 官方证据 purge 天数是否满足 `>= max(label_horizon, 20)`。
- OOT 边界是否无跨月/跨期 label。
- 是否使用 chronological walk-forward。
- 若有 random，是否 blocked + purge + embargo。
- 是否有 split label audit、真正 holdout、DSR/PBO 或等价过拟合审计。
- holdout 是否完全未参与调参、特征选择、early stopping 或阈值选择。

### 12.3 回测

- 成交价是否来自未复权可成交价。
- 收益、动量、标签是否使用 PIT 复权收益。
- T+1、涨跌停、停牌、ST、上市年龄、交易单位是否处理。
- 成本、滑点、冲击和容量是否进入。
- 是否报告成交失败、连续锁死、解锁后反转、成本拖累和容量上限。
- 是否区分日频 L1 开盘冲击模型与尚未具备数据的集合竞价/分钟三段模型。

### 12.4 模型

- 是否先比较简单基线。
- 特征重要性是否集中在可疑字段。
- 参数扰动是否稳定。
- 是否存在调参后只展示最好窗口。
- 是否记录随机种子、命令、输出路径。
- 是否记录 `attempt_count`、参数文件 hash、依赖版本和代码提交。

### 12.5 结果解释

- 是否同时报告模型指标和组合指标。
- 是否报告分年度、分市场状态。
- 是否避免承诺未经验证的收益。
- 是否明确 qant random 8/2 只是验证污染反例。
- 是否把审计报告中的收益路径只作为假设队列，而不是结论或承诺。

---

## 13. 近期执行顺序

### Step 1：构建日频研究面板 v1

输入：

- `universe_daily`
- `prices_daily_returns`
- `valuation_daily`
- `tradability_daily_enriched`
- `benchmarks`
- `reference_rates`
- `trading_costs`
- PIT 行业表

输出：

- `features` 表或实验缓存。
- 字段覆盖率报告。
- 缺失和异常值报告。
- `pit_factor_audit` 报告。
- `validation_params.json` hash。
- `benchmark_audit` 报告。

### Step 2：单因子和分层验证

输出：

- IC / RankIC / ICIR。
- IC t-stat 和 block/bootstrap p-value。
- Top-Bottom。
- 分年度稳定性。
- 季度滚动 IC 衰减监控。
- 因子相关性。
- 中性化前后对比。

### Step 3：保守组合基线

输出：

- 等权、ICIR、线性、LightGBM/Ranker 对照。
- 成本后收益。
- 成交失败、连续锁死和解锁后反转。
- S1 最小容量：1000 万、5000 万、1 亿。
- 资金规模敏感性。
- Deflated Sharpe、holdout 和 split label audit。

### Step 4：风险状态和组合约束

输出：

- 风险开关报告。
- 回撤改善报告。
- 预注册 100/60/30/0 仓位 v1 对照。
- 行业、市值、beta、换手约束对比。

### Step 5：公司行为和外部低频数据 ETL

公司行为、分红送配在 Phase A 期间可并行做最小 ETL，用于 total-return 和复权校验；作为 alpha 因子使用仍需等 source/available_at 审计通过。其他外部低频数据只有当 Step 1-4 证明基线稳定，且 review 同意后启动。

输出：

- source registration。
- ETL 脚本。
- schema registry 增量。
- leakage check 增量。
- source gap report。

---


## 13.5 三方审计共识改进（2026-04-30）

### 新增验证项

1. **因子正交化流程**：在ICIR加权和Ridge之间增加Gram-Schmidt正交化，产物为正交化前后因子相关性矩阵对比。
2. **regime断裂检测**：在walk-forward每个OOT step中单独报告regime断裂期表现，增加简单regime检测（基于波动率聚类或连续IC为负），风险开关中加入regime断裂保护（连续5日因子IC为负时自动减仓）。
3. **尾部风险指标**：S1验证中增加VaR 95%、CVaR 99%、最大回撤持续期。
4. **多重检验校正**：候选因子>20个时，必须报告FDR校正后的显著性。
5. **季节性效应**：在因子中加入月份哑变量，或确保walk-forward训练窗口包含完整季节性周期。

### 因子库扩展

- P1阶段同步纳入3-5个另类数据因子：北向资金净流入、融资余额变化率、限售解禁压力。
- 筹码数据ETL从P3提前到P1阶段并行执行。
- 另类数据因子PIT审计可延后，先标记为candidate。

### 深度模型降级

- 放弃PatchTST/TFT在Arc B390上的执行计划。
- 替代方案：轻量LSTM（hidden=64, 1层）或1D-CNN。
- 或定位为云端实验（Colab A100），本地只做推理。

### 容量测试前移

- S1阶段增加最简容量过滤：日均成交额>1000万。
- S1报告中包含基础容量指标：持仓市值/日均成交额比值。
- 精细容量分析（分档滑点/冲击/参与率）保留在S2。

### 数据缺口影响量化（S1启动前必做）

| 对比实验 | 目的 | 预计耗时 |
|---------|------|---------|
| 有/无ST过滤的因子IC对比 | 量化ST PIT缺口影响 | 2小时 |
| 有/无停牌推断的可交易universe对比 | 量化停牌推断精度 | 1小时 |
| 不同embargo值（5/10/15）的OOT结果对比 | 确定最优embargo | 3小时 |

## 14. 文档治理

Git 项目中的活跃文档只有两份：

- `quant_strategy_plan.md`：总纲。
- `quant_strategy_research_plan_detailed.md`：执行规范。

参考文档：

- `量化时间序列模型调研和选择.md`
- `量化策略设计调研与建议.md`

这些参考文档提供模型和方法论候选，但不覆盖本执行规范中的数据约束、验证约束和回测约束。

每轮专家 review 后，如有采纳意见，优先修改 Git 项目中的这两份活跃文档，并在本仓库 `task_plan.md`、`findings.md`、`progress.md` 记录裁决理由。`D:\data\strategy\` 下旧副本不得与 Git 项目分叉维护。

