# 量化策略研究计划评审意见报告（共识版）

> 评审日期：2026-05-01
> 评审方法：四位专家独立审计（R1）+ 交叉审阅与质证（R2）+ 共识裁决
> 评审人：Main Agent（金融工程/量化策略/ML/DL/架构设计）、Review Agent（量化策略/代码review）、DeepSeek Agent（量化策略/深度学习/金融工程）、Coder Agent（量化开发/数据工程/架构设计）
> 审计对象：quant_strategy_plan.md（总纲）、quant_strategy_research_plan_detailed.md（执行规范）
> 数据依据：DATA_USAGE_GUIDE.md、WAREHOUSE_README.md、external_data_sources.csv

---

## 一、评审流程

| 轮次 | 内容 | 产出 |
|---|---|---|
| R1 | 四位专家独立审计，各自写出完整审计报告 | 4份独立审计报告（main_agent_audit.md, review_agent_audit.md, deepseek_agent_audit.md, coder_agent_audit.md） |
| R2 | 交叉审阅与质证：每位专家阅读其他三位的报告，给出认同/反对/遗漏判断 | 3份R2报告（review_agent_r2.md, deepseek_agent_r2.md, coder_agent_r2.md）+ Main Agent R2回应 |
| 裁决 | Main Agent 对所有分歧进行最终裁决 | 本共识报告 |

---

## 二、总体评价

| 评审人 | R1评分 | R2修正评分 | 核心评价 |
|---|---|---|---|
| Main Agent | 8.0/10 | 8.0/10 | 治理框架和验证体系达专业水平，主要改进空间在参数量化和执行节奏 |
| Review Agent | 7.5/10 | 7.0/10 | R2发现更多遗漏问题（数据供应商PIT、风险模型规格），下调评分 |
| DeepSeek Agent | 8.0/10 | 8.0/10 | 高标准高纪律性，多重检验校正和标签misalignment是关键发现 |
| Coder Agent | 7.5/10 | 7.5/10 | 工程可行性评估扎实，Phase A0工作量估算最有依据 |
| **共识评分** | **7.8/10** | **7.6/10** | **R2发现更多问题后小幅下调，整体优秀，具备落地基础** |

---

## 三、四方共识（所有评审人一致同意）

### 共识 1：GMSL 数据基础严重不完整 [P0]

**现状**：GMSL 仅完成 Cboe VIX/OVX/GVZ 候选源入仓（17,526行），FRED 全部超时，geopolitical_event_calendar 0 行。

**共识结论**：
- GMSL 当前只能作为概念框架
- **GMSL-v1**：基于现有 VIX/OVX/GVZ + 国债收益率 + Shibor，输出简单 stress report
- **GMSL-v2**：完整外生冲击层，需 FRED 替代方案（fredapi/Quandl/Nasdaq Data Link）
- GMSL 阈值使用训练窗口内分位数 + 10 年 lookback（遵守 walk-forward 原则）

### 共识 2：Phase A0 工作量被严重低估 [P0]

**四方估算**：

| 评审人 | 估算 |
|---|---|
| Main Agent | 20-30 工作日（R1）→ 接受 25-45 天（R2） |
| Review Agent | 17-27 工作日 |
| Coder Agent | 25-45 工作日 |
| DeepSeek Agent | 未给出具体估算 |

**共识结论**：Phase A0 约 **25-45 工作日**。建议分为 A0.1（阻塞S1启动）和 A0.2（阻塞S1 keep）：
- **A0.1（2-3周）**：walk-forward calendar（5-8天）、track registry（1-2天）、validation_params.json 更新（1天）、universe_daily_construction_audit（3-5天）
- **A0.2（3-6周）**：execution_label_audit（5-10天）、orders_audit（5-8天）、daily_turnover_capacity_report（3-5天）、experiment_ledger SQLite（2-3天）

### 共识 3：Walk-forward Calendar 是系统基石 [P0]

