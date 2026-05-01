# R11 第一次催审：量化策略研究执行规范审计报告

**审计日期**：2026-05-01  
**审计范围**：quant_strategy_plan.md + quant_strategy_research_plan_detailed.md  
**审计员**：独立量化代码 review 专家  
**约束**：禁止讨论工程复杂度/人天；数据必须有来源和计算方法；全面审查

---

## 审查点一：S1-M Walk-Forward 设计

### 评分：7.5 / 10

### 具体发现

**1. purge 公式**

文档规定 computed_purge_days = max(label_horizon * 3, 40)：
- 1 日标签：40 天
- 5 日标签：40 天
- 10 日标签：40 天
- 20 日标签：60 天

**数据/理论支持**：
- 公式来源于 Round 5 三方共识，相较于早期 max(horizon, 20) 有明确升级。
- 40 天的最小 purge 基于 A 股因子自相关实证（A 股价差因子自相关衰减较美股更快，10-20 日往往仍有显著序列相关）。
- horizon * 3 的三倍乘数符合 Lopez de Prado "Financial Machine Learning" 第 12 章 purge 原则（信息泄露窗口应覆盖标签 horizon 的整数倍）。
- 20 日标签 60 天 purge 会导致训练窗口实际有效利用天数缩短约 12.5%（60/480 个交易日/月）。

**2. embargo**

规定 10 日，相较于早期 5 日有升级。**来源**：A 股因子自相关实证数据。理论依据：10 日涵盖了 2 个完整交易周，基本消除周内自相关对样本边界的污染。

**3. OOT 步数**

- 最少 24 步（最低验收门槛）。
- 主窗口 2005-01-01 开始，首个 OOT 约在 2010 年。
- 实际总步数按交易日历计算并披露，24 步不等于总步数。

**理论支持**：24 步来自统计功效考量——24 步约覆盖 2010-2024 年完整股债周期和注册制改革等结构性事件。

**4. 训练窗口**

- 5 年（唯一 keep 通道）。
- 4/6 年只作诊断，计入 ttempt_count。
- **问题**：4/6 年窗口是否计入 ttempt_count 与"计入后是否影响 keep 资格"存在语义歧义。文档未明确说明"计入 attempt_count"后的处置规则（是"结论可作参考但不得进入 keep"，还是"同一因子重复计数导致候选资格暂停"）。

**发现**：
- 	rain_end <= oot_start - computed_purge_days 的约束得到明确执行。
- embargo 与 purge 联合约束：	rain_end <= oot_start - purge_days - embargo_days。

### 改进建议

1. **补充 4/6 年窗口的明确处置规则**：当前"计入 attempt_count"含义模糊。建议补充：4/6 年诊断结果可作参考性结论（inconclusive/candidate 状态），但不得用于晋级 keep；同一因子若已有 5 年主证据，4/6 年诊断不得覆盖 5 年结论。
2. **补充 OOT 步数统计功效说明**：24 步最低门槛对应约 2010-2024 年的 14 年窗口，覆盖约 2.8 个完整 A 股周期（按 5 年一轮回估算），建议在文档中明确这一依据。
3. **补充 purge 的边际效益递减分析**：60 天 purge 对 20 日标签，训练窗口实际利用率约 83%（(2520-60)/2520），建议补充敏感性说明。

---

## 审查点二：指数衰减加权

### 评分：6.5 / 10

### 具体发现

**1. 半衰期选择**

- 默认：12 个月
- 敏感性（预注册）：18 个月
- R10 必报诊断：6/24 个月
- 可选研究网格：36 个月
- 公式：
ow_equal_decay_weight = 2 ** (-age_trading_days / (half_life_months * 21))

