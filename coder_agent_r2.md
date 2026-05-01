# Coder Agent 交叉审阅与质证（R2）

> 角色：量化开发/数据工程/架构设计专家
> 日期：2026-05-01
> 审阅对象：Main Agent、Review Agent、DeepSeek Agent 的独立审计报告
> 方法：逐条质证，给出认同/反对/遗漏判断及工程依据

---

## 1. 认同的其他 Agent 观点

### 1.1 认同 Main Agent：walk-forward 总步数必须量化

Main 指出"24步只是最低门槛，实际约180步"，这与我 R1 的计算一致。180步的量级直接影响：
- 实验台账的存储规划（180 × 7 模型 × 3 权重方案 = 3,780 条记录）
- block bootstrap 的计算量（180步的IC序列 vs 24步，bootstrap 收敛速度不同）
- 全量运行时间估算

**工程补充**：180步 × 每步读取5年Parquet（~2秒I/O）= 360秒纯I/O。如果每次重新读取，加上训练时间，全量S1-M约需8-12小时。但如果预加载面板到内存，I/O可降至0。

### 1.2 认同 DeepSeek：1日标签40天purge过度保守

DeepSeek 的分析在工程上完全正确。1日标签的label overlap窗口仅1天，40天purge意味着：
- 每个训练窗口损失 40/1260 ≈ 3.2% 的样本
- 对于S1-D的4,000+个OOT step，累计损失的训练样本量可观
- 信息泄漏的根源是特征自相关，不是标签重叠——两者是不同概念

**工程实现角度**：purge值越大，walk-forward calendar中每个step的训练窗口越短，训练样本越少，模型质量越差。10天purge vs 40天purge的差异在5年窗口中约2.4%的样本，看似不大，但在早期年份（2005-2010，股票数少）影响更显著。

### 1.3 认同 Review Agent：walk-forward calendar 是 P0 阻塞项

Review 正确指出"所有 P0 治理工件全部 missing"。从工程角度看，walk-forward calendar 是整个系统的**第一块砖**——没有它，无法定义训练/测试边界，无法计算purge/embargo，无法生成实验台账的step_id，无法验证标签成熟度。我 R1 已将此列为最高复杂度组件。

### 1.4 认同 Main Agent：实验台账应改为 SQLite/JSONL

Main 和我在 R1 都提出了这个建议。70+字段的TSV在工程上不可维护：
- 字段对齐错误难以检测
- 不支持嵌套结构（如cost_breakdown、shock_state摘要）
- 不支持schema evolution（添加新字段需重写整个文件）
- 不支持并发写入（多个实验并行记录会冲突）
- 不支持高效查询（"找出所有Sharpe>1且holdout未污染的实验"需要全量加载）

### 1.5 认同 DeepSeek：FDR 应扩展到完整实验族

DeepSeek 指出 FDR 只针对因子数不够，应覆盖"因子 × 标签 × 模型 × 半衰期 × 训练窗口"的完整实验族。从工程角度看，test_family_registry 的实现需要：
- 定义清晰的族边界规则
- 自动追踪每个族内的trial_count
- 在实验台账中记录attempt_count和test_family_id

我 R1 已提出这个建议，DeepSeek 的独立确认增强了其必要性。

### 1.6 认同 Review Agent：预注册 LightGBM/XGBoost 超参数

Review 建议预注册默认超参数（n_estimators=500、max_depth=6等）。从工程角度看：
- 超参数搜索必须在训练窗口内完成，不能使用OOT信息
- 如果不做预注册，每次训练时的超参数选择可能引入隐性过拟合
- 预注册的超参数应写入 validation_params.json，作为机器可读的约束

### 1.7 认同 Main Agent：concept shift yellow 误报率34.4%

Main 和 DeepSeek 都独立计算了这个数字，结论一致。34.4%的误报率意味着约1/3的因子会被标记为yellow，导致大量不必要的revalidation。从工程角度看：
- revalidation 需要重新运行walk-forward的子集，计算成本不低
- 高误报率会导致"狼来了"效应，降低团队对yellow告警的重视
- 建议调整为"最近8步中至少6步为负"（误报率约10.9%）

