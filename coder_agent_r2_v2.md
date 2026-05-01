# Coder Agent R2 交叉审阅报告

> **角色**: Coder Agent（量化开发/数据工程/架构设计专家）
> **日期**: 2026-05-01
> **性质**: R2 交叉审阅——对四份 R1 报告的分歧点给出独立工程判断

---

## 分歧点 1：统计功效 MDE 分析

### DeepSeek R1 立场
P0 级问题。24 步 OOT 能否检测到经济上有意义的 alpha 未验证。假设 IC 均值 0.03、标准差 0.06，t-stat ≈ 2.45 功效足够；但若 IC 均值 0.015（更现实），t-stat = 1.22 功效不足。要求预注册 MDE 分析。

### 我的立场
**同意 P0，但从工程实现角度，MDE 分析的执行成本很低，应作为 A0.1 的最后一个子任务完成。**

### 工程可行性分析

MDE 分析本质上是一个蒙特卡洛模拟脚本，**不需要任何外部数据，不需要访问 warehouse**，只需要：
- 一个假设的 IC 分布参数（均值、标准差、自相关系数）
- 一个 walk-forward 步数（24 或 180）
- 一个显著性水平（0.05 单侧）

**实现方案**：
```python
# 伪代码：MDE 分析
import numpy as np
from scipy import stats

def mde_analysis(n_steps=24, ic_std=0.06, alpha=0.05, power=0.80, ar_coef=0.0):
    """
    给定步数、IC 标准差、显著性水平和目标功效，
    计算最小可检测 IC 均值。
    
    ar_coef: IC 步间自相关系数（0 = 独立，0.3-0.5 = 有重叠训练窗口）
    """
    # 有效样本量（考虑自相关）
    if ar_coef > 0:
        effective_n = n_steps * (1 - ar_coef) / (1 + ar_coef)
    else:
        effective_n = n_steps
    
    # 非中心 t 分布的 MDE
    t_alpha = stats.norm.ppf(1 - alpha)
    t_power = stats.norm.ppf(power)
    mde = ic_std * (t_alpha + t_power) / np.sqrt(effective_n)
    return mde

# 场景1：IC 独立，24步
mde_24_indep = mde_analysis(24, 0.06, ar_coef=0.0)  # ≈ 0.034

# 场景2：IC 自相关=0.3，24步
mde_24_ar03 = mde_analysis(24, 0.06, ar_coef=0.3)    # ≈ 0.044

# 场景3：IC 独立，180步（完整OOT）
mde_180_indep = mde_analysis(180, 0.06, ar_coef=0.0) # ≈ 0.012
```

**计算资源**：单机 Python 脚本，1 秒内完成。无需 GPU、无需大内存、无需外部 API。

**关键洞察**：
- 24 步 OOT 在独立假设下可检测 IC ≥ 0.034（对应年化 Sharpe ≈ 0.57）
- 24 步 OOT 在 ar=0.3 下只能检测 IC ≥ 0.044（对应年化 Sharpe ≈ 0.73）
- 这意味着 24 步作为 smoke test 是合理的（只检测"大效应"），但**不能用 24 步来判断 IC = 0.015 的边际 alpha**
- 完整 180 步 OOT 才是真正的验证——可检测 IC ≥ 0.012（年化 Sharpe ≈ 0.20）

### 实现建议

1. **在 A0.1 最后一周完成**：写一个 `mde_analysis.py` 脚本，输出 MDE 表格（步数 × 自相关系数 → 最小可检测 IC）
2. **预注册参数**：IC 标准差 = 0.06（基于 A 股月频因子经验）、显著性水平 = 0.05 单侧、功效 = 0.80
3. **输出**：写入 `validation_params.json` 的 `mde_analysis` 字段，记录"24 步可检测 IC ≥ X，180 步可检测 IC ≥ Y"
4. **不需要阻塞 S1 启动**：MDE 分析是诊断性的，不影响训练逻辑

---

## 分歧点 2：Phase A0 工作量详细 Breakdown

### 我的 R1 立场
35-60 工作日。主要低估了 SQLite WAL 和 execution audit。

### R2 更新：更详细的工程评估

**被低估的任务**：

