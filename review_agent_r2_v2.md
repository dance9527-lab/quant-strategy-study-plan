# Review Agent R2 交叉审阅报告

> **审阅人**：Review Agent  
> **日期**：2026-05-01  
> **审阅对象**：Main Agent R1-V2、Review Agent R1-V2、DeepSeek Agent R1-V2、Coder Agent R1-V2  
> **任务**：对6个分歧点给出独立判断

---

## 分歧点 1：统计功效 / MDE 分析

**DeepSeek 立场**：P0（24步OOT能否检测alpha、12月holdout功效、sleeve功效稀释均未评估）  
**Main / Review R1 / Coder**：未提及

### 我的立场：同意 DeepSeek，应补充 MDE 分析，但优先级为 P1 而非 P0

**理论支撑**：

1. **24步OOT的功效**：假设月频IC均值=0.03、IC标准差=0.06，则 t-stat = 0.03 / (0.06 / √24) ≈ 2.45，单侧p≈0.008，功效充足。但如果IC均值=0.015（更现实的A股market-only因子水平），t-stat = 0.015 / (0.06 / √24) ≈ 1.22，单侧p≈0.12，功效不足。24步作为smoke test门槛本身不需要高功效——文档已明确"24步只是最低验收门槛，完整验证约180步"。因此24步的功效问题不阻塞S1启动，但应在A0阶段完成MDE计算。

2. **12月holdout功效**：12个月≈12个调仓周期。如果alpha年化Sharpe=0.3，月度Sharpe≈0.087，12个独立观测的t-stat ≈ 0.087 × √12 ≈ 0.30，功效极低（约20-30%）。但holdout的目的不是独立检测alpha，而是验证模型在完全OOS区间没有退化。文档的holdout使用方式是"holdout PnL必须为正且不低于OOT中位数的50%"，这是一个相对宽松的条件，功效问题不如纯假设检验严重。

3. **sleeve功效稀释**：将Top-N分成5个sleeve后，每个sleeve持仓数减少，组合波动率上升，检测alpha的统计功效确实下降。但sleeve的首要目的是诊断（理解alpha的来源分布），而非独立alpha检测。诊断性分析不需要与主策略相同的统计功效。

**最终建议**：
- 在Phase A0.1中增加一项MDE计算任务：给定IC标准差的合理估计（可从warehouse历史数据得出），计算24步和180步OOT分别能检测到的最小IC均值
- 在Phase A0.2中评估12月holdout的功效，如果功效<50%，考虑延长到18个月
- sleeve的功效稀释作为P2记录，在S1完成后评估是否需要增加sleeve持仓数下限
- **不阻塞S1启动**，但应在validation_params.json中记录MDE分析结果

---

## 分歧点 2：Phase A0 工作量

**文档估计**：25-45工作日  
**Coder评估**：35-60工作日（因SQLite schema DDL、ModelRegistry持久化、execution_slippage计算基准等额外工作）  
**Main / Review R1**：支持文档估计

### 我的立场：支持 Coder 的 35-60 工作日估计

**理论支撑**：

1. **SQLite WAL实验台账**：文档只给出了TSV字段模板（60+字段），没有CREATE TABLE语句、索引定义、约束、WAL checkpoint策略、migration方案和备份策略。Coder正确指出这些是独立的工程任务。60+字段的单表设计还需要考虑拆表（runs/validation_results/audit_status/metadata四表），这增加了schema设计时间。估计2-3周是合理的。

2. **ModelRegistry持久化**：文档只说"所有模型版本写入ModelRegistry"，但持久化方案（SQLite表+文件系统artifact？纯目录结构？）、版本查询接口（get_latest_frozen）、refit/rebalance不同步时的模型选择算法均未定义。这些是A0.2的阻塞项——没有ModelRegistry，S1的冻结模型无法管理。估计1.5-2周是合理的。