---

## 2. 反对的其他 Agent 观点

### 2.1 反对 DeepSeek：1日标签 purge 建议10天可能过低

DeepSeek 建议 `max(label_horizon * 5, 10)` = 10天。我 R1 建议20天。分歧在于：

**DeepSeek 的论点**：1日标签的label overlap仅1天，10天purge已足够。

**我的反驳**：
1. **信息泄漏不仅来自标签重叠，还来自特征自相关**。A股日频数据中，许多特征（如动量、波动率、成交额）的自相关远超1天。10天purge可能不足以隔离特征中的残留信息。
2. **de Prado (2018) 的建议是 purge ≥ label_horizon，而非 purge = label_horizon**。他明确指出purge的目的是防止"标签和特征中包含的关于同一事件的信息"泄漏，这与label overlap是不同概念。
3. **工程安全边际**：在walk-forward中，purge计算一旦确定就很难修改（因为会影响所有step的训练窗口）。选择一个更保守的purge值（如20天）的额外成本很小（损失约1.6%样本），但安全边际显著更高。
4. **实证建议**：不如在validation_params.json中预注册 purge=20 作为默认值，同时报告 purge=10 的敏感性结果。如果10天和20天的IC差异不显著，则可以接受10天。

**结论**：我维持20天的建议，但同意将10天作为敏感性报告项。

### 2.2 反对 Review Agent：估值因子PIT问题"可能被高估"

Review 认为"如果供应商已经处理了PIT问题，则不必将PE/PB完全排除在S1之外"。

**Review 的论点**：供应商可能在T日盘后已使用最新已公告财报计算PE/PB。

**我的反驳**：
1. **供应商的PIT处理逻辑是黑箱**。我们无法确认供应商是否真的在公告日后即时更新。不同供应商（如Wind、东方财富、同花顺）的处理方式可能不同。
2. **`valuation_daily` 已经有146,208个missing key**，说明数据质量本身存在缺口。在这个缺口之上再假设供应商的PIT处理是正确的，逻辑上不自洽。
3. **保守原则**：在无法验证的情况下，应假设PE/PB存在PIT问题，直到完成 `available_at` 审计。这不是"高估"问题，而是"无法确认"问题。
4. **工程建议**：先做 `available_at` 审计（检查财报公告日后的估值更新延迟），再决定是否将PE/PB纳入S1。审计成本低（只需对比公告日和估值更新日），但能消除一个重大不确定性。

### 2.3 反对 Review Agent：全量walk-forward在Arc B390上"可能需要100+小时"

Review 估算"LightGBM训练15M行×50特征可能需要10-30分钟/次，全量运行可能需要100+小时"。

**我的反驳**：
1. **15M行是整个数据集的大小，不是单次训练的输入**。每次训练只读取5年窗口，约300万行（不是1500万行）。LightGBM在300万行×50特征的规模下，单次训练约30-120秒（取决于超参数和硬件），不是10-30分钟。
2. **更准确的估算**：
   - 全量步数：约80个refit点（63天重训频率，20年OOT窗口）
   - 每步训练模型数：7种模型 × 3种权重方案 = 21次
   - 单次训练时间：平均60秒
   - 总训练时间：80 × 21 × 60秒 ≈ 28小时
   - 加上I/O和评估：总计约35-45小时
3. **如果预加载面板到内存**：I/O开销可忽略，总时间可降至30-40小时。
4. **并行化空间**：单因子IC计算可以高度并行（50+个因子相互独立），LightGBM训练可以用joblib并行（控制并发数避免OOM）。

**结论**：全量walk-forward在Arc B390上约需30-45小时，不是100+小时。但仍建议先用24步smoke test验证流程正确性。

### 2.4 反对 DeepSeek：GMSL阈值应使用全局分位数