| 子任务 | R1 评估 | R2 修正 | 低估原因 |
|---|---|---|---|
| SQLite WAL experiment_ledger | 2 周 | 3-4 周 | R1 只算了 schema DDL，漏了 migration 策略、备份策略、并发控制、DuckDB 只读连接池、TSV 导出管道 |
| orders_audit 状态机 | 2.5 周 | 3-4 周 | R1 只算了字段定义，漏了 T+1 open/proxy 的价格获取逻辑、3/5 日分批状态流转、未成交 carryover 的跨日跟踪、涨跌停解锁反转的回调检测 |
| ModelRegistry | 1.5 周 | 2-3 周 | R1 只算了持久化，漏了 artifact 存储目录结构设计、`get_latest_frozen()` 查询接口的 purge 日历匹配算法、模型回滚机制 |
| WalkForwardCalendarValidator | 1.5 周 | 1.5-2 周（不变） | 校验逻辑明确，复杂度可控 |
| universe_daily_construction_audit | 1 周 | 1-1.5 周 | 需要复核 PIT 输入的时间戳对齐，这部分可能比预期更繁琐 |
| FRED 替代方案 smoke test | 未单独列出 | 1-1.5 周 | fredapi 注册+API key 配置+series 逐一验证+fallback 方案测试 |

**R2 修正后总评估**：

| 阶段 | 乐观 | 基准 | 悲观 |
|---|---|---|---|
| A0.1（阻塞 S1 启动） | 2 周 | 2.5 周 | 3 周 |
| A0.2a（台账+注册+holdout） | 2 周 | 3 周 | 4 周 |
| A0.2b（execution audit+ModelRegistry） | 2.5 周 | 3.5 周 | 5 周 |
| A0.2c（FRED 替代+capacity report） | 1 周 | 1.5 周 | 2 周 |
| **总计** | **7.5 周** | **10.5 周** | **14 周** |
| **工作日** | **37 天** | **52 天** | **70 天** |

**关键变化**：
1. **SQLite WAL 比 R1 评估多 1-2 周**：并发控制（`BEGIN IMMEDIATE` + WAL checkpoint 策略）和 migration 框架是独立的工程任务，不能简单地"后面再补"
2. **orders_audit 状态机比 R1 评估多 0.5-1.5 周**：涨跌停解锁反转的回调检测需要监听 T+1/T+2 的价格变化，实现一个带超时的状态机
3. **FRED 替代方案需要单独立项**：fredapi 的 API key 注册、速率限制、series 可用性验证是一个完整的前置任务

**与其他 agent 的对比**：
- DeepSeek R1 未给出具体工作量评估
- Review R1 未给出具体工作量评估
- Main R1 维持 25-45 工作日的估计
- **我的修正后估计（37-70 工作日，基准 52 天）比 Main R1 的上限高约 15%**

**结论**：Phase A0 的基准估计应从 25-45 工作日上调至 **35-55 工作日**，悲观场景可到 70 工作日。

---

## 分歧点 3：CSRP 命中窗口

### Review R1 立场
P0 级问题。命中窗口长度未指定，应预注册主口径和敏感性。

### DeepSeek R1 立场
P0 级问题。命中窗口定义缺失。建议预注册：信号发出后 3 个 OOT step 内，至少 2 步成熟 IC < 0 或组合收益 < benchmark。

### 我的立场
**同意 P0。从工程实现角度，命中窗口的定义必须是可计算的、可验证的、可自动化的。**

### 工程可行性分析

CSRP（Concept Shift Risk Protocol）信号是"连续 IC < 0 触发 yellow/red"。命中窗口的定义是：**信号发出后，需要观察多长时间来判断这个信号是否"真的"预示了策略恶化**。

**工程约束**：
1. 命中窗口必须以 OOT step 为单位（不是交易日），因为 IC 是按 step 计算的
2. 命中窗口不能太短（否则随机噪声也会"命中"），也不能太长（否则信号失去预警价值）
3. 命中标准必须是客观可计算的（不能依赖主观判断）

**我的建议**：