**共识结论**：
- Walk-forward calendar 的 purge/embargo 计算必须精确到交易日
- 先实现 S1-M 的月频 calendar，验证正确性后再扩展到 S1-D/S1-R
- 实现 WalkForwardCalendarValidator，验证 purge 约束、holdout 隔离、标签成熟度、窗口重叠率
- S1-M 和 S1-D 使用独立 calendar 文件，通过 track_id 关联

### 共识 4：Concept Shift 状态机误报率过高 [P0]

**现状**：yellow 告警阈值为"最近6步中至少4步IC<0"，零假设下误报率约 34.4%。

**R2 讨论**：
- DeepSeek 建议"6步中3步+连续性检验"（介于34%和10.9%之间）
- Review/Main 建议"6步中5步为负"（10.9%）
- Coder 建议"8步中6步为负"（10.9%等价）

**裁决结果**：**最近6步中至少5步IC<0**（误报率约10.9%）。理由：
- 34% 误报率不可接受（约1/3的因子会被误标）
- DeepSeek 的"3步+连续性"增加实现复杂度但收益不明确
- 5/6 简洁、可实现、误报率可控

### 共识 5：24 步 OOT 只是 Smoke Test [P1]

**R2 修正**：Main Agent R1 将此定为 P0，R2 修正为 P1（混淆了 walk-forward 滑动步数和 OOT 评估步数）。

**共识结论**：
- 24 步是最低验收门槛，不是完整验证
- S1-M 完整 OOT 步数约 **180 步**（2005-2026，月末调仓，扣除 holdout）
- 建议将 24 步定义为"Phase A0 快速 smoke test"，180 步定义为"Phase A 完整验证"
- 文档需明确区分 walk-forward 滑动步数、OOT 评估步数、rebalance 步数

### 共识 6：实验台账需升级 [P1]

**共识结论**：TSV 格式升级为 **SQLite**（WAL 模式支持并发写入），DuckDB 用于只读分析查询。字段分四层：
- 核心层（约15字段必填）：run_id、track_id、label_id、hypothesis、commit、status、decision
- 验证层（约20字段自动填充）：IC t-stat、bootstrap p、Sharpe、max_drawdown
- 审计层（约15字段自动填充）：leak_audit_status、pit_factor_audit_status
- 元数据层（约20字段自动填充）：各种 hash

### 共识 7：估值因子 PIT 维持 P1 [P1]

**R2 讨论**：Review R1 认为"可能被高估"，R2 修正为"不应降级"。

**共识结论**：
- 供应商处理方式不透明，"可能已处理"不等于"已确认处理"
- S1 启动前必须完成 `available_at` 审计：随机抽取50只股票，对比财报公告日与估值更新日
- 在验证完成之前，PE/PB 归为 `financial_statement_dependent_unverified_pit`

### 共识 8：多重检验校正范围需扩展 [P0, R2新增]

**DeepSeek R2 发现**：30因子 × 5模型 × 3标签 = 450种组合，5%显著性下约22个假显著。

**共识结论**：
- FDR 应覆盖"因子 × 标签 × 模型 × 半衰期 × 训练窗口"的完整实验族
- 使用 `test_family_id` 机制，记录每个 family 的总尝试次数
- `attempt_count` 必须跨整个实验族累计

### 共识 9：标签-持有期 Misalignment 是 P0 [P0, R2升级]

**DeepSeek R2 发现**：20日标签 vs 月度调仓（18-23天变异）存在 silent failure。

**共识结论**：
- 增加"调仓日到调仓日"的 execution-aligned 标签作为对照
- 在 execution_label_audit 中量化 misalignment 对 IC 和 PnL 的影响
- 如果 misalignment 影响显著，调整标签定义为"调仓间隔收益"而非固定20日

---

## 四、关键分歧裁决

### 裁决 1：1 日标签 Purge 规则