DeepSeek 建议"对GMSL阈值使用全局分位数（如VIX的95th percentile基于1990-至今）"。

**我的反驳**：
1. **全局分位数忽略了市场结构变化**。VIX在1990年代的分布与2020年代完全不同（2008年后VIX中枢系统性下移）。使用1990-至今的全局分位数会导致早期的"高波动"在后期看来只是"正常波动"。
2. **walk-forward的哲学是"只使用train_end以前的数据"**。GMSL阈值也应遵循这一原则——在每个训练窗口内计算阈值，确保阈值的计算不使用未来信息。
3. **折中方案**：可以在每个训练窗口内计算阈值，但使用更长的lookback（如10年而非5年），以获得更稳定的分位数估计。这比全局分位数更符合walk-forward原则，同时解决了短窗口阈值不稳定的问题。

### 2.5 反对 Main Agent：Phase A0 工作量"4-6周"

Main 估计Phase A0需要4-6周。我R1估计25-45工作日。

**分歧分析**：
- Main 的4-6周 ≈ 20-30个工作日，我估计25-45个工作日
- 差异主要在walk-forward calendar和orders audit的复杂度评估上

**我的反驳**：
1. **walk-forward calendar 不是"1-2周"能完成的**。它需要：
   - 精确对齐交易日历（不能用自然日近似）
   - 处理S1-M和S1-D/S1-R的不同purge/embargo规则
   - 处理refit和rebalance频率不同步的问题
   - 处理holdout剥离
   - 处理标签成熟度约束
   - 生成审计报告验证calendar正确性
   - 这至少需要5-8个工作日
2. **orders audit 的状态机实现**：
   - 涨停买不到、跌停卖不出、停牌延迟、连续锁死、解锁后反转
   - 每个状态转换都需要记录timestamp、reason和next_action
   - 需要与execution_label_audit联动
   - 这至少需要5-8个工作日
3. **execution_label audit**：
   - T+1 open proxy的构建
   - 分批执行的拆单逻辑
   - 三种执行口径的对比
   - 这至少需要5-10个工作日

**结论**：我维持25-45工作日的估计。Main的4-6周（20-30天）可能低估了orders audit和execution label audit的复杂度。

### 2.6 反对 Review Agent：block bootstrap 应增加 block=40/60 敏感性

Review 建议"对S1-M月选股，增加block=40/60的敏感性分析"。

**我的反驳**：
1. **block_days 的选择应有理论依据，而非随意增加**。DeepSeek 正确指出"IC序列的block_days应基于IC的empirical ACF"。如果IC的ACF在lag=21后已衰减到0，使用block=40/60不会改变结果，只会增加计算量。
2. **正确的做法**：先计算IC序列的empirical ACF，确定IC的自相关半衰期，然后用 `block_days = max(ic_half_life, label_horizon, rebalance_interval)` 作为block长度。这才是有理论支撑的选择。
3. **如果要做敏感性**：应在validation_params.json中预注册"block_days敏感性报告"的要求，但不应将其作为keep/discard的门槛。block=21是基于标签horizon和rebalance interval的选择，有明确的理论依据。

---

## 3. 其他 Agent 遗漏但重要的问题

### 3.1 walk-forward calendar 的 refit/rebalance 不同步问题

**问题描述**：S1-M 是"固定月末/月初调仓"（约21天频率），但"每63个交易日重训"。63/21 = 3，即每3次调仓重训一次模型。在非重训step，使用冻结模型。

**遗漏情况**：四位Agent都提到了walk-forward calendar，但都没有深入讨论refit和rebalance不同步的工程实现细节。

**工程挑战**：
1. **模型版本注册表**：需要维护一个 `model_version_registry`，记录每个模型的train_end、panel_hash、frozen_until等元数据
2. **非重训step的模型选择逻辑**：当refit和rebalance不在同一天时，需要明确使用哪个模型版本。例如：
   - Step 1（月末）：重训，使用新模型v1
   - Step 2（月末）：不重训，使用冻结模型v1
   - Step 3（月末）：不重训，使用冻结模型v1
   - Step 4（月末）：重训，使用新模型v2