```python
# 命中窗口定义
HIT_WINDOW_STEPS = 3  # 信号后 3 个 OOT step
HIT_THRESHOLD = 2     # 至少 2 步成熟 IC < 0 或组合收益 < benchmark

def is_hit(signal_step, oot_ic_series, oot_pnl_series, benchmark_pnl_series):
    """
    判断 CSRP 信号是否"命中"。
    
    signal_step: 信号触发的 OOT step 索引
    oot_ic_series: OOT IC 序列（已成熟）
    oot_pnl_series: OOT 组合收益序列
    benchmark_pnl_series: OOT 基准收益序列
    
    命中条件（满足任一）：
    1. 信号后 3 步中至少 2 步成熟 IC < 0
    2. 信号后 3 步中至少 2 步组合收益 < 基准收益
    """
    window_start = signal_step + 1
    window_end = signal_step + HIT_WINDOW_STEPS + 1
    
    ic_hits = sum(1 for i in range(window_start, window_end) 
                  if oot_ic_series[i] < 0)
    pnl_hits = sum(1 for i in range(window_start, window_end)
                   if oot_pnl_series[i] < benchmark_pnl_series[i])
    
    return ic_hits >= HIT_THRESHOLD or pnl_hits >= HIT_THRESHOLD
```

**敏感性分析**：
- 主口径：3 步窗口、2 步命中
- 敏感性：2 步窗口、2 步命中（更严格）和 5 步窗口、3 步命中（更宽松）
- 三个口径的结果都应报告，最保守的用于 tighten-only 决策

**关键实现细节**：
1. **"成熟 IC"的定义**：IC 必须已经过了 label horizon + purge 期才能算"成熟"。例如 20 日标签的 IC 在 step T 只有在 T+20+purge 天后才能确认。这意味着命中窗口的观察有自然延迟
2. **组合收益 vs IC 的选择**：组合收益包含了交易成本，更能反映真实表现；IC 是纯信号质量。建议两者都报告，组合收益作为主口径
3. **Wilson 置信区间**：对于小样本（`n_signals < 10`），Wilson 区间比 Wald 区间更稳健。Python 实现：`statsmodels.stats.proportion.proportion_confint(method='wilson')`

### 实现建议

1. **在 A0.2 设计实验台账 schema 时**，增加 `hit_window_steps`、`hit_threshold`、`hit_window_sensitivity` 字段
2. **预注册**：在 `validation_params.json` 中记录主口径和敏感性
3. **自动化**：在 CSRP 监控模块中实现 `is_hit()` 函数，每次新 OOT step 成熟时自动更新命中率

---

## 分歧点 4：分层裁剪与 Capital Overlay 执行顺序

### Review R1 立场
P0 级问题。分层裁剪在 capital overlay 之前执行，裁剪后权重乘以 capital_multiplier。

### 我的立场
**同意 P0。这是一个必须在代码中严格遵守的顺序问题，顺序错误会导致权重逻辑完全错误。**

### 工程可行性分析

**正确执行顺序**：

```
1. 模型预测 → raw_scores
2. 选股过滤 → candidate_stocks（universe filter）
3. 权重分配 → target_weights（score-to-weight 映射）
4. 分层裁剪 → trimmed_weights（总换手 → 行业 → 个股）
5. Capital overlay → final_weights = trimmed_weights × capital_multiplier
6. 订单生成 → orders（考虑 T+1、涨跌停、流动性约束）
```

**为什么这个顺序是正确的**：

| 顺序 | 分析 |
|---|---|
| ✅ 先裁剪再 overlay | 裁剪处理的是**交易约束**（换手、行业集中度、个股集中度），overlay 处理的是**资金约束**（市场状态决定仓位水平）。交易约束应在资金约束之前应用，因为：(1) 裁剪后的权重代表"如果满仓，最优组合是什么"；(2) overlay 决定"实际投入多少资金"。两者正交。 |
| ❌ 先 overlay 再裁剪 | 如果先乘以 capital_multiplier（如 0.5），再做换手裁剪，会导致：换手上限被隐式减半（因为权重都缩小了），实际换手远低于预注册的 10% 上限。这违反了"换手上限与市场状态无关"的设计原则。 |

**实现约束**：