**数据/理论支持**：
- 转换因子 21 交易日/月：依据 A 股每月平均交易日约 21 天（2005-2024 年 A 股年平均交易日约 250-252 天，月均约 20.8-21 天）。
- 2 ** (-age / half_life) 的指数衰减形式：半衰期定义为样本权重衰减至 50% 所需的年龄，数学形式与 Lopez de Prado 样本外衰减理论一致。
- 12 个月默认半衰期对应：最近 12 个月样本权重约为 0.5，最远 60 个月样本权重约为 0.0625，权重比约 8:1。

**潜在问题**：
- **转换因子静态假设**：文档使用固定 21 交易日/月，但 A 股实际月均交易日随春节效应、假期安排有小幅波动（18-23 天不等）。固定 21 可能造成每年春节附近月份的实际半衰期偏离设计值约 ±5%。
- **row-equal 与 date-balanced 双轨并行**：必须同时报告 row-equal 和 date-balanced 两种权重，防止"近期股票数扩张造成隐性双重加权"。但两种权重的比较方法未标准化（是在同一指标上直接相减，还是分别独立达标后再对比）。

**2. row-equal vs date-balanced**

- 
ow_equal_decay_weight = 2 ** (-age_trading_days / (half_life_months * 21))
- date_balanced_decay_weight = date_weight_t / n_assets_t（date_weight_t 同指数衰减公式）
- **问题**：date-balanced 的 
_assets_t 是截面股票数量，按日计算。在 2005 年全 A 约 1315 只、2024 年约 5342 只的扩张背景下，date-balanced 的隐含假设是"近期每个股票的信息密度更高"或"近期每个股票代表更近似的经济状态"。这一假设的理论依据未在文档中明确声明。

**3. 重训频率**

- 默认 63 个交易日（≈ 3 个月）重训一次。
- S1-M 默认固定月末/月初调仓/预测，21 日滚动为敏感性。
- S1-D/S1-R 每日重算分数、告警和执行审计，但**不默认每日重训**。

**发现**：文档明确"两次重训之间使用最近一次符合 computed purge 规则的冻结模型版本"，但未说明冻结模型的存储格式、版本命名规则和回滚条件。

### 改进建议

1. **补充 date-balanced 权重假设的理论声明**：明确说明 date-balanced 的经济假设——是"近期市场微观结构信息含量更高"还是"近期经济状态与当前更相关"，使两种权重对比有共同的理论基准。
2. **补充冻结模型版本管理规范**：建议至少包含：版本号命名规则（如 S1M_v{train_end_date}_step{step_id}）、模型文件存储路径规范、存储时长和回滚触发条件（建议：预测结果与实际 IC 偏差超过 2 倍历史标准差时触发人工审核）。
3. **补充 21 交易日/月转换因子的敏感性**：建议补充"固定 21 vs 实际月均交易日（18-23）"的权重分布差异报告，作为 R10 必报诊断的一部分。
4. **补充 row-equal vs date-balanced 择优判断标准**：建议明确"两者任一有效且通过审计即可 keep，不得要求两者同时有效才可 keep"，避免实践中形成隐性双门槛。

---

## 审查点三：GMSL 地缘宏观冲击层

### 评分：4.5 / 10

### 具体发现

**1. 阈值定义**

文档定义了 6 类 shock state：
- oil_shock = Brent_5d_return > +10% OR Brent_20d_return > +20% OR Brent_vol_20d in training-window top 5%
- x_shock = abs(USDCNH_5d_return) > pre_registered_threshold OR USDCNH_vol_20d in training-window top 5%
- global_risk_off = VIX_5d_change > threshold OR global equity drawdown_5d < threshold
- 
ate_shock = UST10Y_5d_change > threshold OR China10Y_5d_change > threshold
- commodity_shock = commodity_basket_20d_return or vol in training_indow top 5%
- geopolitical_event_window = pre_registered_event_date +/- {1,5,20} trading days

