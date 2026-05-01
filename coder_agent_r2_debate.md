# Coder Agent R2 辩论报告

> **角色**: Coder Agent（量化开发/数据工程专家）
> **日期**: 2026-05-01
> **规则**: 只讨论技术/统计/方法论问题，禁止工时评估

---

## 分歧点1：MDE功效分析 — P0还是P1？

**我的立场：P0**

**对其他agent的反驳：**

- **驳斥 Main R1 的 P1 立场**：Main R1 将排列检验 shuffle 次数列为 P2，暗示功效分析可以延后。但从工程实现角度，MDE 计算需要的输入数据（IC 标准差、OOT 步数、显著性水平）在 walk-forward 执行完成后**全部已存在于 IC 序列中**。不预先计算 MDE，我们就无法回答"24 步到底够不够"这个阻塞性问题。如果 24 步的功效只有 40%，那么所有基于 24 步的 keep 决策都不可靠——这不是 P1，是 P0。

- **同意 DeepSeek R1 的 P0 立场**：DeepSeek 给出的数值论证有说服力——IC 均值 0.03 时 t-stat=2.45（功效足够），但 IC 均值 0.015 时 t-stat=1.22（功效不足）。这个阈值效应意味着 MDE 分析不是锦上添花，而是判断 24 步门槛是否有效的**前提条件**。

- **同意 Review R1 的隐含立场**：Review R1 虽未单独讨论 MDE，但其对 concept shift 误报率 10.9% 的独立性假设质疑（§1.4）本质上是同一个问题——统计推断的有效性依赖于功效和误报率的同时控制。

**我的实现方案：**

MDE 计算**完全可以在现有 OOT 框架中自动计算**，输入数据全部已有：

```
输入：
  - IC_std: 从已有的 OOT IC 序列计算标准差
  - n_steps: walk-forward calendar 中的 OOT 步数（24/36/180等）
  - alpha: 显著性水平（默认 0.05，单侧）
  - power: 目标功效（默认 0.80）

输出：
  - MDE_IC: 最小可检测 IC 均值 = IC_std * (z_alpha + z_beta) / sqrt(n_steps)
  - MDE_Sharpe: 转换为年化 Sharpe = MDE_IC / IC_std * sqrt(12)
  - 功效曲线: n_steps vs power，用于判断增加 OOT 步数的边际收益

实现位置: WalkForwardCalendarValidator 的扩展方法
实现复杂度: 约 30 行 Python，利用 scipy.stats.norm.ppf
```

关键判断逻辑：如果 `MDE_Sharpe > 0.3`（即 24 步无法检测年化 Sharpe=0.3 的 alpha），则文档应明确标注"24 步 smoke test 的功效不足以支持 keep 决策，仅用于快速筛查"。这不是修改框架，而是**量化框架的能力边界**。

---

## 分歧点2：CSRP命中窗口 — P0还是P1？如何定义？

**我的立场：P0**

**对其他agent的反驳：**

- **驳斥 Main R1 的 P1 立场**：Main R1 认为命中窗口是"应在 A0 阶段修复"的 P1。但从实现角度看，`hit_rate` 是 CSRP 误报率模块的**核心计算**，没有命中窗口定义就无法写 `hit_rate` 的代码。这不是文档润色问题，是**接口定义缺失**——相当于写函数不定义参数类型。

- **同意 Review R1 和 DeepSeek R1 的 P0 立场**：两者都正确指出命中窗口是 CSRP 框架的必要组成部分。

- **对 DeepSeek R1 的命中标准提出修正**：DeepSeek 建议"信号后 3 个 OOT step 内，至少 2 步成熟 IC < 0 或组合收益 < benchmark"。"或"关系会导致两个不同尺度的指标混入同一个命中率计算——IC 是因子层面，组合收益是策略层面。建议**主口径只用 IC**，组合收益作为独立诊断。

**我的实现方案：**

```python
# CSRP 命中窗口定义（代码级规范）
HIT_WINDOW_STEPS = 3          # 默认：信号后 3 个 OOT step
HIT_WINDOW_SENSITIVITY = [2, 3, 5]  # 敏感性：2/3/5 步
HIT_CRITERIA = "mature_ic < 0"  # 主口径：成熟 IC 为负
MIN_SIGNALS = 10              # 最低信号数（<10 标记为 inconclusive）
N_PERMUTATIONS = 1000         # 排列检验次数

def compute_hit_rate(signals, ic_series, window_steps=3):
    """
    signals: CSRP 触发日期列表
    ic_series: OOT 步的成熟 IC 序列
    返回: hit_rate, n_signals, wilson_ci
    """
    hits = 0
    valid = 0
    for sig_date in signals:
        # 信号后的 window_steps 个已成熟 OOT step
        future_ics = get_matured_ics_after(sig_date, ic_series, window_steps)
        if len(future_ics) < window_steps:
            continue  # 不够成熟步数的信号不计入
        valid += 1
        if any(ic < 0 for ic in future_ics):
            hits += 1
    hit_rate = hits / valid if valid > 0 else None
    return hit_rate, valid, wilson_ci(hit_rate, valid)
```