| 立场 | 来源 |
|---|---|
| 40天（原文） | 总纲/执行规范 |
| 5天 | Review Agent R2 |
| 10天 | DeepSeek Agent R1（R2接受20天） |
| 20天 | Main Agent R1 + Coder Agent + DeepSeek Agent R2 |

**裁决结果：20天**

**依据**：
- 5天过于激进，无法覆盖 A 股 microstructure 效应
- 10天忽略了特征自相关导致的信息泄漏
- 20天额外成本很小（损失约1.6%样本），安全边际显著更高
- 报告 10/20/40 天 purge 的敏感性

### 裁决 2：Block Bootstrap 的 block_days

| 立场 | 来源 |
|---|---|
| max(label_horizon, rebalance_interval) = 21天 | 原文 |
| empirical ACF | DeepSeek R1（R2修正为固定block=6） |
| empirical ACF + 敏感性 {21,42,63} | Review Agent R2 |

**裁决结果：默认21天 + 敏感性报告{10,21,42}**

**依据**：
- DeepSeek R2 正确指出24步小样本下 empirical ACF 不可靠（标准误≈0.204）
- 21天基于标签horizon和rebalance interval，有明确理论依据
- 敏感性报告{10,21,42}覆盖不同自相关假设

### 裁决 3：因子方向预注册

| 立场 | 来源 |
|---|---|
| 全部预注册 | DeepSeek Agent R1（R2接受分级） |
| 分高置信/探索性 | Main Agent R1 |
| Tier 1/2/3 分类 | Review Agent R2 + DeepSeek Agent R2 |

**裁决结果：Tier 1/2/3 分层管理**

**执行方案**：
- **Tier 1（高置信）**：3+篇独立文献支撑 → 预注册方向，单侧检验（p<0.025）
  - 市值、价值（EP/BP）、流动性、短期反转
- **Tier 2（中置信）**：1-2篇文献或强经济学逻辑 → 预注册方向但保留翻转检查
  - 动量、波动率
- **Tier 3（探索性）**：无文献先验 → 双侧检验（p<0.01），限测2个方向
- **红线**：OOT阶段不允许调整因子方向

### 裁决 4：Newey-West 带宽

**裁决结果：增加 Andrews (1991) 自动带宽敏感性**

**执行方案**：
- 在 validation_params.json 中增加 `nw_bandwidth_sensitivity` 字段
- 报告四种带宽下的 t-stat：`default_formula`、`andrews_1991`、`lag_6`、`lag_12`
- keep 决策使用最保守结论

### 裁决 5：换手率控制三层规则冲突

**裁决结果：优先级规则 3>2>1 + 分层裁剪算法**

**执行方案**：
1. 计算理想调仓权重
2. 应用规则3（总换手率上限），等比例缩减
3. 应用规则2（行业上限），对超限行业等比例缩减
4. 应用规则1（个股上限），对超限个股等比例缩减
5. 重新归一化

### 裁决 6：Gram-Schmidt 正交化顺序

**裁决结果：V1 固定顺序，V2 考虑 PCA**

**执行方案**：
- 在所有 walk-forward step 中使用相同的因子顺序
- 顺序基于经济逻辑重要性：市场因子 > 行业因子 > 风格因子 > alpha因子
- 报告正交化顺序在各 step 间的一致性（Spearman rank correlation）

### 裁决 7：其他改进项

