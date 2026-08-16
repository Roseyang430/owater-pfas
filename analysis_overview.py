import pandas as pd
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR', str(BASE_DIR / '.matplotlib'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

df = pd.read_csv(BASE_DIR / 'pfas_data.csv')

# === 1. Basic Statistics ===
total = len(df)
exceeded = df['exceeds_limit'].sum()
rate = exceeded / total * 100
print("=" * 50)
print("PFAS 饮用水污染基本统计")
print("=" * 50)
print(f"总检测记录数: {total}")
print(f"超标记录数: {int(exceeded)}")
print(f"超标率: {rate:.1f}%")
print()

# Which PFAS type exceeds most
pfas_exceed = df[df['exceeds_limit']].groupby('pfas_type').size().sort_values(ascending=False)
print("各 PFAS 种类超标次数:")
for ptype, count in pfas_exceed.items():
    print(f"  {ptype}: {count} 次")
print(f"\n超标最多的 PFAS 种类: {pfas_exceed.index[0]} ({pfas_exceed.iloc[0]} 次)")

# === 2. Exceedance rate by state ===
print("\n" + "=" * 50)
print("各州超标率 (Top 10)")
print("=" * 50)
state_stats = df.groupby('state').agg(
    total=('exceeds_limit', 'count'),
    exceeded=('exceeds_limit', 'sum')
).reset_index()
state_stats['rate'] = state_stats['exceeded'] / state_stats['total'] * 100
state_stats = state_stats.sort_values('rate', ascending=False)

for _, row in state_stats.head(10).iterrows():
    print(f"  {row['state']}: {row['rate']:.1f}% ({int(row['exceeded'])}/{int(row['total'])})")

# === 3. Bar chart: Top 15 states ===
top15 = state_stats.head(15)
fig, ax = plt.subplots(figsize=(14, 7))
colors = ['#e74c3c' if r > 50 else '#3498db' for r in top15['rate']]
bars = ax.bar(top15['state'], top15['rate'], color=colors, edgecolor='white', linewidth=0.5)

# Add value labels
for bar, val in zip(bars, top15['rate']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{val:.0f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.set_xlabel('State', fontsize=13, fontweight='bold')
ax.set_ylabel('Exceedance Rate (%)', fontsize=13, fontweight='bold')
ax.set_title('PFAS Exceedance Rate by State', fontsize=18, fontweight='bold', pad=15)
ax.set_ylim(0, max(top15['rate']) + 12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.axhline(y=50, color='#e74c3c', linestyle='--', alpha=0.5, label='50% threshold')
ax.legend(fontsize=10)
plt.xticks(fontsize=11)
plt.yticks(fontsize=11)
plt.tight_layout()
plt.savefig(BASE_DIR / 'chart_states.png', dpi=150)
print("\n✓ chart_states.png 已保存")

# === Summary in Chinese ===
print("\n" + "=" * 50)
print("分析解读")
print("=" * 50)
print(f"在本数据集的 {total} 条水系统-PFAS 检出记录中，有 {int(exceeded)} 条超过了 EPA 2024 年设定的标准限值，")
print(f"整体超标率达 {rate:.1f}%。")
print(f"其中 {pfas_exceed.index[0]} 是超标最为严重的 PFAS 化学物质，共有 {pfas_exceed.iloc[0]} 次超标。")
print(f"从州级数据来看，{state_stats.iloc[0]['state']} 州的超标率最高，达到 {state_stats.iloc[0]['rate']:.1f}%。")
print("这意味着在这些地区，部分供水系统中的'永久化学物质'浓度已超过联邦安全标准，")
print("对居民健康构成潜在风险。")