3. **execution_slippage计算基准**：Coder指出orders_audit的execution_slippage未定义计算基准（相对open、vwap还是close？），以及T+1 open/proxy、3/5日分批、未成交carryover和解锁反转的完整状态机需要约2周独立开发。这不是简单的字段补充，而是完整的订单执行模拟逻辑。

4. **额外发现的隐藏工作**：
   - WalkForwardCalendarValidator的异常处理和edge case（如假期导致的步长不规则）
   - validation_params.json的参数hash和版本管理
   - universe_daily_construction_audit的PIT输入验证
   - 估值覆盖审计的三口径实验

**反驳文档估计的理由**：
- 25-45工作日的范围本身就很大（1.8x），说明估计者对不确定性缺乏信心
- 文档的估计基于"任务清单"而非"工程实现"，没有考虑SQLite WAL的并发控制、ModelRegistry的查询接口等工程细节
- Coder的逐项分解（6.5周乐观 / 11.5周最可能 / 16.5周悲观）比文档的粗略范围更有说服力

**最终建议**：
- 更新Phase A0估计为35-60工作日
- 拆分为A0.1（2-3周，不变）+ A0.2a（3-4周：holdout log + test family + experiment ledger schema）+ A0.2b（3-4周：execution audit + orders audit + capacity report + ModelRegistry）
- 在A0.1结束时进行一次checkpoint，根据实际进度调整A0.2a/2b的估计

---

## 分歧点 3：CSRP 命中窗口

**Review R1**：P0（未定义命中窗口）  
**Main R1**：P1  
**DeepSeek R1**：P2（建议信号后3个OOT step内至少2步成熟IC<0）

### 我的立场：P0，同意 Review R1

**理论支撑**：

1. **命中窗口是误报率计算的前提**：CSRP误报率框架要求计算 `false_positive_rate = 1 - hit_rate`，而hit_rate的计算必须先定义"什么算命中"。如果命中窗口未定义，整个CSRP误报率框架无法执行。这不是一个"可以后续补充"的细节，而是框架的核心参数。

2. **窗口长度直接影响误报率**：
   - 窗口=5日：只有短期持续恶化才算命中，hit_rate低，误报率高
   - 窗口=20日：中期恶化也算命中，hit_rate高，误报率低
   - 窗口=60日：长期趋势也算命中，但可能错过短期反弹
   
   不同窗口会导致完全不同的CSRP信号质量评估结论。

3. **预注册的必要性**：如果在看到数据后再选择"最优"命中窗口，等于对同一信号进行多重检验（选择窗口=选择检验统计量），会膨胀误报率。必须在实验登记中预注册主口径和敏感性。

**最终建议**：
- 定义默认命中窗口：信号触发后**3个OOT step**（约3个月）内，至少**2步成熟IC < 0**或组合收益 < benchmark
- 预注册敏感性：2步/3步/4步 OOT step窗口
- 最小信号数门槛：`n_signals < 5`时，CSRP统计仅作参考，不得作为tighten-only依据
- 将此规则写入执行规范§9.1.5

---

## 分歧点 4：分层裁剪与capital overlay执行顺序

**Review R1**：P0（执行顺序未明确）  
**其他agent**：未明确讨论

### 我的立场：P0，正确顺序是"先裁剪，再overlay"

**理论支撑**：

1. **架构逻辑**：文档明确"选股模型先生成目标股票篮子，资金模块再按市场状态给组合目标市值乘以capital multiplier"。这意味着：
   - Step 1：模型生成目标权重（满仓权重，总和=1.0）
   - Step 2：分层裁剪（总换手→行业→个股），裁剪后权重归一化到1.0
   - Step 3：capital overlay（乘以capital_multiplier < 1.0），最终权重总和 < 1.0

2. **反向顺序的问题**：如果先overlay再裁剪：
   - overlay将权重缩放到80%（牛市），此时总换手计算基于缩放后的权重
   - 但换手应该基于"如果不考虑仓位限制的理想换手"来计算
   - 先overlay会导致换手上限被低估（因为权重已被缩放）
   - 行业上限和个股上限也会被低估