3. **模型版本的向后兼容**：如果v2的特征集合与v1不同（如因特征选择），非重训step使用v1模型但需要v2的特征——这会导致特征不匹配

**建议**：
- 在walk-forward calendar中增加 `model_refit_flag` 和 `frozen_model_version` 字段
- 实现一个 `ModelRegistry` 类，管理模型版本的注册、查询和冻结
- 在非重训step，强制使用与当前特征集合兼容的最新冻结模型

### 3.2 实验台账的并发写入问题

**问题描述**：如果多个实验并行运行（如不同因子的单因子IC计算），它们需要同时写入实验台账。TSV格式不支持并发写入——多个进程同时写入会导致文件损坏或记录覆盖。

**遗漏情况**：Main和Review都建议改为SQLite，但没有讨论并发写入的具体实现。

**工程方案**：
1. **SQLite的WAL模式**：SQLite支持Write-Ahead Logging，允许多个读连接和一个写连接并发。适合"多实验并行写入"的场景。
2. **DuckDB的并发限制**：DuckDB默认不支持多个写连接并发（它更偏向OLAP读密集场景）。如果实验台账需要高并发写入，SQLite比DuckDB更合适。
3. **推荐方案**：SQLite作为实验台账的存储后端，使用WAL模式支持并发写入。DuckDB用于对实验台账的分析查询（只读）。

### 3.3 orders_audit 的字段补充

我在R1提出了6个补充字段（execution_price、execution_slippage、order_status、cost_breakdown、prev_weight、turnover_contribution）。没有其他Agent讨论这些字段的实现复杂度。

**实现复杂度评估**：

| 字段 | 复杂度 | 说明 |
|------|--------|------|
| `execution_price` | 低 | 直接从prices_daily_unadjusted读取T+1 open |
| `execution_slippage` | 低 | = execution_price / decision_price - 1 |
| `order_status` | 中 | 需要实现订单状态机FSM |
| `cost_breakdown` | 中 | 需要从trading_costs读取分项费率 |
| `prev_weight` | 中 | 需要维护前一日持仓快照 |
| `turnover_contribution` | 中 | = |new_weight - prev_weight|，需要prev_weight |

**S1阶段建议**：`execution_price` 和 `execution_slippage` 是低成本高价值的字段，必须在S1实现。`order_status` 是orders_audit的核心，也必须实现。`cost_breakdown`、`prev_weight`、`turnover_contribution` 可以在S1的简化版本中省略（用总成本替代分项），在S1.5中补充。

### 3.4 S1-D/S1-R 的内存优化方案

我R1提出"预加载整个features/labels面板到内存（3GB）"。没有其他Agent讨论这个方案的可行性。

**可行性分析**：
- features/labels 各15,420,654行 × 50列 × 4字节/float32 ≈ 3GB
- 两个面板合计约6GB
- 加上元数据和中间变量，峰值内存约8-10GB
- Intel Arc B390 有16.5GB显存，但CPU端内存取决于系统RAM
- 如果系统RAM为16GB，预加载6GB面板后剩余10GB给OS、Python和其他进程——**可行但紧张**
- 如果系统RAM为8GB，**不可行**——需要使用memory-mapped parquet或流式处理

**建议**：
- 在validation_params.json中增加 `panel_memory_mode` 参数：`preload`（16GB+ RAM）/ `mmap`（8-16GB RAM）/ `streaming`（<8GB RAM）
- 在S1启动前，自动检测系统可用内存并选择合适的模式
- 对S1-M（24-180步），即使使用streaming模式，总I/O时间也在可接受范围内（约10分钟）
- 对S1-D/S1-R（4000+步），preload模式可以将I/O从2.2小时降至0

### 3.5 walk-forward calendar 的验证机制