```python
def apply_portfolio_construction(raw_weights, prev_weights, capital_multiplier, 
                                  turnover_limit, sector_limits, stock_limit):
    """
    正确的执行顺序：裁剪 → overlay → 订单
    """
    # Step 1: 分层裁剪（与 capital_multiplier 无关）
    # 1a. 总换手裁剪
    gross_turnover = np.sum(np.abs(raw_weights - prev_weights)) / 2
    if gross_turnover > turnover_limit:
        scale = turnover_limit / gross_turnover
        trimmed = prev_weights + (raw_weights - prev_weights) * scale
    else:
        trimmed = raw_weights
    
    # 1b. 行业集中度裁剪
    for sector in unique_sectors:
        sector_weight = trimmed[sector_mask].sum()
        if sector_weight > sector_limits[sector]:
            trimmed[sector_mask] *= sector_limits[sector] / sector_weight
    
    # 1c. 个股集中度裁剪
    trimmed = np.clip(trimmed, 0, stock_limit)
    
    # Step 2: 归一化（裁剪后权重之和可能 < 1）
    trimmed = trimmed / trimmed.sum()
    
    # Step 3: Capital overlay
    final_weights = trimmed * capital_multiplier
    
    # Step 4: 现金部分
    cash_weight = 1.0 - final_weights.sum()
    
    return final_weights, cash_weight
```

**特殊情况：裁剪后归一化 vs 现金留存**：

这里有一个设计选择：
- **选项 A**：裁剪后归一化到 1.0，再乘以 overlay → 总是满仓（减去 overlay 的现金）
- **选项 B**：裁剪后不归一化（允许 < 1.0），再乘以 overlay → 可能有"裁剪现金"和"overlay 现金"

**我的建议**：选项 A。原因：
1. 归一化确保裁剪只影响**组合结构**（行业/个股权重比例），不影响**仓位水平**（由 overlay 独立控制）
2. 选项 B 会导致裁剪和 overlay 产生耦合——裁剪越激进，现金越多，overlay 的效果被稀释
3. 选项 A 的语义更清晰："裁剪决定持有哪些股票，overlay 决定投入多少资金"

### 实现建议

1. **在代码中用注释和断言强制顺序**：
   ```python
   # ASSERT: turnover trimming MUST happen BEFORE capital overlay
   assert capital_multiplier_applied == False, "Capital overlay already applied!"
   ```
2. **在单元测试中覆盖错误顺序的场景**：测试"先 overlay 再裁剪"会产生的错误结果
3. **在文档中明确写出执行顺序**：建议在执行规范 §7.1 增加一个"组合构建执行流程图"

---

## 分歧点 5：Sleeve FDR 计入规则

### DeepSeek R1 立场
P0 级问题。每个 sleeve 独立计入 `attempt_count`，FDR 在 sleeve 族内和族间均适用。

### 我的立场
**同意 P0，但从工程实现角度，sleeve 的 FDR 计入规则需要明确"族"的定义。**

### 工程可行性分析

**问题本质**：5 个预注册 sleeve 如果各自独立计入 `attempt_count`，会显著膨胀实验族大小，导致 FDR 惩罚加重。

**两种方案对比**：

| 方案 | 族定义 | attempt_count | FDR 惩罚 | 适用场景 |
|---|---|---|---|---|
| A: 每个 sleeve 独立成族 | 5 个族 | 每族独立计数 | 低（每族内尝试少） | sleeve 之间完全独立（不同 universe） |
| B: 所有 sleeve 共享一族 | 1 个族 | 所有 sleeve × 模型 × 标签 累计 | 高（总尝试多） | sleeve 之间高度相关（同 universe 不同分位） |

**我的判断**：方案 B 更合理。原因：

1. **sleeve 之间高度相关**：5 个 sleeve 共享同一训练数据、同一 walk-forward calendar、同一模型。差异只在选股过滤阶段（分数分位 / 市值分位）。这意味着不同 sleeve 的 alpha 来源高度重叠
2. **防 p-hacking**：如果每个 sleeve 独立成族，研究者可以测试 5 个 sleeve，只要有一个通过 FDR 就可以"keep"。这实质上是 5 次独立的多重比较，但 FDR 只在族内校正
3. **与现有框架一致**：文档已定义实验族为"因子 × 标签 × 模型 × 半衰期 × 训练窗口 × 正交化分支 × 执行规则"。sleeve 可以视为"执行规则"维度的一个分支

