# 量化策略文档评审意见

> 审计日期：2026-05-01
> 审计对象：更新后的 quant_strategy_plan.md 和 quant_strategy_research_plan_detailed.md
> 审计依据：DATA_USAGE_GUIDE.md、WAREHOUSE_README.md

---

## 一、需修正项（P0）

### 1. CSRP命中窗口未定义

**问题**：§9.1.5 定义了 CSRP 误报率公式 `false_positive_rate = 1 - hit_rate`，但未定义"命中"的窗口长度和判定标准。没有命中窗口定义，`hit_rate` 的分子分母无法计算，整个误报率监控框架无法执行。

**修正建议**：

| 参数 | 定义 |
|---|---|
| 命中窗口 | 信号触发后 3 个 OOT step（约 3 个月） |
| 命中标准（主口径） | 3 步中至少 2 步的组合收益（扣除成本后）< benchmark 收益 |
| 命中标准（辅助报告） | 3 步中至少 2 步的成熟 IC < 0 |
| 排列检验 | ≥ 1000 次 block permutation（block = 21 天） |
| 最小信号数 | n_signals ≥ 5 才报告点估计，≥ 20 才作为 tighten-only 依据 |
| 敏感性 | 2-step / 3-step / 5-step 窗口 |

**原因**：
- CSRP 信号基于 6 个 OOT step 的连续 IC < 0，用 3 个 OOT step 验证中期趋势是否持续，时间尺度匹配
- 仅用 IC < 0 作为命中标准会导致自相关下的自证预言（IC 自相关使"IC<0 之后 IC 继续<0"的概率天然偏高）
- 组合收益 < benchmark 直接衡量投资者体验，是更合适的监控指标
- block permutation 保留信号的时序聚类结构，简单 shuffle 会破坏 CSRP 信号的自相关

### 2. 分层裁剪与 capital overlay 执行顺序未定义

**问题**：§7.1 定义了分层裁剪规则，§9.3 定义了 capital overlay，但未规定两者的执行顺序。不同的执行顺序会导致不同的换手计算和最终权重。

**修正建议**：

```
Step 1: 模型生成目标权重（满仓，总和 = 1.0）
Step 2: 分层裁剪（总换手 → 行业 → 个股），每层等比例缩减
Step 3: 归一化到 1.0
Step 4: 乘 capital_multiplier（牛市 0.8-1.0 / 震荡 0.4-0.7 / 熊市 0-0.3）
Step 5: 现金 = 1 - sum(w_final)
```

代码中用断言强制顺序：`assert abs(sum(w_clipped) - 1.0) < 1e-6 before overlay`

**原因**：
- 先 overlay 再裁剪会低估换手。例如：旧权重 A=50%/B=50%，新权重 A=30%/B=70%，理想换手 = 40%。先 overlay (×0.5) 后换手被低估为 20%
- 裁剪后归一化确保 overlay 的语义清晰：multiplier 直接表示满仓比例（0.8 = 80% 满仓）
- 裁剪只影响股票间相对权重，overlay 只影响总敞口，两者互不干扰

### 3. Sleeve FDR 计入规则未明确

**问题**：§3.1.1 定义了 5 个分层 sleeve，但未明确 sleeve 的尝试是否计入 FDR 实验族。如果 5 个 sleeve 独立计入，BH 校正的 p 值阈值会收紧约 5 倍（从 0.02 降至 0.004）。这个影响不是"可控"的——p 值在 0.004-0.02 之间的因子会被淘汰。

**修正建议**：
- 所有 sleeve 的尝试计入 `attempt_count`，共享 `test_family_id`
- BH 校正在整个实验族上执行
- 实验报告必须披露："本次实验族包含 N 个 sleeve，BH 校正后的 p 值阈值为 X"
- 如果 5× 收紧过于严格：减少 sleeve 数量，或使用 Storey-q 替代 BH

