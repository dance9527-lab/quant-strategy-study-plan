import os
import pandas as pd

base = "D:/quantum_a0/quant-strategy-study-plan/external_data_runs/20260501"

# 读取物理文件扫描
phys = pd.read_csv(f"{base}/physical_files_scan.csv")

# 定义数据集元数据
# 格式: (logical_id, physical_path_pattern, pit_status, coverage, scope, posthoc, issues, role)
datasets = []

def find_phys(pattern):
    """查找匹配的物理文件"""
    matches = phys[phys['physical_path'].str.contains(pattern, regex=False)]
    if len(matches) > 0:
        return matches.iloc[0]['physical_path'], matches.iloc[0]['row_count']
    return None, 0

def add(ds_id, phys_pattern, role, pit, coverage, scope, posthoc="", issues=""):
    path, rows = find_phys(phys_pattern)
    datasets.append({
        'dataset_id': ds_id,
        'physical_path': path if path else phys_pattern,
        'row_count': int(rows),
        'version_role': role,
        'pit_status': pit,
        'coverage_scope': coverage,
        'sample_or_full': scope,
        'posthoc_fields': posthoc,
        'blocking_issues': issues,
        'exists': path is not None,
    })

# === P0 阻塞数据 ===
add("suspend_d_raw", "suspension_events\\suspend_d_full.csv",
    "raw_evidence", "candidate_raw_blocked", "2000-2026", "full",
    "", "缺PIT字段;未来日期38行;主键重复82行;suspend_timing缺失99%")

add("suspend_d_staging", "suspend_d\\suspend_d.csv",
    "staging_candidate", "candidate_staging_partial_pit_no_lineage", "1999-2001", "sample",
    "", "仅5000行早期窗口;缺source_name/vendor/license/source_hash/time_zone/session_cutoff_rule")

add("namechange", "namechange\\namechange.csv",
    "staging_candidate", "candidate_staging_ready_pit_no_lineage", "2010-2026", "full",
    "", "Tushare重拉去重后3731行,ann_date100%,0重复;缺source_name/vendor/license/source_hash/time_zone/session_cutoff_rule")

add("index_000300", "index_000300\\index_000300.csv",
    "staging_candidate", "partial_effective_snapshot_no_removal_history", "2025-2026", "sample",
    "", "仅20个月度截面,无移除记录")

add("index_000905", "index_000905\\index_000905.csv",
    "staging_candidate", "partial_effective_snapshot_no_removal_history", "2025-2026", "sample",
    "", "仅12个月度截面")

add("index_000852", "index_000852\\index_000852.csv",
    "staging_candidate", "partial_effective_snapshot_no_removal_history", "2025-2026", "sample",
    "", "仅6个月度截面")

add("idx_cons_300", "000300_cons.csv",
    "raw_evidence", "partial_effective_snapshot_no_removal_history", "当前快照", "snapshot",
    "", "无移除记录,幸存者偏差")

add("idx_daily_300", "000300_SH_daily.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2005-2026", "full",
    "", "缺available_at/decision_time")

add("idx_daily_500", "000905_SH_daily.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2005-2026", "full",
    "", "缺available_at/decision_time")

add("idx_daily_1000", "000852_SH_daily.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2005-2026", "full",
    "", "缺available_at/decision_time")

add("stock_basic", "stock_basic\\stock_basic.csv",
    "staging_candidate", "reference_only_universe_metadata_blocked", "1990-2026", "full",
    "", "delist_date全空,不能解除幸存者偏差")

add("dividend", "dividend\\dividend.csv",
    "reference_only", "reference_only", "累计统计", "full",
    "", "非逐笔公司行为事件流;缺record_date/ex_rights_date等")

# === P1 风控执行 ===
add("margin_tushare", "margin_detail_tushare.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2025-2026", "sample",
    "", "仅2025-2026多月采样,非全历史")

add("northbound_tushare", "hk_hold_tushare.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2025-2026", "sample",
    "", "仅2025-2026采样")

add("share_float_akshare", "share_float_akshare_combined.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2010-2024", "full",
    "解禁前20日涨跌幅;解禁后20日涨跌幅;pre_20d_return;post_20d_return", "后验字段需禁用")

add("share_float_tushare", "share_float_tushare.csv",
    "raw_evidence", "raw_evidence_only", "2015-2035", "future_plans",
    "", "全部为未来解禁计划")

add("stk_limit", "stk_limit_tushare.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2026", "sample",
    "", "仅2026采样")

add("top_list", "top_list_tushare.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2026", "sample",
    "", "仅2026采样")

add("fut_daily", "fut_daily_tushare.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2019-2026", "full",
    "", "覆盖较好但缺PIT字段")

add("zt_pool", "zt_pool.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2026-04~05", "sample",
    "", "仅近1个月")

add("dt_pool", "dt_pool.csv",
    "raw_candidate", "candidate_raw_needs_pit", "2026-04~05", "sample",
    "", "仅近1个月")

# P1 staging samples - 标记为 sample_probe_only
add("margin_staging", "margin_trading.parquet",
    "staging_candidate", "sample_probe_only", "样本", "sample",
    "", "仅17行,1个asset_id")

add("northbound_staging", "northbound_flow.parquet",
    "staging_candidate", "sample_probe_only", "单日快照", "snapshot",
    "", "仅300行,2024-08-16")

add("fut_staging", "index_futures.parquet",
    "staging_candidate", "sample_probe_only", "样本", "sample",
    "", "仅400行,远小于raw18990行")

add("limit_staging", "limit_events\\limit_events_staging.csv",
    "staging_candidate", "sample_probe_only", "单日", "snapshot",
    "", "仅90行,2026-05-01,封板时间解析异常")