**遗漏情况**：所有Agent都讨论了walk-forward calendar的生成，但没有人讨论如何验证生成的calendar是否正确。

**验证方案**：
1. **Purge约束验证**：对每个step，检查 `train_end + purge_days + embargo_days <= oot_start`
2. **Holdout隔离验证**：检查没有任何step的train窗口包含holdout期间的数据
3. **标签成熟度验证**：检查每个step的 `label_maturity_date` 在 `oot_start + label_horizon` 之后
4. **窗口重叠率验证**：计算相邻step的训练窗口重叠率，报告是否在预期范围内（~95%）
5. **步数一致性验证**：检查生成的step数与预期一致（S1-M约180步，S1-D约4000步）

**建议**：实现一个 `WalkForwardCalendarValidator` 类，在calendar生成后自动运行以上验证，输出验证报告。

### 3.6 数据版本控制与可复现性

**遗漏情况**：所有Agent都讨论了数据质量，但没有人讨论数据版本控制。如果warehouse重建（如修复了某个bug），如何确保之前的实验结果仍然可复现？

**工程方案**：
1. **Panel hash**：文档已要求记录 `panel_hash`，这是正确的方向
2. **Parquet文件的content hash**：对每个Parquet文件计算SHA256，记录在manifest中
3. **Warehouse版本号**：为每次warehouse重建分配版本号（如v1.0、v1.1），实验台账中记录 `warehouse_version`
4. **快照机制**：对关键表（features、labels）在实验运行时保存快照，或至少记录其content hash，以便事后验证数据是否变化

---

## 4. 关键分歧的独立立场

### 4.1 1日标签 purge：10天 vs 20天

**独立立场：20天**

理由：
1. 信息泄漏不仅来自标签重叠，还来自特征自相关。10天可能不足以隔离特征中的残留信息。
2. de Prado的建议是purge ≥ label_horizon，但他的讨论主要针对标签重叠，未充分考虑特征自相关。
3. 20天purge的额外成本很小（损失约1.6%样本），但安全边际显著更高。
4. 建议在validation_params.json中预注册purge=20为默认值，同时报告purge=10的敏感性结果。

### 4.2 实验台账格式：SQLite vs TSV vs JSONL

**独立立场：SQLite（首选），JSONL（备选）**

理由：
1. **SQLite优势**：
   - 支持SQL查询（"找出所有Sharpe>1且holdout未污染的实验"）
   - 支持schema evolution（添加新字段不需要重写整个文件）
   - 支持并发写入（WAL模式）
   - 支持索引（对run_id、track_id等字段建立索引）
   - 单文件存储，便于备份和迁移
2. **JSONL优势**：
   - 每行一个JSON对象，支持嵌套结构
   - 可以用 `jq` 命令行工具查询
   - 不需要额外的数据库引擎
3. **JSONL劣势**：
   - 不支持索引，大文件查询慢
   - 不支持并发写入（需要外部锁）
   - schema evolution需要额外处理
4. **DuckDB的适用场景**：只读分析查询（如对实验台账做聚合统计），不适合作为写入端

**建议**：SQLite作为实验台账的主存储，DuckDB用于分析查询。JSONL作为中间格式（实验运行时先写入JSONL，结束后批量导入SQLite）。

### 4.3 Phase A0 工作量：25-45工作日

**独立立场：维持25-45工作日**

理由：
1. walk-forward calendar的精确实现（5-8天）是最高复杂度的单一组件
2. orders audit的状态机实现（5-8天）需要处理A股特有的涨跌停、停牌、T+1等复杂场景
3. execution label audit（5-10天）需要构建T+1 open proxy、分批执行、三种执行口径对比
4. 其他组件（track_registry、holdout_log、universe_audit等）合计约10-19天

**并行化空间**：
- walk-forward calendar 和 orders audit 可以并行开发（无依赖）
- execution label audit 依赖 prices_daily_unadjusted，但不依赖 walk-forward calendar
- universe_daily_construction_audit 可以与以上三个并行
- **关键路径**：walk-forward calendar → 实验台账 → KeepDecisionEngine