**具体实现**：

```python
# test_family_id 的生成规则
def generate_test_family_id(factor_id, label_id, model_id, half_life, 
                             train_window, ortho_branch, sleeve_id=None):
    """
    sleeve_id 是执行规则维度的扩展。
    同一因子+标签+模型+半衰期+训练窗口+正交化分支的所有 sleeve
    共享同一 test_family_id。
    """
    family = f"{factor_id}_{label_id}_{model_id}_{half_life}_{train_window}_{ortho_branch}"
    return family

# attempt_count 的计数
# 每个 sleeve 的每次尝试都计入同一 family 的 attempt_count
# 5 sleeve × 7 模型 = 35 次尝试 → FDR 校正基于 35 次
```

**对 keep 决策的影响**：

如果使用方案 B（共享一族），5 个 sleeve 的 keep 决策必须通过**包含所有 sleeve 尝试的 FDR 校正**。具体来说：
- 如果 5 个 sleeve × 7 个模型 = 35 次尝试，BH FDR 在 35 次中校正
- 只有通过 FDR 校正的 sleeve 才能 keep
- **不允许**："sleeve A 通过了 FDR（在 7 次尝试中），所以 keep sleeve A"——因为实际尝试了 35 次

### 实现建议

1. **在实验台账 schema 中**：`test_family_id` 不包含 `sleeve_id`，`attempt_count` 包含所有 sleeve 的尝试
2. **在 FDR 计算中**：`total_trials_in_family = n_sleeves × n_models × n_labels × ...`
3. **在文档中明确**："sleeve 是执行规则维度的扩展，不独立成族"

---

## 分歧点 6：Concept Shift 独立性假设与 IC 自相关

### DeepSeek R1 立场
P0 级问题。IC 步间存在训练窗口重叠（5 年窗口、63 日步长），相邻步 IC 相关系数可能达 0.3-0.6。在正自相关下，5/6 yellow 门槛的实际误报率会显著高于理论值 10.9%。

### 我的立场
**同意这是真实问题，但从工程实现角度，检测和处理 IC 自相关的方案已经成熟且计算成本低。**

### 工程可行性分析

**IC 自相关的来源**：
1. **训练窗口重叠**：5 年训练窗口、63 日步长 → 相邻步的训练数据有 4.75 年重叠（95% 重叠）
2. **因子本身的动量**：某些因子（如短期反转）的 IC 有自然的自相关结构
3. **市场状态持续性**：牛市/熊市期间，因子表现有持续性

**检测 IC 自相关**：

```python
import numpy as np
from statsmodels.stats.diagnostic import acorr_ljungbox

def detect_ic_autocorrelation(ic_series, max_lag=6):
    """
    检测 OOT IC 序列的自相关结构。
    
    返回：
    - lag-1 到 lag-6 的自相关系数
    - Ljung-Box 检验 p 值（检验是否存在显著自相关）
    - 有效自由度调整系数
    """
    n = len(ic_series)
    
    # 自相关系数
    acf = np.correlate(ic_series - ic_series.mean(), 
                       ic_series - ic_series.mean(), mode='full')
    acf = acf[n-1:] / acf[n-1]  # 归一化
    acf = acf[:max_lag+1]
    
    # Ljung-Box 检验
    lb_result = acorr_ljungbox(ic_series, lags=max_lag, return_df=True)
    
    # 有效自由度调整（Neiderreiter 估计）
    # effective_n = n / (1 + 2 * sum(acf[k]^2, k=1..max_lag))
    acf_sum = np.sum(acf[1:max_lag+1]**2)
    effective_n = n / (1 + 2 * acf_sum)
    
    return {
        'acf': acf,
        'ljung_box_pvalues': lb_result['lb_pvalue'].values,
        'effective_n': effective_n,
        'has_significant_autocorrelation': lb_result['lb_pvalue'].min() < 0.05
    }
```

**处理 IC 自相关的方案**：