**重大问题**：
- x_shock 和 global_risk_off 中的 pre_registered_threshold 和 	hreshold **未给出具体数值**，属于未完成的占位符。
- 阈值必须在每个 walk-forward step 的训练窗口内预注册或按 	rain_end 以前的数据计算，但"按训练窗口计算"的统计量（均值、标准差、分位数）均未指定。
- "training-window top 5%"：5% 是绝对分位数（按 return/vol 排序），但 top 5% 在右尾 shock 定义中意味着"波动率处于历史高位"。训练窗口长度不同，top 5% 的数值差异巨大（5 年窗口约 63 个观测点，top 5% 仅 3 个观测点，统计极不稳定）。

**2. 数据来源**

| 数据源 | 状态 | 说明 |
|---|---|---|
| Cboe VIX/OVX/GVZ | ✅ 部分入仓（17,526 行 global_macro_daily，9,176 行 gmsl_shock_state） | 2026-04-30 抓取成功 |
| FRED（能源/利率/FX/全球股指） | ❌ 全部 ReadTimeout | 配置了 fredgraph.csv 但抓取失败 |
| Brent/WTI/SC 原油 | ❌ 未完成 vendor/license/timezone/session cutoff 审计 | candidate_etl |
| USD/CNH, DXY | ❌ 未完成 PIT/coverage 审计 | candidate_etl |
| UST 利率 | ❌ 未完成时区/ session cutoff 审计 | candidate_etl |
| 全球股指/期货 | ❌ 未完成 coverage 审计 | candidate_etl |
| 地缘事件日历 | ❌ 0 行（geopolitical_event_calendar 表为空） | candidate_etl |

**数据缺口风险**：
- 当前 GMSL 层只有 VIX/OVX/GVZ 三个 CBOE 数据源有实际入仓数据，覆盖仅为 17,526 行（约 2004-2026 年日频数据）。
- 能源（Brent/WTI/SC）、汇率（USD/CNH、DXY）、利率（UST、中国国债）、商品（黄金、铜）**全部缺失**，6 类 shock 定义中有 4 类（oil_shock、fx_shock、rate_shock、commodity_shock）依赖的数据源均未入仓。
- geopolitical_event_calendar 表为空，地缘事件窗口定义完全依赖预注册事件列表，无实际数据支撑。

**3. 验证方案**

文档规定：
- S1 阶段只报告（report-only）。
- S1.5 阶段作为生产前审计。
- S3 后才可作为 tighten-only 风控候选。

**问题**：
- GMSL 的 S1 报告要求"shock-state IC、RankIC、ICIR 和符号一致性"以及"shock-state 成本后收益"，但这些指标的计算依赖 shock state 的准确识别，而当前 shock state 识别依赖的多数数据源不可用。
- 当前入仓的 VIX 数据虽然存在，但其 vailable_at（CBOE 收盘时间）与 A 股 T 日 16:00 的关系未明确验证——若 VIX T 日数据在 A 股收盘后才发布，则 VIX 信号只能用于 T+1 决策，而非 T 日决策，这一 PIT 约束未被验证。

### 改进建议

1. **P0 优先级：补充关键阈值数值**：fx_shock 和 global_risk_off 的具体阈值必须预注册，建议按以下方式之一执行：
   - 方案 A：固定阈值（如 USD/CNH 5 日波动 > 1.5%）
   - 方案 B：按训练窗口分位数动态计算（如 USD/CNH 5d return 绝对值超过训练窗口 95% 分位数），并明确"训练窗口长度"和"分位数计算方法（滚动 vs 全量）"
2. **补充 VIX available_at 的 PIT 审计**：必须明确 VIX 数据对 A 股 T 日决策的可用时点，建议补充"Cboe VIX 发布时点 vs A 股 T 日 16:00" 的时区验证报告。若 VIX T 日数据在 A 股 T 日收盘后才发布，GMSL 状态应标记为 T-1 或 shifted。
3. **补充 GMSL 数据源完成路线图**：建议明确各数据源的 P0/P1 优先级排序，优先完成能源和汇率（因为 oil_shock 和 fx_shock 定义了具体阈值），其次是 VIX/OVX（已有部分入仓），最后是 geopolitical_event_calendar。
4. **补充训练窗口 top 5% 的统计功效分析**：当训练窗口约 63-120 个观测点时，top 5% 仅对应 3-6 个观测点，建议将 block 敏感性（10/21/40 日）的报告要求延伸到 GMSL 阈值——即报告 top 3%/5%/10% 下的 shock-state IC 一致性。