add("breadth_staging", "market_breadth\\market_breadth_staging.csv",
    "staging_candidate", "sample_probe_only", "单日", "snapshot",
    "", "仅1行,2026-04-30")

# === P1.5 GMSL ===
gmsl_files = [
    ("brent_crude", "WTI/布伦特原油"),
    ("wti_crude", "WTI原油"),
    ("sc_crude", "上海原油"),
    ("dxy", "美元指数"),
    ("usdcny_akshare", "美元/人民币AkShare"),
    ("usdcny_fred", "美元/人民币FRED"),
    ("fed_funds", "联邦基金利率"),
    ("ust_10y_fred", "10年国债FRED"),
    ("ust_10y_akshare", "10年国债AkShare"),
    ("ust_2y_fred", "2年国债FRED"),
    ("ust_2y_akshare", "2年国债AkShare"),
    ("ust_30y_fred", "30年国债FRED"),
    ("cboe_vix", "VIX Cboe"),
    ("fred_vix", "VIX FRED"),
    ("vix9d", "VIX9D"),
    ("vxn", "VXN"),
    ("gvz", "GVZ黄金波动率"),
    ("ovx", "OVX原油波动率"),
    ("gold_futures", "黄金期货"),
    ("silver_futures", "白银期货"),
    ("copper_fred", "铜期货"),
    ("spx", "标普500"),
    ("nasdaq", "纳斯达克"),
]
for sid, name in gmsl_files:
    path, rows = find_phys(f"mimo\\staging\\{sid}\\{sid}.parquet")
    if path:
        datasets.append({
            'dataset_id': f'gmsl_{sid}',
            'physical_path': path,
            'row_count': int(rows),
            'version_role': 'staging_candidate',
            'pit_status': 'stress_report_candidate',
            'coverage_scope': '历史',
            'sample_or_full': 'full',
            'posthoc_fields': '',
            'blocking_issues': '需session_cutoff/source_status/license复核;不得用于alpha/选模/阈值',
            'exists': True,
        })

# === P2 review ===
add("rev_lhb", "event_lhb_staged.csv",
    "staging_candidate", "blocked_mapping_error", "样本", "sample",
    "上榜后1日;上榜后2日;上榜后5日;上榜后10日;post_1d;post_2d;post_5d;post_10d",
    "asset_id全部为000001.SZ映射错误;后验字段需禁用;缺available_at/decision_time")

add("rev_holder", "event_holder_staged.csv",
    "staging_candidate", "source_probe_only", "样本", "sample",
    "", "缺available_at/decision_time")

add("rev_analyst_cninfo", "analyst_cninfo_staged.csv",
    "staging_candidate", "source_probe_only", "样本", "sample",
    "", "核心字段全空;主键重复;单日")

add("rev_bs", "fundamental_bs_staged.csv",
    "staging_candidate", "source_probe_only", "单股", "sample",
    "", "仅000001.SZ;大量财报科目为空")

add("rev_is", "fundamental_is_staged.csv",
    "staging_candidate", "source_probe_only", "单股", "sample",
    "", "仅000001.SZ;roe/gross_margin为空")

add("rev_minute", "minute_daily_staged.csv",
    "unusable", "unusable", "单股", "sample",
    "", "SSL阻断;仅78行单股")

add("rev_share_change", "event_share_change_staged.csv",
    "staging_candidate", "source_probe_only", "样本", "sample",
    "", "样本极少")

add("rev_news_cctv", "news_cctv_staged.csv",
    "reference_only", "reference_only", "样本", "sample", "", "仅11行")
add("rev_news_stock", "news_stock_staged.csv",
    "reference_only", "reference_only", "样本", "sample", "", "仅10行")
add("rev_news_div", "news_dividend_staged.csv",
    "reference_only", "reference_only", "样本", "sample", "", "仅15行")
add("rev_news_suspend", "news_suspend_staged.csv",
    "reference_only", "reference_only", "样本", "sample", "", "仅8行")
add("rev_analyst_ths", "analyst_ths_staged.csv",
    "unusable", "unusable", "样本", "sample", "", "仅3行")

# 生成 manifest
df = pd.DataFrame(datasets)
df.to_csv(f"{base}/data_manifest_v3.csv", index=False)

# 统计
print("=" * 80, flush=True)
print("数据集 Manifest v3", flush=True)
print("=" * 80, flush=True)
print(f"总数据集: {len(df)}, 存在: {df['exists'].sum()}", flush=True)

print(f"\n--- 按 pit_status ---", flush=True)
for s, g in df.groupby('pit_status'):
    print(f"  {s:50s} {len(g):>2} 个  {g['row_count'].sum():>10,} 行", flush=True)

print(f"\n--- 按 sample_or_full ---", flush=True)
for s, g in df.groupby('sample_or_full'):
    print(f"  {s:20s} {len(g):>2} 个  {g['row_count'].sum():>10,} 行", flush=True)

print(f"\n--- 按 version_role ---", flush=True)
for s, g in df.groupby('version_role'):
    print(f"  {s:20s} {len(g):>2} 个  {g['row_count'].sum():>10,} 行", flush=True)

print(f"\n--- 后验字段 ---", flush=True)
for _, r in df[df['posthoc_fields'] != ''].iterrows():
    print(f"  {r['dataset_id']:30s} → {r['posthoc_fields']}", flush=True)

print(f"\n--- 阻塞/不可用 ---", flush=True)
for _, r in df[df['pit_status'].str.contains('blocked|unusable|failed|invalid')].iterrows():
    print(f"  {r['dataset_id']:30s} → {r['pit_status']}", flush=True)

print(f"\n✅ 已保存: {base}/data_manifest_v3.csv", flush=True)
