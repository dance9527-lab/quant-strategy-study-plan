# A股量化策略研究与落地总纲（2026-04-30 版）

> 本文件是后续策略研究的短总纲。详细执行规则以 `quant_strategy_research_plan_detailed.md` 为准。  
> Canonical 数据源：`D:\data\warehouse`。旧 `processed`、旧 qant cache、旧随机验证结果只能作为历史对照或反例，不作为策略有效性证据。
> 2026-04-30 已吸收 `三方审计报告_20260430.md`：采纳其对执行可成交性、因子 PIT、walk-forward 固化和过拟合审计的核心批评；不采纳未经本地验证的收益承诺。

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

`三方审计报告_20260430.md` 给当前计划的共识评分为 `6.0-6.5/10`。我对其意见的裁决如下：

| 审计意见 | 裁决 | 写入方式 |
|---|---|---|
| 涨跌停执行风险是 P0 | 采纳 | 任何组合回测必须报告涨停禁买、跌停禁卖、连续锁死和反转统计；纸面 alpha 若无法成交则不计为有效 alpha。 |
| 开盘冲击三段模型是 P0 | 部分采纳 | 日频阶段先用 open/amount/participation 做保守冲击和容量惩罚；集合竞价和分钟三段模型需等 `prices_minute`/竞价表入仓后升级。 |
| 因子 PIT 合规是 P0 | 采纳 | 市值/估值/行业/风险警示均需通过实验层 PIT audit；warehouse leakage PASS 不能替代因子层审计。 |
| walk-forward 参数固化 | 采纳 | 官方证据默认 5 年训练、21 个交易日调仓、`purge_days >= max(horizon,20)`、embargo 5、至少 12 个 OOT step。 |
| Deflated Sharpe 和 holdout 默认化 | 采纳 | 所有可 keep 的组合结果必须做过拟合审计和 holdout/稳定性复核。 |
| S1 完成标准量化 | 采纳 | S1 通过条件新增 IC t-stat、bootstrap p、换手、成本后超额和容量门槛。 |
| 分红送配从 P2 提到 P1.5 | 部分采纳 | 作为 Phase A 并行 ETL，不阻塞首轮价格/收益基线，但阻塞 total-return 和基本面增强结论。 |
| 风险开关 v1 | 采纳 | 放入 S1 通过后的强制风险模块，默认 100/60/30/0 仓位状态只作为待验证 v1。 |
| DeepSeek 收益路径和 alpha 区间 | 不作为承诺采纳 | 只能作为假设队列，所有收益区间必须由本地实验重新验证。 |

---

## 2. 独立评估结论

当前最优先的工作不是追求新模型或高收益叙事，而是建立强基线和严格验证体系。

可立即推进的主线：

1. 日频多因子基线：估值、市值、流动性、动量、反转、波动率。
2. 保守可交易回测：T+1、涨跌停、停牌、ST、上市年龄、交易成本、容量。
3. 市场状态和风险开关：指数趋势、市场宽度、波动率、涨跌停压力。
4. PIT 行业中性和行业轮动：只使用 `pit_industry_intervals_akshare`，固定分类标准。
5. qant 小盘模型重审：只用 corrected baseline、OOT purge、blocked validation 和 embargo。

暂不作为第一批核心 alpha 的方向：

- 筹码增强：原始数据有价值，但尚未形成可审计 warehouse 主表，先做 ETL 和时点验证。
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
| P1 | 日频多因子强基线 | P0 audit 通过 | 证明 warehouse 下可交易超额是否存在 | 立即启动 |
| P1 | 基础容量压力测试 | P0 成交规则可运行 | 量化真实成交边界和成本拖累 | 随 S1 同步输出 |
| P1.5 | 风险状态和仓位开关 v1 | S1 有正向证据后 | 降低回撤和波动 | S1 通过后强制验证 |
| P1.5 | 公司行为/分红送配 ETL | source/available_at 先行 | total-return 和基本面 PIT 校验 | Phase A 并行准备 |
| P2 | PIT 行业中性和行业轮动 | 固定分类标准并验证覆盖 | 约束暴露、研究行业动量和拥挤 | 基线后启动 |
| P2 | qant 小盘模型重审 | 必须 purge/embargo | 判断旧 132 特征是否有可救增量 | 作为反例驱动重审 |
| P2 | AkShare 低频外部数据 | schema、available_at、质量检查先行 | 财务、公司行为、融资融券、解禁等增强 | 单独 ETL 阶段 |
| P3 | 筹码增强 | `chip_daily` 入仓并验证时点 | A 股特色增量 alpha | ETL 后研究 |
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
- Ridge、ElasticNet、线性横截面回归。
- LightGBM、XGBoost。
- LightGBM Ranker 或 LambdaRank，用于 Top-N 排序。

第一阶段目标是形成强基线，而不是调参追高收益。

### 4.2 第二阶段模型

在第一阶段通过后再评估：

- CatBoost：用于类别特征和稳健树模型对照。
- GARCH/HAR-RV：用于波动率和风险状态。
- TFT、N-HiTS、PatchTST、iTransformer：用于多周期时序增强。
- AutoGluon-TimeSeries、Darts、NeuralForecast：只作为快速模型比较平台。

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
| 3 | 融资融券明细 | 杠杆资金和拥挤度 | P2 接入 |
| 4 | 股东户数、质押、限售解禁 | 供给压力和风险过滤 | P2 接入 |
| 5 | 分析师预期修正 | 预期变化和事件驱动 | P2 候选，需可审计历史源 |
| 6 | 北向资金 | 资金流状态 | P3 接入 |
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

### 验证框架参数调整
- **embargo**：5日 → 10-15日（A股因子自相关持续期更长）
- **purge**：max(horizon,20) → max(horizon*3,40)
- **训练窗口**：默认5年 → 默认3年（产出更多OOT steps）
- **OOT steps**：最少12 → 最少24（覆盖2年）
- **S1门槛放宽**：IC t-stat>1.5或bootstrap p<0.10（满足其一），增加"弱alpha候选"路径

### 因子库扩展
- P1阶段同步纳入3-5个另类数据因子（北向资金、融资融券）
- 筹码数据ETL从P3提前到P1阶段

### 新增验证项
- 因子正交化流程（ICIR加权前）
- 多重检验校正（FDR，因子>20个时）
- 尾部风险指标（VaR 95%、CVaR 99%）
- regime断裂检测和保护

### 深度模型降级
- 放弃PatchTST/TFT，改用轻量LSTM或1D-CNN
- 或定位为云端实验，本地只做推理

### 容量测试前移
- S1阶段增加最简容量过滤（日均成交额>1000万）
- S2做精细容量分析（分档滑点/冲击/参与率）

详细共识报告见：consensus_audit_report_20260430.md

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

---

## 7. 近期行动路线

### Phase A：日频强基线

目标：建立可复现、可审计的日频股票多因子基线。

产出：

- `validation_params.json` 固化的 walk-forward 参数。
- 实验层 PIT audit、split label audit、benchmark audit。
- 涨跌停禁买/跌停禁卖、连续锁死、开盘冲击和成交失败报告。
- 因子覆盖率和质量报告。
- 单因子 IC、RankIC、ICIR。
- 分层收益和衰减报告。
- 基础组合回测：等权、ICIR、线性、LightGBM/Ranker。
- 成本、换手、成交失败、容量报告。

### Phase B：风险状态和组合约束

目标：减少回撤，约束风格和行业暴露。

产出：

- 市场状态变量库。
- 仓位开关对照实验。
- 风险开关 v1：牛市 100%、震荡 60%、熊市 30%、极端 0% 作为候选，不作为默认事实。
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

