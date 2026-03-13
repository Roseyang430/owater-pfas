import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

df = pd.read_csv('/Users/binruyang/owater-pfas/pfas_data.csv')
exceeded_df = df[df['exceeds_limit']]

# === 1. Total affected population ===
# De-duplicate by city to avoid counting the same population multiple times
affected_by_city = exceeded_df.drop_duplicates(subset=['state', 'city'])[['state', 'city', 'population_served']]
total_affected = affected_by_city['population_served'].sum()
print("=" * 50)
print("受 PFAS 超标影响的人口分析")
print("=" * 50)
print(f"受 PFAS 超标影响的总人口: {total_affected:,} 人 (约 {total_affected/1e6:.1f} 百万人)")

# === 2. Top 10 most affected cities ===
city_pop = exceeded_df.groupby(['city', 'state']).agg(
    population=('population_served', 'first'),
    num_pfas_exceeded=('pfas_type', 'count')
).reset_index().sort_values('population', ascending=False).head(10)

print(f"\n受影响人口最多的 10 个城市:")
for _, row in city_pop.iterrows():
    print(f"  {row['city']}, {row['state']}: {row['population']:,} 人 ({row['num_pfas_exceeded']} 种 PFAS 超标)")

# Horizontal bar chart
fig, ax = plt.subplots(figsize=(12, 7))
city_pop_sorted = city_pop.sort_values('population', ascending=True)
colors = plt.cm.Reds([0.3 + 0.7 * i / len(city_pop_sorted) for i in range(len(city_pop_sorted))])
bars = ax.barh(
    [f"{row['city']}, {row['state']}" for _, row in city_pop_sorted.iterrows()],
    city_pop_sorted['population'],
    color=colors,
    edgecolor='white',
    linewidth=0.5
)
for bar, val in zip(bars, city_pop_sorted['population']):
    ax.text(val + 50000, bar.get_y() + bar.get_height()/2,
            f'{val:,.0f}', va='center', fontsize=10, fontweight='bold')

ax.set_xlabel('Population Served', fontsize=13, fontweight='bold')
ax.set_title('Top 10 Cities Most Affected by PFAS Contamination', fontsize=16, fontweight='bold', pad=15)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('/Users/binruyang/owater-pfas/chart_cities.png', dpi=150)
print("\n✓ chart_cities.png 已保存")

# === 3. PFAS type distribution pie chart ===
pfas_counts = df.groupby('pfas_type').size().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(9, 9))
wedge_colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
wedges, texts, autotexts = ax.pie(
    pfas_counts.values,
    labels=pfas_counts.index,
    autopct='%1.1f%%',
    colors=wedge_colors[:len(pfas_counts)],
    startangle=140,
    textprops={'fontsize': 12},
    pctdistance=0.8
)
for t in autotexts:
    t.set_fontweight('bold')
    t.set_fontsize(11)
ax.set_title('Distribution of PFAS Types Detected', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('/Users/binruyang/owater-pfas/chart_types.png', dpi=150)
print("✓ chart_types.png 已保存")

# === 4. Summary ===
print("\n" + "=" * 50)
print("总结：如果你是一个美国居民，这些数据意味着什么？")
print("=" * 50)
print(f"""
约 {total_affected/1e6:.0f} 百万美国人每天饮用的自来水中 PFAS 浓度超过了 EPA 2024 年设定的安全标准。
这些被称为"永久化学物质"的 PFAS 不会在环境中自然降解，会在人体中持续累积。

PFOS 和 PFOA 是最常被检出且超标最严重的两种 PFAS，EPA 将它们的安全限值设为仅 4 ppt
（万亿分之四）——这相当于一个奥运游泳池中的几滴水。

像纽约市、芝加哥、费城等大城市的供水系统也存在 PFAS 超标问题，
这意味着数百万城市居民在不知不觉中暴露于这些有害物质。

科学研究已将 PFAS 暴露与癌症、甲状腺疾病、免疫系统损伤和生殖问题联系起来。
如果你担心家中的饮用水安全，建议使用经 NSF 认证的反渗透（RO）过滤系统，
这是目前去除 PFAS 最有效的家用方法。普通的 Brita 滤水壶对 PFAS 的去除效果有限。
""")