| 项目 | 来源 | 裁决 |
|---|---|---|
| valuation缺口对holdout影响 | Main | holdout 验收同时报告 drop-gap 和 ffill 两种口径 |
| 停牌推断精度 | Main/Review | S1启动前用2023以来AkShare数据对比，报告 precision/recall |
| 冲击成本模型 | DeepSeek | S1阶段至少报告 square-root impact model 结果 |
| orders_audit 字段 | Coder | S1实现：execution_price、slippage、order_status；S1.5补充：cost_breakdown、prev_weight、turnover_contribution |
| FRED 替代方案 | Coder | 调研 fredapi、Quandl/Nasdaq Data Link |
| 数据版本控制 | Review/Coder | warehouse 版本号 + content hash + panel hash |
| 停牌期间因子处理 | Review | 明确停牌期间因子值处理规则（forward-fill or skip） |
| Alpha 衰减 vs concept shift | Review | 分别监控：滚动6月IC趋势检测（衰减）+ 状态机（shift） |
| refit/rebalance不同步 | Coder | 模型版本注册表（ModelRegistry），calendar增加 model_refit_flag 和 frozen_model_version |
| Phase A0 工作量 | Coder | 25-45 工作日，分为 A0.1（2-3周）和 A0.2（3-6周） |

---

## 五、策略计划改进建议

### 5.1 总纲（quant_strategy_plan.md）改进

1. **§1.1 数据底座**：增加 2026 估值缺口对 holdout 的影响说明，明确 holdout 验收允许 forward-fill 的条件
2. **§1.4 执行规则**：增加"1日标签 purge 默认20天，报告10/20/40敏感性"
3. **§4.1 第一阶段模型**：增加"事件触发重训"机制（GMSL red 或 IC 连续3步为负）
4. **§5.5 验证参数**：
   - 明确 S1-M 预期 OOT 步数约 180 步（非 24 步），24 步为 smoke test
   - 增加 Newey-West 带宽敏感性参数（Andrews 自动带宽）
   - 增加 block bootstrap block_days 敏感性报告{10,21,42}
5. **§5.5 Concept Shift**：将 yellow 门槛从"6步中4步"提高到"6步中5步"（误报率从34%降至11%）

### 5.2 执行规范（quant_strategy_research_plan_detailed.md）改进

1. **§4.1 默认标签**：修改 1 日标签 purge 为 `max(label_horizon*5, 20)` = 20天
2. **§5.1 P1 核心因子**：
   - 为 Tier 1 因子（市值、价值、流动性、短期反转）预注册方向
   - 增加因子计数口径说明（按独立信息来源计数）
   - 增加行业默认分类标准（建议申万一级）
3. **§7.1 默认验证**：
   - 增加 block bootstrap 敏感性报告{10,21,42}
   - 增加 Newey-West Andrews 自动带宽敏感性
   - 明确 refit/rebalance 不同步时的模型版本管理规则
4. **§9.1 S1 启动前置条件**：
   - 将 Phase A0 分为 A0.1（阻塞启动）和 A0.2（阻塞 keep）
   - 为每个产出项估算工作量
5. **§11 实验台账**：TSV 升级为 SQLite（WAL 模式），定义四层字段结构
6. **orders_audit 字段**：补充 execution_price、execution_slippage、order_status

### 5.3 数据依据文档改进

1. **DATA_USAGE_GUIDE.md**：
   - 增加估值缺口对 holdout 影响的说明
   - 补充停牌推断精度验证方法
   - 增加冲击成本 square-root model 说明
   - 明确数据供应商并验证 PIT 处理逻辑
2. **external_data_sources.csv**：
   - 为 FRED 超时源标记替代方案（fredapi/Quandl）
   - 增加 `planned` 状态区分"已有ETL脚本"和"连ETL脚本都没有"

---

## 六、工程实施路线建议

### Phase A0.1：S1 启动最小集（2-3 周）

| 产出物 | 复杂度 | 工作量 | 依赖 |
|---|---|---|---|
| track_registry_v1 | 低 | 1-2天 | 无 |
| walk_forward_calendar_S1M_v1 | **高** | 5-8天 | exchange_calendar, validation_params.json |
| WalkForwardCalendarValidator | 中 | 1-2天 | walk_forward_calendar |
| validation_params.json 更新 | 低 | 1天 | 无 |
| universe_daily_construction_audit | 中 | 3-5天 | universe_daily 构造脚本 |
| valuation_coverage_audit | 中 | 1-2天 | valuation_daily, prices_daily_returns |
| suspension_inference_validation | 中 | 1天 | tradability_daily, AkShare official |
| available_at 审计（估值因子PIT） | 中 | 1-2天 | valuation_daily, 财报公告日 |