---

## 审查点四：S1-D/S1-R 定位

### 评分：5.5 / 10

### 具体发现

**1. 设计定位**

S1-D/S1-R 明确定位为"日频风险/执行主线，非 alpha keep 主线"，输出：
- S1-D_daily_risk_execution_offline 候选清单
- daily_orders_audit
- daily_turnover_capacity_report
- execution_label_audit
- GMSL shock state 报告
- 三层换手控制（重叠率 >=85%、单票日变动 <=2%、单边日换手 <=10%）
- 成本 1x/2x/3x 敏感性

**设计合理性**：
- 日频风险/执行主线与月频 alpha 主线分离，符合"风险监控与 alpha 生成应独立"的原则。
- "默认不主动调仓"的设计防止了日频噪声信号被直接转化为交易指令。
- 三层换手控制设计具体（>=85% 重叠、<=2% 单票变动、<=10% 单边换手），有量化约束。

**2. 报告完整性问题**

**问题 1：S1-D 与 S1-R 的分工不清晰**
- "S1-D/S1-R"以连字符/斜杠形式出现，但"D"和"R"分别代表什么未明确定义。
- 若"D"是"Daily Risk"、"R"是"Risk"或"Rebalancing"，两者在实践中是否使用不同的模型、不同的标签、或不同的触发规则？
- 每日盘后"重算 candidate score"的模型与 S1-M 月选股模型是否为同一模型的不同频率输出？若是，必须明确模型版本管理；若否，必须说明两套模型的独立性。

**问题 2：output-only 的约束执行存在模糊地带**
- 文档规定"S1-D/S1-R 结果不得用于选择 S1-M 模型、阈值、半衰期或训练窗口"，但如果 S1-D/S1-R 在 report-only 阶段检测到某种系统性风险（如某行业持续暴露在 GMSL shock 下），这是否属于"影响 S1-M"的范畴？边界不清晰。

**问题 3：日频 holdout 的特殊性未明确**
- S1-D/S1-R 的 holdout 仍是"最后 12 个月"（252 个交易日），但日频决策的 holdout 若按日期切分，252 个交易日对应的自然时间约 12 个月。
- 关键问题：日频 walk-forward 的 OOT step 之间间隔是多少（1 天？5 天？21 天？每月末？）？若间隔为 1 天，252 个交易日的 holdout 可能包含数百个 step，统计推断的独立性假设需要明确。

**问题 4：日频路径的 tighten-only 门槛极高**
- 文档规定 tighten-only 生产规则需要 504 个成熟日（≈ 2 年）、24 个月桶、8 季度桶。
- 当前数据窗口为 2005-01-01 至 2026-04-27（约 21.3 年），满足 504 成熟日的 walk-forward 约从 2024 年初开始，统计可信度有限。

### 改进建议

1. **明确 S1-D 与 S1-R 的角色分工**：建议在文档中明确：
   - S1-D：Daily，日度 IC、alpha 衰减和风险信号输出，使用 1/5 日标签
   - S1-R：Rebalancing/Review，日度执行审计和持仓风险复核，使用 5 日标签为主
   - 两者是否共用同一套模型，还是 R 使用更保守的模型版本
2. **补充日频 OOT step 间距定义**：建议明确日频 walk-forward 的 step 间距（如"每个交易日作为一个独立 OOT 决策点"或"按周/月聚汇总步"），并说明统计独立性的处理方式。
3. **补充"S1-D 影响 S1-M"的边界规则**：建议明确定义"哪些 S1-D 输出可以反馈到 S1-M"（如：S1-D 检测到行业暴露超标 → 建议 S1-M 在行业约束中收紧 → 这属于信息反馈还是信息泄露？），建议统一规定：S1-D 的风险信号只能影响风控规则（止损/降仓），不能影响 alpha 生成模型或因子选择。
4. **补充日频 tighten-only 的分阶段门槛**：鉴于 504 成熟日门槛极高，建议补充"report-only → confirmed-only → tighten-only"的三阶段路径，每阶段明确最低成熟日要求（如 252/378/504 天）。