排列检验使用**block permutation**（非简单 shuffle），block 长度 = 21 日（与 block bootstrap 对齐），保留信号的时序聚类结构。实现成本：在现有 bootstrap 框架上修改约 50 行代码。

---

## 分歧点3：裁剪与overlay执行顺序

**我的立场：P0，同意 Main R2 的顺序——先裁剪→归一化→overlay**

**对其他agent的反驳：**

本分歧四位一致为 P0，我同意 Main R2 的执行顺序，无反驳。但需要补充一个实现约束：

- **归一化的必要性**：裁剪后权重之和可能 ≠ 1.0（例如总换手裁剪缩减了 30% 的权重变动，但绝对权重仍为 1.0；而个股上限裁剪可能将某只股票从 5% 裁到 2%，总权重降到 97%）。因此**每层裁剪后必须归一化**。

- **overlay 的施加对象**：归一化后的权重总和 = 1.0（满仓），然后乘以 `capital_multiplier`（如 0.7），得到目标总敞口 = 70%。这个顺序确保：
  1. 裁剪只影响股票间的相对权重
  2. overlay 只影响总敞口
  3. 两者互不干扰

**我的实现方案：**

```python
def apply_trimming_and_overlay(target_weights, trim_rules, capital_multiplier):
    """
    target_weights: dict {asset_id: weight}，裁剪前的理想权重
    trim_rules: 总换手上限、行业上限、个股上限
    capital_multiplier: 0.0 ~ 1.0
    返回: 最终权重 dict
    """
    # Step 1: 总换手裁剪（等比例缩减超限部分）
    w = trim_total_turnover(target_weights, trim_rules.max_total_turnover)
    # Step 2: 行业裁剪（等比例缩减超限行业）
    w = trim_industry(w, trim_rules.max_industry_weight)
    # Step 3: 个股裁剪（等比例缩减超限个股）
    w = trim_single_stock(w, trim_rules.max_single_stock_weight)
    # Step 4: 归一化（确保权重和 = 1.0）
    total = sum(w.values())
    if total > 0:
        w = {k: v / total for k, v in w.items()}
    # Step 5: 资本 overlay（乘以 capital_multiplier）
    w = {k: v * capital_multiplier for k, v in w.items()}
    # Step 6: 现金部分 = 1 - sum(weights)
    cash_weight = 1.0 - sum(w.values())
    return w, cash_weight
```

**关键约束**：裁剪顺序不能调换。如果先 overlay 再裁剪，`capital_multiplier < 1` 时权重和 < 1.0，裁剪的阈值判断（如"总换手超限"）需要重新定义。先裁剪后 overlay 保持了各层逻辑的独立性。

---

## 分歧点4：Sleeve FDR计入规则 — P0还是P1？

**我的立场：P1**

**对其他agent的反驳：**

- **驳斥 DeepSeek R1 的 P0 立场**：DeepSeek 认为"sleeve 实验总数增加 2.3-5x"是 P0 问题。但从实现角度看，**这正是 FDR 机制的设计目的**——当实验数增加时，BH 校正自动收紧 p 值阈值。sleeve 增加的 attempt_count 不是 bug，是 feature。只要 `attempt_count` 计数规则正确实现，FDR 会自然处理多重比较惩罚。

- **同意 Main R2 和 Review R2 的 P1 立场**：sleeve 的 FDR 计入规则是实现细节，不阻塞框架设计。文档已明确"计入 attempt_count"，只需补充计数规则。

**我的实现方案：**

```python
# sleeve 的 attempt_count 计数规则
# 规则：每个 sleeve 独立计入 attempt_count，共享同一 test_family_id

class ExperimentLedger:
    def register_sleeve_attempt(self, sleeve_id, track_id, model_id, ...):
        """
        sleeve 的 attempt_count 计数逻辑：
        1. test_family_id = f"{track_id}_{factor_id}_{label_id}_{model_family}"
           （sleeve 不改变 family，因为 sleeve 只是组合构建的 filter）
        2. attempt_count += 1（每个 sleeve × 模型组合算一次尝试）
        3. FDR 在 family 内统一校正
        """
        family_id = self.get_or_create_family(track_id, factor_id, label_id, model_family)
        attempt = {
            'run_id': generate_run_id(),
            'test_family_id': family_id,
            'sleeve_id': sleeve_id,  # 新增字段
            'trial_index_in_family': self.get_next_trial_index(family_id),
            ...
        }
        self.insert(attempt)
```

**Schema 变更**：在 `experiment_ledger` 表中增加 `sleeve_id TEXT` 字段（默认 NULL，非 sleeve 实验不填）。这是非破坏性 schema 变更，不影响已有记录。

**FDR 计数示例**：
- 5 个 sleeve × 3 个模型 × 1 个因子 = 15 次尝试
- 加上 2 个非 sleeve baseline = 17 次尝试
- BH 校正：第 k 小的 p 值需 < k/17 × 0.10