### 4.4 walk-forward calendar 实现：refit/rebalance 不同步

**独立立场：维护模型版本注册表**

方案：
1. 在walk-forward calendar中增加 `model_refit_flag`（布尔值，标记本step是否重训）和 `frozen_model_version`（字符串，指向冻结的模型版本）
2. 实现 `ModelRegistry` 类：
   ```python
   class ModelRegistry:
       def __init__(self):
           self.models = {}  # version -> model artifact
           self.current_version = None
       
       def register(self, version, model, train_end, panel_hash):
           self.models[version] = {
               'model': model,
               'train_end': train_end,
               'panel_hash': panel_hash,
           }
           self.current_version = version
       
       def get_frozen_model(self, step_date):
           """返回step_date之前最近的冻结模型"""
           candidates = [
               (v, m) for v, m in self.models.items()
               if m['train_end'] <= step_date
           ]
           return max(candidates, key=lambda x: x[1]['train_end'])
   ```
3. 在非重训step，从ModelRegistry获取最近的冻结模型
4. 如果冻结模型的特征集合与当前step不兼容，记录warning并跳过该step

### 4.5 orders_audit 补充字段

**独立立场：S1阶段实现核心字段，S1.5补充完整字段**

S1必须实现：
- `execution_price`（低成本高价值）
- `execution_slippage`（低成本高价值）
- `order_status`（orders_audit的核心）

S1.5补充：
- `cost_breakdown`（需要trading_costs的分项费率）
- `prev_weight`（需要持仓状态管理器）
- `turnover_contribution`（依赖prev_weight）

### 4.6 S1-D/S1-R I/O优化：预加载面板到内存

**独立立场：可行，但需要根据系统RAM动态选择模式**

- 16GB+ RAM：预加载整个面板（6GB），I/O开销为0
- 8-16GB RAM：使用memory-mapped parquet，按需读取
- <8GB RAM：使用streaming模式，每次读取5年窗口

建议在S1启动前自动检测系统可用内存，选择合适的模式。对于S1-M（24-180步），即使使用streaming模式，总I/O时间也在可接受范围内（约10分钟）。对于S1-D/S1-R（4000+步），预加载模式可以将I/O从2.2小时降至0。

---

## 5. 总结

### 共识点
1. walk-forward calendar 是 P0 阻塞项
2. 实验台账应从 TSV 升级为 SQLite
3. 1日标签40天purge过度保守
4. FDR 应扩展到完整实验族
5. concept shift yellow 误报率34.4%过高
6. 全量walk-forward在Arc B390上约需30-45小时（非100+小时）

### 分歧点
1. **1日标签purge**：DeepSeek建议10天，我建议20天。核心分歧在"信息泄漏是否仅来自标签重叠"
2. **Phase A0工作量**：Main估计4-6周（20-30天），我估计25-45天。差异在orders audit和execution label audit的复杂度评估
3. **GMSL阈值**：DeepSeek建议全局分位数，我建议训练窗口内分位数（但用更长lookback）。核心分歧在"是否违反walk-forward原则"
4. **block bootstrap敏感性**：Review建议增加block=40/60，我建议基于IC的empirical ACF选择block长度。核心分歧在"是否有理论依据"

### 遗漏项
1. refit/rebalance不同步的工程实现细节（模型版本注册表）
2. 实验台账的并发写入方案（SQLite WAL模式）
3. orders_audit补充字段的实现复杂度和分阶段计划
4. S1-D/S1-R的内存优化方案（根据RAM动态选择模式）
5. walk-forward calendar的验证机制
6. 数据版本控制与可复现性（warehouse版本号、content hash）

---

> 交叉审阅独立形成，基于四份审计报告的内容和量化系统工程实践经验。所有工程估算基于实际硬件配置（Intel Arc B390、16.5GB显存、NVMe SSD）和Python包性能（LightGBM、pandas、PyArrow）。