**原因**：
- FDR 校正的目的是控制"在所有被检验的假设中，错误拒绝零假设的比例"
- 关键不是"是否独立训练模型"，而是"是否做出独立的 keep 决策"
- 每个 sleeve 都是一个独立的假设（如"P80-P95 分段是否有 alpha"），即使共享同一个模型
- 类比：药物临床试验中，即使共享同批数据，5 个亚组的假设检验仍需多重比较校正

---

## 二、需修正项（P1）

### 4. MDE 功效分析缺失

**问题**：文档在 §5.5、§9.1 中多处使用 24 步 OOT 做判断（exploratory tracking 的 65% 方向一致性、concept shift 的 5/6 门槛），但未评估 24 步 OOT 的统计功效。24 步 OOT 对年化 Sharpe = 0.5 的 alpha 功效仅约 17%，意味着 83% 的概率会漏掉一个真实的中等 alpha。

**修正建议**：在 §5.5 增加功效分析表：

| 年化 Sharpe | IC 均值 (σ=0.06) | 24 步功效 | 180 步功效 |
|---|---|---|---|
| 0.3 | 0.0052 | 8.5% | 28% |
| 0.5 | 0.0087 | 17.4% | 58% |
| 0.8 | 0.0139 | 32.6% | 87% |
| 1.0 | 0.0173 | 43.3% | 95% |
| 1.5 | 0.0260 | 68.8% | 99.7% |

同时在 validation_params.json 中记录 MDE 分析的假设和结论。

**原因**：
- 24 步 OOT 是最低验收门槛（smoke test），不是总步数。完整 OOT 约 180 步，功效充足
- 功效分析不阻塞 S1 启动，但量化了框架的能力边界，影响对 smoke test 结果的解读方式
- 如果 smoke test 不通过但完整 OOT 的 MDE 低于预期 alpha，应等待更多步数而非立即放弃

### 5. Concept shift 5/6 门槛的理论解释需修正

**问题**：§4.1 声称 5/6 yellow 门槛的误报率为 10.9%，基于 IC 步间独立假设（二项分布）。但 walk-forward 中 IC 存在正自相关（因训练窗口 95% 重叠），正自相关**降低**零假设误报率（实际约 2-5%），但同时降低检测真实 concept shift 的功效。文档当前的理论解释方向有误。

**修正建议**：§4.1 增加说明：

> "5/6 yellow 门槛的 10.9% 误报率基于 IC 步间独立假设。实际 walk-forward 中 IC 存在正自相关（因训练窗口重叠），正自相关**降低**极端序列（连续 5-6 步同号）的概率，实际误报率约 2-5%（比预期更保守）。但正自相关同时降低检测真实 concept shift 的功效——6 步窗口在自相关下可能不足以检测渐进式策略失效。"

OOT 报告中必须同时报告 IC lag-1 自相关系数 ρ。如果 ρ > 0.3：
- 用 block bootstrap（block = 21 天，≥ 5000 次重采样）估计实际误报率和功效
- 如果功效 < 50%，标注 "inconclusive - insufficient power"，建议增加 OOT 步数或放宽门槛（如 4/6）

**原因**：
- 正自相关使 IC 序列更"平滑"，在零假设下更难出现连续 5-6 步同号的极端聚集
- 但正自相关也使 IC 变化更慢，真实 concept shift 发生时 6 步内可能只有 3-4 步为负，无法触发告警
- 功效不足（漏报）比误报率偏高（过度告警）更危险——过度告警只触发报告，漏报意味着策略在 regime change 中继续运行而不被告警
- 功效不足时应**放宽**门槛（如 4/6）来提高检测能力，而非收紧（如 6/6）

### 6. SQLite 实验台账缺少 schema 定义

**问题**：§11 提及 SQLite WAL 实验台账，但未给出 CREATE TABLE 语句、索引定义和 WAL 配置。没有 schema 定义，无法实现。