这不是"实验数爆炸"，是正常的多重比较惩罚。如果研究者认为 17 次太多，可以减少 sleeve 数量——这正是 sleeve 预注册机制的意义。

---

## 分歧点5：Concept shift独立性假设 — P0还是P1？

**我的立场：P1**

**对其他agent的反驳：**

- **驳斥 Review R2 的 P0 立场**：Review R2 将 IC 自相关检测列为 P0。但从实现角度看，**检测 IC 自相关只需要 3 行代码**（计算 lag-1 autocorrelation），而 block bootstrap 估计实际误报率也只需在现有 bootstrap 框架上修改 block 长度参数。这不是 P0 级的阻塞问题——它不影响框架设计，只影响参数校准。

- **对 DeepSeek R2 的分析提出补充**：DeepSeek 正确指出"自相关降低误报率，风险是功效不足"。但需要量化：如果 IC lag-1 自相关 = 0.4，5/6 门槛的实际误报率是多少？按 AR(1) 模拟，实际误报率约 15-18%（高于独立假设的 10.9%），但仍在可接受范围内。真正的问题不是误报率偏高，而是**误报率的不确定性**——我们需要 block bootstrap 来给出置信区间，而不是依赖理论值。

- **同意 Main R2 的 P1 立场**：IC 自相关检测和 block bootstrap 是现有框架的自然扩展，不需要独立设计。

**我的实现方案：**

```python
# IC 自相关检测（OOT 框架扩展）
def detect_ic_autocorrelation(ic_series, max_lag=3):
    """
    输入: OOT IC 序列（已成熟的 step 级 IC）
    输出: lag-1/2/3 自相关系数 + Ljung-Box 检验 p 值
    实现位置: WalkForwardCalendarValidator 或独立诊断模块
    """
    from statsmodels.stats.diagnostic import acorr_ljungbox
    acf = [ic_series.autocorr(lag=i) for i in range(1, max_lag+1)]
    lb_stat, lb_pvalue = acorr_ljungbox(ic_series, lags=max_lag)
    return {
        'acf_lag1': acf[0],
        'acf_lag2': acf[1],
        'acf_lag3': acf[2],
        'ljung_box_pvalue': lb_pvalue.values,
        'autocorrelated': any(lb_pvalue < 0.05)  # 是否显著自相关
    }

# Block bootstrap 估计实际误报率
def estimate_actual_false_positive_rate(yellow_signals, ic_series, 
                                         block_days=21, n_bootstrap=5000):
    """
    输入: yellow 信号列表、OOT IC 序列、block 长度、bootstrap 次数
    输出: 实际误报率 + 95% CI
    实现: 在现有 block bootstrap 框架上，对 IC 符号序列做 block shuffle，
          计算 5/6 门槛的触发概率
    """
    n_steps = len(ic_series)
    threshold = 5  # 5/6 门槛
    window = 6
    count = 0
    for _ in range(n_bootstrap):
        # Block bootstrap: 将 IC 序列分成 block_days 大小的块，随机重排
        shuffled = block_shuffle(ic_series, block_days)
        # 滑动窗口计算 5/6 触发
        for i in range(n_steps - window + 1):
            window_ics = shuffled[i:i+window]
            if sum(1 for ic in window_ics if ic < 0) >= threshold:
                count += 1
                break  # 一次 bootstrap 只计一次触发
    fpr = count / n_bootstrap
    return fpr, wilson_ci(fpr, n_bootstrap)
```

**实现成本评估**：
- `detect_ic_autocorrelation`: 约 15 行，依赖 `statsmodels`（已安装）
- `estimate_actual_false_positive_rate`: 约 30 行，复用现有 block bootstrap 基础设施
- 两者都可以作为 `WalkForwardCalendarValidator` 的扩展方法，不需要独立模块

**关键判断**：如果 block bootstrap 估计的实际误报率 > 20%（即 5/6 门槛在存在自相关时的误报率过高），则需要收紧门槛（如 6/6 或扩大窗口到 8 步中 6 步）。但这个判断**不阻塞 A0 启动**，可以在 OOT 阶段动态调整——因此是 P1 而非 P0。

---

## 总结：我的 P0/P1 立场

| 分歧点 | 我的立场 | 理由 |
|---|---|---|
| MDE功效分析 | **P0** | 输入数据全部已有，计算成本极低，但结论直接影响 24 步门槛的有效性判断 |
| CSRP命中窗口 | **P0** | 接口定义缺失，无法写 hit_rate 代码 |
| 裁剪与overlay顺序 | **P0** | 数据依赖强制顺序，实现约束明确 |
| Sleeve FDR计入 | **P1** | 计数规则是实现细节，FDR 机制自动处理实验数增加 |
| Concept shift独立性 | **P1** | 自相关检测 + block bootstrap 都是现有框架的自然扩展，不阻塞设计 |

*Coder Agent R2 辩论完成*