3. **归一化的处理**：裁剪后归一化到1.0是正确的（满仓状态），然后overlay将其缩放到目标仓位。如果裁剪后不归一化，而是保留残余现金，再overlay，会导致双重缩放（裁剪产生现金 + overlay产生现金）。

4. **与sleeve的交互**：如果有多个sleeve，正确顺序是：
   - Step 1：各sleeve独立生成目标权重
   - Step 2：合并为总组合（加权平均或等权）
   - Step 3：分层裁剪（在总组合层面）
   - Step 4：capital overlay

**最终建议**：
- 在执行规范§7.1中明确："分层裁剪在capital overlay之前执行。裁剪后权重归一化到1.0（满仓），然后乘以capital_multiplier得到最终目标权重。"
- 明确sleeve合并与裁剪的顺序："多sleeve先合并为总组合，再执行分层裁剪，最后施加capital overlay。"
- 将此规则写入P0，阻塞S1启动前完成

---

## 分歧点 5：sleeve FDR 计入规则

**DeepSeek R1**：P0（分层sleeve产生新假设，扩大实验族）  
**Review R1**：P1（sleeve的test_family_id归属规则未明确）  
**Main / Coder**：已识别但未给优先级

### 我的立场：P1，同意 Review R1 的优先级判断，但补充 DeepSeek 的核心关切

**理论支撑**：

1. **sleeve是否构成独立假设？** 这取决于sleeve的使用目的：
   - **诊断性sleeve**（如微盘诊断、次高分段）：目的是理解alpha来源分布，不独立支持keep决策。这类sleeve不应独立计入FDR实验族。
   - **候选策略sleeve**（如baseline_top_score、small_mid_mv_top_score）：如果sleeve的keep决策独立于baseline，则每个sleeve是一个独立假设，必须计入FDR。

2. **DeepSeek的核心关切正确**：如果5个sleeve都独立做keep决策，实验族从1个baseline变成5个baseline，BH校正的p值阈值会从0.05降到约0.01（假设5个独立检验）。这确实会膨胀实验族大小。

3. **但P0过高**：文档已经要求"所有sleeve计入attempt_count"，这意味着实验族大小已经包含了sleeve。问题只是"是否每个sleeve独立触发FDR"——这是一个实操细节，不是框架缺陷。

**最终建议**：
- 明确规则：**诊断性sleeve不独立触发FDR，但计入attempt_count；候选策略sleeve独立触发FDR**
- 具体来说：
  - `baseline_top_score`：独立触发FDR（这是主策略）
  - `upper_middle_score_p80_p95`：诊断性，不独立触发FDR
  - `small_mid_mv_p20_p60_top_score`：候选策略，独立触发FDR
  - `balanced_mv_p20_p80_score_p60_p95`：诊断性，不独立触发FDR
  - `micro_mv_p0_p20_diagnostic_only`：纯诊断，不独立触发FDR
- 在执行规范§3.1.1中明确每个sleeve的FDR归属
- 将此规则写入P1

---

## 分歧点 6：concept shift 独立性假设

**DeepSeek R1**：P0（5/6门槛基于步间独立假设，但walk-forward IC存在自相关，实际误报率可能显著高于10.9%）  
**Review R1**：提及但未升级为P0  
**Main / Coder**：未提及

### 我的立场：同意 DeepSeek，P0

**理论支撑**：

1. **自相关的存在是确定的**：walk-forward的训练窗口为5年、步长为63个交易日，相邻步的训练窗口重叠约4.75年（95%重叠）。这意味着相邻步的IC高度相关——如果第N步的训练窗口包含一个异常年份（如2015年牛市），第N+1步也会包含该异常年份。文献中walk-forward IC的相邻步相关系数通常在0.3-0.6之间。

