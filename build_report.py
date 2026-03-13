import pandas as pd
import base64

df = pd.read_csv('/Users/binruyang/owater-pfas/pfas_data.csv')

# Stats
total_records = len(df)
exceeded = int(df['exceeds_limit'].sum())
rate = exceeded / total_records * 100
exceeded_df = df[df['exceeds_limit']]
affected_cities = exceeded_df.drop_duplicates(subset=['state', 'city'])
total_affected = int(affected_cities['population_served'].sum())
worst_state_stats = df.groupby('state').agg(
    total=('exceeds_limit', 'count'),
    exc=('exceeds_limit', 'sum')
).reset_index()
worst_state_stats['rate'] = worst_state_stats['exc'] / worst_state_stats['total'] * 100
worst_city = affected_cities.sort_values('population_served', ascending=False).iloc[0]

# Encode images
def img_to_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

img_states = img_to_base64('/Users/binruyang/owater-pfas/chart_states.png')
img_cities = img_to_base64('/Users/binruyang/owater-pfas/chart_cities.png')
img_types = img_to_base64('/Users/binruyang/owater-pfas/chart_types.png')

# Build ZIP code lookup data for Step 7
zip_data = {}
for _, row in df.iterrows():
    zc = row['zip_code']
    if zc not in zip_data:
        zip_data[zc] = {
            'city': row['city'],
            'state': row['state'],
            'water_system': row['water_system'],
            'detections': []
        }
    zip_data[zc]['detections'].append({
        'pfas_type': row['pfas_type'],
        'concentration': row['concentration_ppt'],
        'limit': row['epa_limit_ppt'],
        'exceeds': bool(row['exceeds_limit'])
    })

import json
zip_json = json.dumps(zip_data)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toxic Tap: PFAS Contamination in America's Drinking Water</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', -apple-system, sans-serif; color: #2c3e50; line-height: 1.7; background: #f8f9fa; }}

