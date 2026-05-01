# 多专家共识讨论 — Round 1

> 参与方：Main Agent、Review Agent、DeepSeek Agent、Coder Agent
> 日期：2026-05-01

---

## 一、四方共识（所有 agent 一致同意）

### 共识 1：GMSL 数据基础严重不完整（P0 阻塞）
- **Main**：GMSL 只有 VIX/OVX/GVZ，geopolitical_event_calendar 0 行，短期无法产生实际价值
- **Review**：GMSL 数据严重不完整（FRED 全部超时）
- **DeepSeek**：GMSL 数据覆盖严重不足是当前最大阻塞，oil_shock/fx_shock/rate_shock 均无法计算
- **Coder**：GMSL 数据严重缺失需要替代方案

**共识结论**：GMSL 当前只能作为概念框架，需要分阶段交付（v1 基于现有数据，v2 完整外生冲击层）。

### 共识 2：Phase A0 工作量被低估（P0 阻塞）
- **Main**：17 个产出项，估计 4-6 周
- **Review**：walk-forward calendar、holdout log、execution label audit 等 P0 治理工件全部 missing
- **DeepSeek**：P0 治理工件全部 missing，S1 正式启动前必须先完成
- **Coder**：Phase A0 纯工程实现 25-45 个工作日，walk-forward calendar、orders audit、execution label audit 是三个最高复杂度模块

**共识结论**：Phase A0 需要 4-9 周，应分为 A0.1（阻塞 S1 启动的最小集）和 A0.2（阻塞 S1 keep 的完整集）。

### 共识 3：Walk-forward Calendar 是系统基石（P0）
- **Coder**：这是整个系统中工程复杂度最高的单一组件
- **DeepSeek**：purge/embargo 精确性要求极高
- **Main**：建议 S1-M 和 S1-D 使用独立 calendar 文件

**共识结论**：Walk-forward calendar 的 purge/embargo 计算必须精确到交易日，任何错误都会导致后续所有结论无效。

### 共识 4：Concept Shift 状态机误报率过高（P1）
- **Main**：yellow 误报率约 34%（6 步中 4 步为负的概率）
- **DeepSeek**：同样计算，建议提高门槛到"最近 8 步中至少 6 步为负"或增加 effect size 要求

**共识结论**：yellow 告警阈值需要调整，当前 4/6 步为负的门槛会导致 1/3 的因子被误标为 yellow。

### 共识 5：实验台账 70+ 字段 TSV 不可维护（P2）
- **Main**：建议改为 SQLite/JSONL
- **Coder**：建议升级为 SQLite/DuckDB，支持 SQL 查询和 schema evolution
- **DeepSeek**：未直接评论但认同字段过多

**共识结论**：实验台账应升级为 SQLite 或 DuckDB。

### 共识 6：24 步 OOT 统计功效偏低（P1）
- **Main**：应明确预期总步数（约 180 步）
- **Review**：24 步 = 24 个月 ≈ 2 年 OOT 样本，统计功效偏低
- **DeepSeek**：24 步的有效独立样本量因 95% 训练窗口重叠率远小于 24

**共识结论**：24 步只是 smoke test，完整验证需要全量 OOT step（约 180 步）。

---

## 二、关键分歧（需要讨论）

### 分歧 1：1 日标签 purge 规则
- **DeepSeek**：1 日标签用 40 天 purge 过度保守，混淆了 label overlap 和信息泄漏。建议改为 `max(label_horizon*5, 10)` = 10 天
- **Main/Review**：未对此提出异议，文档原规则为"1 日标签也至少使用 40 个交易日 purge"

**辩论焦点**：1 日标签的信息泄漏风险到底有多大？A 股的日内自相关和 microstructure noise 是否支持更短的 purge？

### 分歧 2：Block Bootstrap 的 block_days 选择
- **DeepSeek**：IC 序列的 block_days 应基于 IC 的 empirical ACF，而非标签 horizon。IC 是横截面统计量，其自相关结构不同于收益序列
- **Main/Review**：按文档规则 `block_days = max(label_horizon, rebalance_interval)` = 21 日

**辩论焦点**：IC 序列的自相关结构是否与收益序列不同？如果是，block_days 应如何确定？

### 分歧 3：Refit（63日）和 Rebalance（月频）频率不同步
- **Coder**：两个频率不同步的处理未明确。当 refit 和 rebalance 不在同一天时，使用哪个模型版本？
- **Main/DeepSeek**：未对此提出异议

**辩论焦点**：是否需要同步 refit 和 rebalance 频率？还是用冻结模型版本管理解决？

### 分歧 4：因子方向是否需要预注册假设
- **DeepSeek**：因子方向假设缺乏先验支撑，A 股因子方向有 regime-dependent 特性
- **Coder**：未涉及
- **Main/Review**：未对此提出异议

**辩论焦点**：是否需要为每个因子预注册经济学机制和方向假设？

### 分歧 5：Newey-West 带宽选择
- **DeepSeek**：当前公式 `lag = max(1, floor(4*(n/100)^(2/9)))` 对小样本可能不足，建议增加 Andrews (1991) 自动带宽
- **Main/Review**：未对此提出异议

**辩论焦点**：当前带宽公式是否足够？是否需要额外敏感性？

---

## 三、请各方对以上分歧发表独立观点

请各 agent 基于事实和理论，对每个分歧点给出：
1. 你的立场（支持哪一方或提出新方案）
2. 事实/理论依据
3. 具体建议