### Phase A0.2：S1 keep 完整集（3-6 周）

| 产出物 | 复杂度 | 工作量 | 依赖 |
|---|---|---|---|
| execution_label_audit | **高** | 5-10天 | prices_daily_unadjusted, tradability_daily, trading_costs |
| orders_audit | **高** | 5-8天 | execution_label_audit |
| daily_turnover_capacity_report | 中 | 3-5天 | orders_audit, tradability_daily |
| experiment_ledger (SQLite) | 中 | 2-3天 | 无 |
| factor_direction_registry | 低 | 1天 | 无 |
| ModelRegistry | 中 | 2-3天 | 无 |
| 数据版本控制机制 | 中 | 1-2天 | manifest/hash |

### Phase A：S1 完整验证（6-12 周）

| 阶段 | 内容 | 预计耗时 |
|---|---|---|
| A-M Step 1 | 单因子 IC/RankIC/ICIR | 2-3 周 |
| A-M Step 2 | 等权/ICIR/正交化复合因子 | 1-2 周 |
| A-M Step 3 | 线性/GBDT/Ranker 对照 | 2-3 周 |
| A-M Step 4 | 组合回测 + 成本/容量 | 2-3 周 |
| A-R | 日频风险/执行主线（并行） | 3-4 周 |

---

## 七、风险提示

1. **最大风险**：P0 治理工件全部 missing，S1 无法正式启动。Phase A0 的完成质量直接决定后续所有结论的有效性。
2. **统计风险**：24 步 OOT 的有效独立样本量因 95% 训练窗口重叠率远小于 24。完整 180 步验证才能产生可靠结论。
3. **数据风险**：GMSL 数据严重不完整，concept shift 检测和外生冲击分析只能基于有限数据。
4. **工程风险**：walk-forward calendar 和 orders audit 的实现复杂度被严重低估，任何 purge/embargo 计算错误都会导致后续结论无效。
5. **过拟合风险**：多标签×多模型×多半衰期×多训练窗口的组合搜索会产生巨大多重比较问题（450种组合下约22个假显著），attempt_count 和 test_family_id 机制必须严格执行。
6. **Silent failure 风险**：标签-持有期 misalignment 不会在回测中报错，但会系统性降低实盘表现。

---

## 八、评审结论

本策略计划在**治理框架和验证体系上达到了专业量化基金的水平**，在 PIT 审计、holdout access log、experiment ledger、三层 universe 分离等方面甚至更为严格。核心优势在于：
- 数据治理严格（canonical 数据源、manifest/hash 追踪、leakage check）
- 验证纪律强（purge/embargo + HAC/bootstrap 双重门槛 + FDR + DSR/PBO）
- 自我纠正意识强（qant 随机 8/2 的 label leakage 诊断和修正）
- 渐进式设计（market-only → 外部数据，日频保守 → 分钟精细，report-only → tighten-only）

主要改进空间集中在：
1. **降低概念 shift 状态机误报率**（从34%降至约11%）
2. **明确 Phase A0 的执行节奏和工作量**（25-45工作日，分为A0.1和A0.2）
3. **补齐 GMSL 数据基础**（FRED替代方案）
4. **升级实验台账**（TSV → SQLite）
5. **扩展多重检验校正范围**（覆盖完整实验族）
6. **修复标签-持有期 misalignment**（增加 execution-aligned 标签）

**总体判断**：计划整体方向正确，具备落地基础。严格执行并落实上述改进后，有较大概率产出**稳健、可复现、可审计**的策略结论。

---

*本报告由四位专家独立审计（R1）+ 交叉审阅与质证（R2）后达成共识，所有观点均有事实/数据/理论支持。*