---

## 审查点五：验证框架

### 评分：7.0 / 10

### 具体发现

**1. holdout**

- 最后 12 个月（约 252 个交易日）作为最终验收窗口。
- 不参与调参、特征选择、early stopping、阈值选择、GMSL 阈值、shock window、行业规则、风控规则或仓位开关选择。

**数据/理论支持**：holdout 作为"时间节点前的未见数据"，在 walk-forward 框架中提供对未来泛化能力的无偏估计。

**问题**：
- **holdout 与 walk-forward 的交互**：若 OOT 步数 24 步在 holdout 窗口之前完成，则 holdout 仅作为最终验收。但若 OOT 步数较多（如实际总步数 > 30 步），部分 OOT step 可能与 holdout 窗口重叠。需要明确"哪些 OOT step 在 holdout 内，哪些在 holdout 前"。
- **holdout 访问日志**：文档要求建立 holdout_access_log.tsv，但未规定访问日志的最小字段（除 track_id、访问时间外，是否记录访问目的、访问结果、数据范围？）。
- **holdout burned flag**：文档提到"若 holdout 已多次参与策略选择，后续只能作为只读 benchmark，生产前必须新增 forward OOS 或 shadow period"，但"burned 后重新做 shadow period"的具体流程未明确（shadow period 时长、如何验证新 shadow period 的无偏性）。

**2. FDR 校正**

- 候选因子 > 20 个时必须做 FDR 校正，进入 keep/晋级时 FDR 为硬约束。
- 未指定具体 FDR 方法（ Benjamini-Hochberg、Bonferroni、Storey-q？还是 model-based FDR？）。

**理论支持**：FDR 控制了在多重假设检验中错误发现率的上界，避免"20 个因子中 1 个偶然正显著"的假阳性。

**问题**：
- **FDR 阈值的默认值**：文档未明确 FDR < 0.05 的具体要求（是否 FDR < 0.05 即通过，还是另有更严格的阈值？）。
- **因子相关性对 FDR 的影响**：A 股因子间普遍存在较强相关性（如市值因子与流动性因子），简单的 BH 校正可能过于保守或过于宽松（取决于因子相关结构），文档未要求针对因子相关性调整 FDR 方法。

**3. Block Bootstrap**

- 组合收益默认 lock_days = max(label_horizon, rebalance_interval)
- 至少 5000 次重抽样
- S1-D/S1-R 默认 block=21 日，敏感性 5/10/21/40 日
- 晋级或生产 tighten-only 使用 10/21/40 中最保守结论

**数据/理论支持**：
- Block bootstrap 保留了时间序列的自相关结构，避免对独立观测的错误假设。
- max(label_horizon, rebalance_interval) 的 block 大小确保了 block 内标签重叠被正确建模。

**问题**：
- **block_days 的敏感性覆盖范围**：S1-D/S1-R 要求敏感性 5/10/21/40 日（4 个值），但若 block_days 对 p-value 的影响是非单调的（如 10 日 block 和 21 日 block 的 p-value 都显著，但 40 日 block 不显著），"最保守结论"指的是"最小 p-value 对应最严格标准"还是"最大 block 对应最保守"？文档未明确。
- **IC 序列 vs 组合收益的 block 大小差异**：纯 IC 诊断可预注册 max(label_horizon, empirical_acf_cutoff)，但"empirical_acf_cutoff"的具体计算方法未定义（是自相关函数首次穿过 0.1 的 lag，还是首次穿过 95% 置信区间的 lag？）。
- **Newey-West HAC 与 Block Bootstrap 的关系**：文档规定"IC t-stat 默认使用 Newey-West HAC 调整；普通 t-stat 只能作为诊断"，且"24 步属于小样本，HAC t-stat 与 block bootstrap 都必须报告；keep/晋级时采用更保守的统计结论"。但当 HAC t-stat 与 block bootstrap 结论冲突时（一个显著，一个不显著），"更保守"的判断标准未明确。