**修正建议**：补充 `experiment_runs` 表的 schema，至少包含：
- `run_id TEXT PRIMARY KEY`
- `test_family_id TEXT`
- `track_id TEXT`
- `sleeve_id TEXT`（默认 NULL）
- `factor_id TEXT`
- `label_id TEXT`
- `model_id TEXT`
- `trial_index_in_family INTEGER`
- `ic_mean REAL`
- `ic_pvalue REAL`
- `bh_adjusted_pvalue REAL`
- `keep_decision TEXT`
- `created_at TEXT`

配置 `PRAGMA journal_mode=WAL` 和 `PRAGMA synchronous=NORMAL`。

**原因**：schema 是实现的前提，没有 schema 无法写入实验记录，也无法执行 BH 校正。

### 7. IC 自相关报告要求

**问题**：OOT 报告中未要求报告 IC lag-1 自相关系数。IC 自相关影响 concept shift 门槛的实际误报率和功效，不报告则无法评估门槛的可靠性。

**修正建议**：在 §9.1.5 增加：OOT 报告必须同时报告 IC lag-1 自相关系数 ρ。如果 ρ > 0.3，触发 block bootstrap 功效分析。

**原因**：IC 自相关是 concept shift 检测的关键参数，直接影响 5/6 门槛的实际行为。

### 8. ModelRegistry 持久化方案缺失

**问题**：§8.4 提及 ModelRegistry 管理 refit/rebalance 不同步，但未给出持久化方案（SQLite + 文件系统）和 artifact 存储结构。

**修正建议**：补充 ModelRegistry 的存储结构：
- SQLite 表存储模型元数据（model_id、track_id、refit_date、rebalance_date、artifact_path）
- 文件系统存储模型 artifact（pickle/joblib），路径写入 SQLite

**原因**：没有持久化方案，refit 和 rebalance 的不同步管理无法实现。

### 9. Sleevecross 比较应计入 FDR

**问题**：§5.1 未明确 sleeve 间的交叉比较（如微盘 vs 大盘 sleeve 的 IC 差异）是否计入 FDR。

**修正建议**：sleeve 共享基础因子方向的 `test_family_id`，不独立成族。但 sleeve 间的交叉比较（IC 差异检验）应作为独立假设计入 FDR。

**原因**：sleeve 间比较是一个新的假设检验，即使底层模型相同。

---

## 三、文档一致性确认

以下项目在两份文档中已一致，无需修改：

| 检查项 | 状态 |
|---|---|
| purge 规则（20日标签=60天，1日标签=20天） | ✅ 一致 |
| OOT 步数（24步为smoke test，~180步为完整验证） | ✅ 一致 |
| Concept shift 阈值（5/6步触发yellow） | ✅ 一致 |
| 因子方向 Tier 1/2/3 | ✅ 一致 |
| Phase A0 拆分（A0.1 + A0.2） | ✅ 一致 |
| 实验台账（SQLite WAL） | ✅ 一致 |
| 半衰期（12月默认，18月敏感性，6/24诊断） | ✅ 一致 |
| GMSL（S1报告，S1.5审计，S3后tighten-only） | ✅ 一致 |
| Block bootstrap 敏感性（10/21/42日） | ✅ 一致 |
| 新ey-West 带宽（Andrews + lag 6 + lag 12） | ✅ 一致 |

---

## 四、修正优先级

| 优先级 | 修正项 | 预计工作量 |
|---|---|---|
| P0 | CSRP 命中窗口定义 | 补充一段定义 |
| P0 | 裁剪与 overlay 执行顺序 | 补充一段定义 + 代码示例 |
| P0 | Sleeve FDR 计入规则 | 补充一段定义 |
| P1 | MDE 功效分析表 | 补充一个表格 + 一段说明 |
| P1 | Concept shift 理论修正 | 修改 §4.1 的理论解释段落 |
| P1 | SQLite schema DDL | 补充 CREATE TABLE 语句 |
| P1 | IC 自相关报告要求 | 在 §9.1.5 增加一句要求 |
| P1 | ModelRegistry 持久化 | 补充存储结构说明 |
| P1 | Sleeve 间比较 FDR | 在 §5.1 增加一句说明 |

---

*评审完成时间：2026-05-01 13:24 CST*