2. **自相关膨胀误报率**：在正自相关下，连续步IC同号的概率高于独立假设。以ρ=0.4的AR(1)模型为例，P(IC_N < 0 | IC_{N-1} < 0) ≈ 0.65（而非独立假设的0.5）。此时P(至少5/6步为负) ≈ C(6,5)×0.65^5×0.35 + 0.65^6 ≈ 0.25+0.08 = 0.33，远高于独立假设的10.9%。

3. **这不是理论风险，是实际风险**：A股市场存在明显的 regime clustering（牛市/熊市各持续数月），IC的自相关在A股可能比美股更高。如果误报率实际是33%而非10.9%，那么5/6门槛会在约1/3的walk-forward中产生虚假yellow信号，导致不必要的策略降级。

4. **解决方案存在且可行**：
   - **Block bootstrap**：对OOT IC序列做block bootstrap（block=21天），估计实际误报率
   - **Permutation test**：随机打乱OOT IC的时序，计算P(至少5/6步为负)的排列p值
   - **调整门槛**：如果实际误报率过高，可以调整为6/6（全部为负才触发yellow）或增加步数（如8/10）

**最终建议**：
- 在执行规范§6.1.5中明确："5/6 yellow门槛的10.9%误报率基于IC步间独立假设。实际walk-forward中IC存在自相关（因训练窗口重叠），实际误报率可能显著高于10.9%。必须通过block bootstrap（block=21天）或permutation test估计实际误报率。"
- 在Phase A0.2中增加一项任务：使用历史OOT数据估计IC的相邻步自相关系数，计算5/6门槛的实际误报率
- 如果实际误报率>20%，考虑调整门槛（如6/6或增加步数）
- 将此规则写入P0，阻塞S1 keep决策

---

## 附录：分歧点优先级汇总

| # | 分歧点 | DeepSeek | Review R1 | Main R1 | Coder R1 | **Review R2 独立判断** |
|---|--------|----------|-----------|---------|----------|----------------------|
| 1 | 统计功效MDE | P0 | — | — | — | **P1**（不阻塞启动，但A0阶段必须完成） |
| 2 | Phase A0工作量 | — | — | 25-45日 | 35-60日 | **支持35-60日**（Coder的逐项分解更有说服力） |
| 3 | CSRP命中窗口 | P2 | P0 | P1 | — | **P0**（误报率框架的前提参数） |
| 4 | 裁剪与overlay顺序 | — | P0 | — | — | **P0**（先裁剪再overlay） |
| 5 | sleeve FDR计入 | P0 | P1 | — | — | **P1**（区分诊断性vs候选策略sleeve） |
| 6 | concept shift独立性 | P0 | — | — | — | **P0**（自相关膨胀误报率是确定性风险） |

### 与各Agent的分歧总结

- **与DeepSeek的分歧**：MDE分析（DeepSeek P0 vs 我P1）、sleeve FDR（DeepSeek P0 vs 我P1）。我认为MDE和sleeve FDR都不阻塞S1启动，但DeepSeek对这两个问题的理论分析是正确的。
- **与Main R1的分歧**：CSRP命中窗口（Main P1 vs 我P0）。我认为命中窗口是误报率框架的前提参数，不是"可以后续补充"的细节。
- **与Review R1（我自己）的分歧**：concept shift独立性假设在R1中我只作为一般性问题提及，R2中升级为P0，因为DeepSeek的定量分析（自相关下误报率可达33%）说服了我。
- **与Coder的分歧**：Phase A0工作量我支持Coder的35-60日估计，但建议的拆分方式略有不同（A0.2a/2b vs Coder的类似拆分）。

---

*Review Agent R2 交叉审阅完成。核心结论：6个分歧点中3个P0（CSRP命中窗口、裁剪与overlay顺序、concept shift独立性）、2个P1（MDE分析、sleeve FDR）、1个支持Coder（工作量35-60日）。*