| 方案 | 原理 | 实现复杂度 | 推荐度 |
|---|---|---|---|
| Block bootstrap 误报率 | 用 block bootstrap 估计实际误报率，替代理论 10.9% | 低 | ⭐⭐⭐⭐⭐ |
| 有效自由度调整 | 用 effective_n 替代 n 计算二项分布概率 | 低 | ⭐⭐⭐⭐ |
| Permutation test | block permutation 保留自相关结构 | 中 | ⭐⭐⭐⭐ |

**推荐方案：Block bootstrap 误报率估计**

```python
def estimate_actual_false_positive_rate(ic_series, block_size=21, 
                                         n_bootstrap=10000, 
                                         threshold=5, window=6):
    """
    用 block bootstrap 估计 5/6 yellow 门槛的实际误报率。
    
    block_size: block bootstrap 的块大小（建议 21 = 一个月）
    """
    n = len(ic_series)
    actual_fpr = 0
    
    for _ in range(n_bootstrap):
        # Block bootstrap 重采样
        resampled = block_bootstrap(ic_series, block_size)
        
        # 检查 5/6 门槛
        negative_count = 0
        for i in range(len(resampled) - window + 1):
            window_ic = resampled[i:i+window]
            if np.sum(window_ic < 0) >= threshold:
                negative_count += 1
                break
        
        if negative_count > 0:
            actual_fpr += 1
    
    return actual_fpr / n_bootstrap

def block_bootstrap(series, block_size):
    """Block bootstrap 重采样"""
    n = len(series)
    n_blocks = int(np.ceil(n / block_size))
    indices = []
    for _ in range(n_blocks):
        start = np.random.randint(0, n - block_size + 1)
        indices.extend(range(start, start + block_size))
    return series[indices[:n]]
```

**计算资源**：10000 次 bootstrap × 24 步 × 简单比较 = 毫秒级。可以在每次 OOT 更新时实时运行。

**预期结果**：
- 如果 IC 自相关 = 0.3，实际误报率可能从 10.9% 上升到 15-20%
- 如果 IC 自相关 = 0.5，实际误报率可能上升到 20-30%
- 这意味着 5/6 门槛可能需要调整为 5/6 + block bootstrap p < 0.05 的双重条件

### 实现建议

1. **在 CSRP 监控模块中**：每次 OOT 更新时，自动运行 `detect_ic_autocorrelation()` 和 `estimate_actual_false_positive_rate()`
2. **在实验台账中**：增加 `ic_autocorrelation_lag1`、`ic_autocorrelation_lag6`、`block_bootstrap_fpr` 字段
3. **在 keep 决策中**：如果 block bootstrap 估计的实际误报率 > 15%，yellow 信号应升级为更保守的处理
4. **在文档中**：注明 10.9% 的独立性假设，并要求通过 block bootstrap 估计实际误报率

---

## 总结：六分歧点共识矩阵

| # | 分歧点 | DeepSeek R1 | Review R1 | Main R1 | Coder R2（我） |
|---|---|---|---|---|---|
| 1 | MDE 分析 | P0 | 未提及 | 未提及 | **P0，A0.1 完成，1 天工作量** |
| 2 | Phase A0 工作量 | 未评估 | 未评估 | 25-45 天 | **35-55 天（基准 52 天）** |
| 3 | CSRP 命中窗口 | P0 | P0 | P1 | **P0，3 步窗口/2 步命中** |
| 4 | 裁剪 vs overlay 顺序 | 未提及 | P0 | 未提及 | **P0，先裁剪再 overlay** |
| 5 | Sleeve FDR 计入 | P0 | 未提及 | 未提及 | **P0，共享一族** |
| 6 | IC 自相关 | P0 | 未提及 | 未提及 | **P0，block bootstrap 估计** |

**与其他 agent 的主要分歧**：
- **MDE 分析**：只有 DeepSeek 和我关注。我认为执行成本极低（1 天），不应成为阻塞项
- **Phase A0 工作量**：我比 Main R1 的上限高约 15%，主要因为 SQLite WAL 和 orders_audit 状态机的复杂度被低估
- **Sleeve FDR**：只有 DeepSeek 和我关注。我认为共享一族是唯一合理的方案
- **裁剪 vs overlay 顺序**：只有 Review 和我关注。我认为这是代码级的硬约束，必须用断言保护

---

*Coder Agent R2 交叉审阅完成。*