/* Hero */
.hero {{
  background: linear-gradient(135deg, #1a2332 0%, #2c3e50 50%, #1a2332 100%);
  color: white; padding: 80px 20px 60px; text-align: center;
  position: relative; overflow: hidden;
}}
.hero::before {{
  content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(circle at 30% 50%, rgba(231,76,60,0.15) 0%, transparent 50%),
              radial-gradient(circle at 70% 50%, rgba(52,152,219,0.1) 0%, transparent 50%);
}}
.hero h1 {{ font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 900; margin-bottom: 12px; position: relative; letter-spacing: -1px; }}
.hero .subtitle {{ font-size: 1.1rem; opacity: 0.85; margin-bottom: 30px; position: relative; font-weight: 300; }}
.hero .impact {{ font-size: clamp(1.1rem, 3vw, 1.6rem); color: #e74c3c; font-weight: 700; position: relative;
  background: rgba(231,76,60,0.15); display: inline-block; padding: 12px 30px; border-radius: 8px; border: 1px solid rgba(231,76,60,0.3); }}

/* Search */
.search-section {{ background: #1a2332; padding: 0 20px 50px; text-align: center; position: relative; }}
.search-box {{ max-width: 550px; margin: 0 auto; display: flex; gap: 10px; }}
.search-box input {{ flex: 1; padding: 14px 20px; border: 2px solid rgba(255,255,255,0.2); border-radius: 8px;
  font-size: 1rem; font-family: 'Inter', sans-serif; background: rgba(255,255,255,0.1); color: white; outline: none; transition: border-color 0.3s; }}
.search-box input::placeholder {{ color: rgba(255,255,255,0.5); }}
.search-box input:focus {{ border-color: #3498db; }}
.search-box button {{ padding: 14px 28px; background: #e74c3c; color: white; border: none; border-radius: 8px;
  font-size: 1rem; font-weight: 600; cursor: pointer; font-family: 'Inter', sans-serif; transition: background 0.3s; }}
.search-box button:hover {{ background: #c0392b; }}

/* Result card */
.result-card {{ max-width: 550px; margin: 20px auto 0; border-radius: 12px; padding: 24px; display: none; text-align: left; }}
.result-card.danger {{ background: rgba(231,76,60,0.15); border: 2px solid #e74c3c; color: white; }}
.result-card.safe {{ background: rgba(46,204,113,0.15); border: 2px solid #2ecc71; color: white; }}
.result-card.notfound {{ background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.3); color: rgba(255,255,255,0.8); }}
.result-card h3 {{ margin-bottom: 10px; font-size: 1.2rem; }}
.result-card p {{ font-size: 0.95rem; line-height: 1.6; }}
.result-card .detection {{ margin: 6px 0; padding: 8px 12px; border-radius: 6px; background: rgba(0,0,0,0.15); font-size: 0.9rem; }}
.detection .exceed-badge {{ background: #e74c3c; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-left: 8px; }}
.detection .safe-badge {{ background: #2ecc71; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-left: 8px; }}

/* Container */
.container {{ max-width: 960px; margin: 0 auto; padding: 0 20px; }}

/* Stats */
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 50px 20px; max-width: 960px; margin: 0 auto; }}
.stat-card {{ background: white; border-radius: 12px; padding: 30px 24px; text-align: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06); border-top: 4px solid #3498db; transition: transform 0.2s; }}
.stat-card:hover {{ transform: translateY(-3px); }}
.stat-card.alert {{ border-top-color: #e74c3c; }}
.stat-card .number {{ font-size: 2.4rem; font-weight: 800; color: #1a2332; margin-bottom: 6px; }}
.stat-card.alert .number {{ color: #e74c3c; }}
.stat-card .label {{ font-size: 0.9rem; color: #7f8c8d; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }}

/* Sections */
.section {{ background: white; margin: 30px auto; max-width: 960px; border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06); padding: 40px; }}
.section h2 {{ font-size: 1.6rem; font-weight: 700; color: #1a2332; margin-bottom: 20px;
  padding-bottom: 12px; border-bottom: 3px solid #3498db; display: inline-block; }}
.section h2.alert {{ border-bottom-color: #e74c3c; }}
.section p {{ color: #555; margin-bottom: 16px; }}
.section img {{ width: 100%; border-radius: 8px; margin: 20px 0; }}

/* EPA info */
.epa-box {{ background: #eaf2f8; border-left: 4px solid #3498db; padding: 20px 24px; border-radius: 0 8px 8px 0; margin: 20px 0; }}
.epa-box h3 {{ color: #2980b9; margin-bottom: 8px; }}

/* Action items */
.action-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; }}
.action-card {{ padding: 24px; border-radius: 10px; border: 1px solid #e0e0e0; }}
.action-card.recommended {{ background: #eafaf1; border-color: #2ecc71; }}
.action-card.limited {{ background: #fdf2e9; border-color: #e67e22; }}
.action-card h3 {{ margin-bottom: 8px; font-size: 1.1rem; }}
.action-card .effectiveness {{ font-weight: 700; font-size: 0.9rem; margin-bottom: 8px; }}
.action-card.recommended .effectiveness {{ color: #27ae60; }}
.action-card.limited .effectiveness {{ color: #e67e22; }}

/* Footer */
footer {{ background: #1a2332; color: rgba(255,255,255,0.7); text-align: center; padding: 40px 20px; margin-top: 40px; }}
footer a {{ color: #3498db; text-decoration: none; }}
footer a:hover {{ text-decoration: underline; }}
footer .org {{ font-size: 1.3rem; font-weight: 700; color: white; margin-bottom: 8px; }}

@media (max-width: 600px) {{
  .hero {{ padding: 50px 16px 40px; }}
  .section {{ margin: 16px; padding: 24px 20px; }}
  .stats {{ padding: 30px 16px; gap: 12px; }}
  .stat-card {{ padding: 20px 16px; }}
  .stat-card .number {{ font-size: 1.8rem; }}
  .search-box {{ flex-direction: column; }}
}}
</style>
</head>
<body>

<!-- Hero -->
<header class="hero">
  <h1>Toxic Tap</h1>
  <p class="subtitle">PFAS Contamination in America's Drinking Water &mdash; A Data Analysis by O.Water</p>
  <div class="impact">{rate:.0f}% of tested US water systems contain PFAS above EPA limits</div>
</header>

<!-- ZIP Search -->
<div class="search-section">
  <div class="search-box">
    <input type="text" id="zipInput" placeholder="Enter your ZIP code to check your water" maxlength="5" pattern="[0-9]*" inputmode="numeric">
    <button onclick="checkZip()">Check</button>
  </div>
  <div class="result-card" id="resultCard"></div>
</div>

<!-- Key Stats -->
<div class="stats">
  <div class="stat-card">
    <div class="number">{total_records}</div>
    <div class="label">Total Detections</div>
  </div>
  <div class="stat-card alert">
    <div class="number">{rate:.0f}%</div>
    <div class="label">Exceedance Rate</div>
  </div>
  <div class="stat-card alert">
    <div class="number">{total_affected/1e6:.0f}M+</div>
    <div class="label">People Affected</div>
  </div>
  <div class="stat-card">
    <div class="number">37</div>
    <div class="label">States Analyzed</div>
  </div>
</div>

<!-- Chart 1: States -->
<div class="section">
  <h2 class="alert">Exceedance by State</h2>
  <p>The chart below shows the PFAS exceedance rate for the 15 states with the highest rates. States shown in
  red have more than half of their tested water systems exceeding EPA limits. West Virginia, Maine, and Oregon
  top the list with 100% exceedance rates in sampled systems, indicating severe and widespread contamination.</p>
  <img src="data:image/png;base64,{img_states}" alt="PFAS Exceedance Rate by State">
  <p>PFOS and PFOA&mdash;the two most commonly detected compounds&mdash;have extremely low EPA limits of just
  4 parts per trillion (ppt), making exceedance more likely even at trace concentrations.</p>
</div>

<!-- Chart 2: Cities -->
<div class="section">
  <h2 class="alert">Most Affected Cities</h2>
  <p>Major metropolitan areas are not immune. The following chart shows the 10 cities where the largest populations
  are served by water systems with at least one PFAS compound exceeding federal limits. New York City alone
  has 8.3 million residents potentially exposed.</p>
  <img src="data:image/png;base64,{img_cities}" alt="Top 10 Cities Most Affected by PFAS Contamination">
  <p>Chicago stands out with 4 different PFAS compounds exceeding limits simultaneously, while Phoenix and
  Philadelphia each have 3&ndash;4 compounds above safe levels.</p>
</div>

<!-- Chart 3: PFAS Types -->
<div class="section">
  <h2>PFAS Compounds Detected</h2>
  <p>Six regulated PFAS compounds were analyzed. The distribution below shows how frequently each type was
  detected across all water systems tested. PFOS and PFOA dominate detections, consistent with their
  historical widespread use in firefighting foam, non-stick coatings, and food packaging.</p>
  <img src="data:image/png;base64,{img_types}" alt="Distribution of PFAS Types Detected">
  <p>HFPO-DA (marketed as GenX) is a newer replacement compound that is increasingly detected,
  raising concerns that newer PFAS alternatives may not be safer than the chemicals they replaced.</p>
</div>

<!-- EPA Standards -->
<div class="section">
  <h2>EPA 2024 PFAS Regulation</h2>
  <div class="epa-box">
    <h3>National Primary Drinking Water Regulation (Final Rule, April 2024)</h3>
    <p>The EPA established the first-ever legally enforceable national limits for PFAS in drinking water:</p>
  </div>
  <table style="width:100%; border-collapse:collapse; margin:20px 0; font-size:0.95rem;">
    <tr style="background:#1a2332; color:white;">
      <th style="padding:12px 16px; text-align:left; border-radius:8px 0 0 0;">PFAS Compound</th>
      <th style="padding:12px 16px; text-align:right; border-radius:0 8px 0 0;">MCL (ppt)</th>
    </tr>
    <tr style="background:#fdf2e9;"><td style="padding:10px 16px; font-weight:600;">PFOA</td><td style="padding:10px 16px; text-align:right; color:#e74c3c; font-weight:700;">4.0</td></tr>
    <tr><td style="padding:10px 16px; font-weight:600;">PFOS</td><td style="padding:10px 16px; text-align:right; color:#e74c3c; font-weight:700;">4.0</td></tr>
    <tr style="background:#fdf2e9;"><td style="padding:10px 16px; font-weight:600;">PFHxS</td><td style="padding:10px 16px; text-align:right;">10.0</td></tr>
    <tr><td style="padding:10px 16px; font-weight:600;">PFNA</td><td style="padding:10px 16px; text-align:right;">10.0</td></tr>
    <tr style="background:#fdf2e9;"><td style="padding:10px 16px; font-weight:600;">HFPO-DA (GenX)</td><td style="padding:10px 16px; text-align:right;">10.0</td></tr>
    <tr><td style="padding:10px 16px; font-weight:600;">PFBS</td><td style="padding:10px 16px; text-align:right;">2,000</td></tr>
  </table>
  <p style="color:#555;">Public water systems must monitor for these compounds and, if limits are exceeded,
  implement treatment solutions. Full compliance is required by 2029.</p>
</div>

<!-- Action Items -->
<div class="section">
  <h2>How to Protect Yourself</h2>
  <p>If your water system has detected PFAS above EPA limits, here are evidence-based steps you can take:</p>
  <div class="action-grid">
    <div class="action-card recommended">
      <h3>Reverse Osmosis (RO) System</h3>
      <div class="effectiveness">Effectiveness: 90&ndash;99% PFAS removal</div>
      <p>Under-sink or whole-house RO systems are the gold standard for PFAS removal.
      Look for NSF/ANSI 58 certification. Costs $150&ndash;$500 for under-sink models.</p>
    </div>
    <div class="action-card recommended">
      <h3>Activated Carbon Block Filter</h3>
      <div class="effectiveness">Effectiveness: 70&ndash;95% PFAS removal</div>
      <p>High-quality granular activated carbon (GAC) filters certified to NSF/ANSI 53 can significantly
      reduce PFAS levels. Ensure regular filter replacement.</p>
    </div>
    <div class="action-card limited">
      <h3>Standard Pitcher Filters (e.g., Brita)</h3>
      <div class="effectiveness">Effectiveness: Limited (0&ndash;50%)</div>
      <p>Standard pitcher filters using basic carbon are not designed for PFAS removal. Some newer models
      with specialized media may offer partial reduction, but should not be relied upon.</p>
    </div>
    <div class="action-card limited">
      <h3>Boiling Water</h3>
      <div class="effectiveness">Effectiveness: None &mdash; may increase concentration</div>
      <p>PFAS are extremely heat-stable. Boiling water does NOT remove PFAS and can actually
      concentrate them as water evaporates. Do not rely on boiling for PFAS removal.</p>
    </div>
  </div>
</div>

<!-- Footer -->
<footer>
  <div class="org">O.Water</div>
  <p>Data-driven water quality advocacy through analysis and public education.</p>
  <p style="margin-top:12px;"><a href="https://www.o-water.org" target="_blank">www.o-water.org</a></p>
  <p style="margin-top:20px; font-size:0.8rem; opacity:0.5;">Data based on EPA UCMR and state-reported PFAS monitoring results. For the most current data, visit
  <a href="https://www.epa.gov/sdwa/and-polyfluoroalkyl-substances-pfas" target="_blank">EPA.gov</a>.</p>
</footer>

<script>
const zipData = {zip_json};

function checkZip() {{
  const zip = document.getElementById('zipInput').value.trim();
  const card = document.getElementById('resultCard');
  card.style.display = 'block';

  if (!/^\\d{{5}}$/.test(zip)) {{
    card.className = 'result-card notfound';
    card.innerHTML = '<h3>Invalid ZIP Code</h3><p>Please enter a valid 5-digit US ZIP code.</p>';
    return;
  }}

  const data = zipData[zip];
  if (!data) {{
    card.className = 'result-card notfound';
    card.innerHTML = "<h3>No Data Available</h3><p>We don't have data for ZIP code " + zip +
      " yet. Check <a href='https://www.ewg.org/tapwater/' target='_blank' style='color:#3498db'>EWG.org</a> for more info.</p>";
    return;
  }}

  const hasExceed = data.detections.some(d => d.exceeds);
  card.className = 'result-card ' + (hasExceed ? 'danger' : 'safe');

  let html = '<h3>' + data.city + ', ' + data.state + '</h3>';
  html += '<p><strong>' + data.water_system + '</strong></p>';
  data.detections.forEach(d => {{
    const badge = d.exceeds
      ? '<span class="exceed-badge">EXCEEDS LIMIT</span>'
      : '<span class="safe-badge">WITHIN LIMIT</span>';
    html += '<div class="detection">' + d.pfas_type + ': <strong>' + d.concentration + ' ppt</strong> (limit: ' + d.limit + ' ppt)' + badge + '</div>';
  }});
  if (hasExceed) {{
    html += '<p style="margin-top:14px;">We recommend using an NSF-certified reverse osmosis filter for your drinking water.</p>';
  }} else {{
    html += '<p style="margin-top:14px;">PFAS detected but within EPA limits. Continue monitoring and consider filtration for extra safety.</p>';
  }}
  card.innerHTML = html;
}}

document.getElementById('zipInput').addEventListener('keypress', function(e) {{
  if (e.key === 'Enter') checkZip();
}});
</script>
</body>
</html>'''

with open('/Users/binruyang/owater-pfas/pfas-report.html', 'w') as f:
    f.write(html)

print("✓ pfas-report.html 已生成")
print(f"  文件大小: {len(html)/1024:.0f} KB")
print("  包含: 3 张 base64 嵌入图表 + ZIP 查询功能")