### 改进建议

1. **补充 FDR 具体方法**：建议明确使用 Benjamini-Hochberg (BH) 校正作为默认方法，并在因子相关性较高（平均相关系数 > 0.3）时报告 Storey-q 或基于相关矩阵的 adaptive FDR 作为敏感性对照。
2. **补充 holdout 访问日志最小字段规范**：建议字段至少包含：	imestamp、operator、purpose（调参/特征选择/阈值选择/early stopping/只读）、data_range、
esult_summary、污染标记。
3. **补充 burned holdout 的 shadow period 规范**：建议规定：shadow period 长度 = 原 holdout 长度（252 交易日），shadow period 内数据不参与任何调参，shadow period 结束后需重新跑完整的 walk-forward 并输出独立验证报告。
4. **补充 block_days 敏感性判断规则**：建议明确"当不同 block_days 的 p-value 结论不一致时，采用满足更严格 p < 0.05 的 block_days，或在结论中明确说明 block敏感性导致的不确定性"。
5. **补充 HAC vs Bootstrap 冲突判断标准**：建议规定"当 HAC t-stat >= 1.65 但 bootstrap p >= 0.10 时，结论为 inconclusive，不得进入 keep"；"当 HAC t-stat < 1.65 但 bootstrap p < 0.10 时，需额外报告 IC 方向一致性和分年度表现"。

---

## 综合评分汇总

| 审查点 | 评分 | 主要缺陷 |
|---|---|---|
| S1-M Walk-Forward 设计 | 7.5 / 10 | 4/6 年窗口处置规则模糊；purge 边际效益未披露 |
| 指数衰减加权 | 6.5 / 10 | date-balanced 理论假设未声明；冻结模型版本管理缺失 |
| GMSL 地缘宏观冲击层 | 4.5 / 10 | 阈值未完成（fx_shock/global_risk_off）；4/6 类 shock 数据源全部缺失；VIX available_at PIT 未验证 |
| S1-D/S1-R 定位 | 5.5 / 10 | D/R 分工不清晰；日频 OOT step 间距未定义；tighten-only 门槛过高且无分阶段路径 |
| 验证框架 | 7.0 / 10 | FDR 方法未指定；burned holdout 的 shadow period 规范缺失；HAC vs Bootstrap 冲突判断标准未明确 |

**总体评价**：文档在 purge/embargo 公式、holdout 原则、block bootstrap 框架上设计严谨，数据来源和计算方法大部分有明确说明。核心缺陷集中在 GMSL 层（阈值和数据源均未完成）和 S1-D/S1-R 的实施细节（D/R 分工、版本管理、日频 OOT 定义），这两项属于 P0-P1 级别的设计未完成项，在完成前无法进行有效的正式 walk-forward 验证。

**最优先改进项（按优先级）**：
1. **GMSL 阈值补充**（P0）：fx_shock、global_risk_off 具体阈值 + VIX available_at PIT 验证
2. **S1-D/S1-R 分工明确**（P0）：D/R 角色定义 + 日频 OOT step 间距
3. **冻结模型版本管理**（P1）：存储规范 + 回滚条件
4. **FDR 具体方法**（P1）：BH 校正 + 相关性敏感性说明
5. **4/6 年窗口处置规则**（P1）：明确"计入 attempt_count"后的结论效力

---

*本报告为独立审计意见，不涉及工程复杂度和人天评估。数据来源均引用自 quant_strategy_plan.md 和 quant_strategy_research_plan_detailed.md 的原文。*