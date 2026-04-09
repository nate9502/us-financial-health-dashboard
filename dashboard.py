"""
=============================================================================
U.S. Financial Health Dashboard
=============================================================================
Analyst : Natheneal Alamrew
Degree  : B.S.B.A., Management Information Systems
School  : Christian Brothers University, December 2025

Description:
    This script loads pre-processed data from the Federal Reserve G.19
    Consumer Credit Report and FDIC Bank Performance datasets, then builds
    an 11-chart publication-quality dashboard using Matplotlib and Seaborn.

    The data was originally pulled from PostgreSQL using 16 SQL queries
    (see us_financial_analysis_clean.sql) and exported as CSV files.

Tools   : Python 3, Matplotlib, Seaborn, Pandas, NumPy
Data    : Federal Reserve FRED (TOTALNS, REVOLNS, NONREVNS, DTCTHFNM, SLOAS)
          FDIC Bank Financial Reports
Output  : Natheneal_Alamrew_Financial_Dashboard.png (180 DPI)
=============================================================================
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
# matplotlib.pyplot is the core plotting library — all charts are built with it
import matplotlib.pyplot as plt
# mpatches lets us create custom legend entries (colored squares/patches)
import matplotlib.patches as mpatches
# gridspec controls the layout of multiple charts on one figure
import matplotlib.gridspec as gridspec
# FancyBboxPatch draws rounded rectangle card backgrounds
from matplotlib.patches import FancyBboxPatch
# FuncFormatter lets us write custom functions to format axis tick labels
from matplotlib.ticker import FuncFormatter
# seaborn sets a clean statistical aesthetic on top of matplotlib
import seaborn as sns
# pandas is used to store and manipulate all tabular data
import pandas as pd
# numpy is used for array operations, spacing, and math
import numpy as np
# suppress non-critical warnings that don't affect output
import warnings
warnings.filterwarnings('ignore')


# ── GLOBAL STYLE SETUP ────────────────────────────────────────────────────────
# rcParams is matplotlib's global settings dictionary.
# Setting these once here applies the dark theme to every chart automatically
# so we don't have to repeat styling on each individual axis.
plt.rcParams.update({
    'figure.facecolor':  '#0a0e1a',   # outermost background (deep navy)
    'axes.facecolor':    '#0d1220',   # chart background (slightly lighter)
    'axes.edgecolor':    '#1e293b',   # border around each chart
    'axes.labelcolor':   '#94a3b8',   # x/y axis label text color
    'axes.titlecolor':   '#e2e8f8',   # chart title text color
    'axes.grid':         True,        # show gridlines on all charts
    'axes.axisbelow':    True,        # draw gridlines behind data, not over it
    'grid.color':        '#1e293b',   # gridline color (subtle dark line)
    'grid.linewidth':    0.6,         # thin gridlines for a clean look
    'grid.alpha':        0.8,         # slightly transparent gridlines
    'text.color':        '#e2e8f8',   # default text color across all elements
    'xtick.color':       '#475569',   # x-axis tick mark color
    'ytick.color':       '#475569',   # y-axis tick mark color
    'xtick.labelsize':   8,           # x-axis label font size
    'ytick.labelsize':   8,           # y-axis label font size
    'font.family':       'DejaVu Sans', # default font (ships with matplotlib)
    'legend.facecolor':  '#111827',   # legend background
    'legend.edgecolor':  '#1e293b',   # legend border
    'legend.fontsize':   8,           # legend text size
    'lines.linewidth':   2,           # default line thickness for line charts
    'patch.linewidth':   0,           # remove default border on bar/patch shapes
})


# ── COLOR PALETTE ─────────────────────────────────────────────────────────────
# All colors are defined as constants here so they are easy to change in one
# place and stay consistent across all 11 charts.
BG     = '#0a0e1a'   # page background — deep navy
CARD   = '#0d1220'   # chart card background — slightly lighter navy
BLUE   = '#4f8ef7'   # primary accent — used for totals and general data
GREEN  = '#3ecf8e'   # positive / high performance indicator
YELLOW = '#f5c842'   # moderate / warning indicator
RED    = '#f76e6e'   # negative / high risk indicator
PURPLE = '#a78bfa'   # revolving credit category color
ORANGE = '#fb923c'   # secondary accent (used sparingly)
MUTED  = '#64748b'   # secondary text — labels, footnotes
MUTED2 = '#94a3b8'   # primary muted text — descriptions, axis labels
WHITE  = '#e2e8f8'   # near-white — headlines and key values


# ── DATA ──────────────────────────────────────────────────────────────────────
# All values below were extracted from PostgreSQL using SQL queries and verified
# against the raw Federal Reserve and FDIC source files.
# Consumer debt figures are in BILLIONS of dollars.
# None represents missing data (e.g., student loan 2025 not yet reported).

# Federal Reserve G.19 Consumer Credit Data (2010–2025)
# Source series: TOTALNS, REVOLNS, NONREVNS, DTCTHFNM, SLOAS
debt_df = pd.DataFrame({
    'year':         [2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025],

    # Total outstanding consumer credit each year (all categories combined)
    'total':        [2511,2676,2811,2983,3184,3387,3500,3707,3891,4076,4103,4311,4671,4906,4993,5009],

    # Revolving credit = credit cards and lines of credit
    'revolving':    [845, 805, 809, 818, 842, 866, 897, 951, 999,1038, 958, 947,1083,1213,1289,1267],

    # Nonrevolving = auto loans, student loans, personal loans (fixed repayment)
    'nonrevolving': [1666,1870,2002,2165,2342,2521,2603,2756,2893,3037,3145,3364,3589,3693,3705,3742],

    # Auto loans subset (part of nonrevolving)
    'auto':         [690, 812, 819, 842, 862, 870, 735, 733, 727, 726, 724, 861, 904, 901, 930, 938],

    # Student loans subset (part of nonrevolving) — 2025 not yet reported
    'student':      [828, 926,1025,1118,1209,1296,1382,1464,1545,1618,1684,1728,1754,1749,1761, None],

    # Year-over-year growth rate for total consumer debt (%)
    # None for 2010 because there is no prior year to compare against
    'yoy':          [None,6.55,5.05,6.12,6.72,6.38,3.34,5.92,4.97,4.73,0.67,5.07,8.37,5.02,1.78,0.31],

    # YoY growth rate for auto loans specifically
    # Note: 2016 shows -15.49% due to a FRED series methodology change
    'auto_yoy':     [None,17.58,0.90,2.79,2.43,0.90,-15.49,-0.34,-0.79,-0.12,-0.22,18.81,5.02,-0.29,3.22,0.81],

    # YoY growth rate for student loans — declining trend as growth slows
    'student_yoy':  [None,11.76,10.78,9.03,8.13,7.20,6.65,5.93,5.58,4.73,4.03,2.61,1.54,-0.28,0.67,None],

    # YoY growth rate for revolving credit — surged 14.35% in 2022 (inflation driver)
    'revolving_yoy':[None,-4.68,0.49,1.02,2.92,2.91,3.57,6.03,5.00,3.98,-7.76,-1.13,14.35,12.04,6.21,-1.68],
})

# FDIC Bank Return on Assets (ROA) by State
# ROA = Net Income / Total Assets — measures how efficiently a bank uses its assets to generate profit
# Industry benchmark: healthy banks typically run 1.0%–1.5% ROA
# Data reflects FDIC-insured institutions HEADQUARTERED in each state (not branch locations)
roa_df = pd.DataFrame([
    ('New Mexico',14,1.7689), ('Arkansas',40,1.6533), ('Utah',5,1.6002),
    ('Georgia',70,1.5338),    ('West Virginia',14,1.5158), ('Michigan',33,1.5130),
    ('Virginia',9,1.4768),    ('Missouri',104,1.4229), ('Idaho',3,1.4211),
    ('Alaska',3,1.4127),      ('Texas',142,1.4117),   ('Alabama',23,1.3908),
    ('Indiana',37,1.3891),    ('Kentucky',34,1.3885), ('Montana',20,1.3871),
    ('Tennessee',35,1.3812),  ('Nebraska',86,1.3371), ('Kansas',108,1.3341),
    ('Oklahoma',57,1.2665),   ('Minnesota',109,1.2100),('South Carolina',16,1.2077),
    ('Colorado',23,1.1894),   ('Ohio',31,1.1772),     ('Wisconsin',84,1.1352),
    ('Wyoming',7,1.1270),     ('Iowa',131,1.1126),    ('Mississippi',24,1.1125),
    ('Pennsylvania',13,1.1020),('Connecticut',18,1.0958),('South Dakota',25,1.0781),
    ('North Dakota',34,1.0414),('New Jersey',6,1.0383),('Hawaii',4,1.0344),
    ('North Carolina',7,1.0140),('California',16,0.9745),('Illinois',161,0.9695),
    ('Washington',2,0.9596),  ('Florida',16,0.9164),  ('Oregon',4,0.8891),
    ('Maine',15,0.8614),      ('New York',26,0.8465), ('Massachusetts',6,0.8297),
    ('Maryland',5,0.7695),    ('Rhode Island',2,0.7679),('Louisiana',48,0.7573),
    ('Vermont',5,0.6356),     ('Delaware',3,0.6068),  ('New Hampshire',9,0.5714),
    ('District Of Columbia',2,0.4572),
], columns=['state','banks','roa'])

# FDIC Bank Tier Distribution
# Banks are classified by total asset size — this is how regulators think about them
# Key insight: 6 mega banks hold 41.6% of all sector assets despite being 0.36% of institutions
tier_df = pd.DataFrame([
    ('Community\n(<$100M)',    250,  15.29),    # smallest banks — very local, community focused
    ('Mid-Size\n($100M–$1B)', 1107, 416.77),   # largest count — the backbone of U.S. banking
    ('Regional\n($1B–$10B)',  296,  825.16),   # mid-tier — significant regional players
    ('Large\n($10B–$100B)',   31,   885.19),   # large banks — major market presence
    ('Mega\n(>$100B)',        6,    1528.20),  # JPMorgan, BofA, Wells Fargo, Citi, etc.
], columns=['tier','banks','assets'])

# FDIC Unprofitable Banks by State
# Shows % of a state's headquartered banks reporting negative net income
# IMPORTANT: States with few HQ banks have inflated percentages (small denominator effect)
# Example: NY has 26 HQ banks — 2 unprofitable = 7.69%, but absolute count is low
unprof_df = pd.DataFrame([
    ('New York',26,2,7.69),      ('West Virginia',14,1,7.14),
    ('Florida',16,1,6.25),       ('California',16,1,6.25),
    ('Connecticut',18,1,5.56),   ('Oklahoma',57,3,5.26),
    ('Arkansas',40,2,5.00),      ('Alabama',23,1,4.35),
    ('Colorado',23,1,4.35),      ('Georgia',70,3,4.29),
], columns=['state','total','unprofitable','pct'])

# Capstone Risk Signal (2016–2025)
# Risk classification based on YoY consumer debt growth rate:
#   HIGH     = ≥7%  (only 2022 qualifies at 8.37%)
#   MODERATE = 4–7% (most years fall here)
#   LOW      = <4%  (2020 COVID anomaly, 2024–2025 slowdown)
# NOTE: FDIC bank stress data was only available for 2025 in this dataset.
# Risk signals for 2016–2024 reflect consumer debt growth rate alone.
capstone_df = pd.DataFrame([
    (2016,3.34,'MODERATE'), (2017,5.92,'MODERATE'), (2018,4.97,'MODERATE'),
    (2019,4.73,'MODERATE'), (2020,0.67,'LOW'),       (2021,5.07,'MODERATE'),
    (2022,8.37,'HIGH'),     (2023,5.02,'MODERATE'),  (2024,1.78,'LOW'),
    (2025,0.31,'LOW'),
], columns=['year','growth','signal'])


# ── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def style_ax(ax, title='', xlabel='', ylabel='', spines=True):
    """
    Apply consistent dark card styling to a matplotlib axis.
    Called at the start of every chart to avoid repeating the same style code.
    Parameters:
        ax     — the matplotlib axis object to style
        title  — chart title text (displayed top-left)
        xlabel — x-axis label (optional)
        ylabel — y-axis label (optional)
        spines — whether to style the border around the chart (default True)
    """
    ax.set_facecolor(CARD)
    ax.set_title(title, color=WHITE, fontsize=10, fontweight='bold',
                 pad=12, loc='left')
    if xlabel: ax.set_xlabel(xlabel, color=MUTED2, fontsize=8, labelpad=6)
    if ylabel: ax.set_ylabel(ylabel, color=MUTED2, fontsize=8, labelpad=6)
    if spines:
        for spine in ax.spines.values():
            spine.set_edgecolor('#1e293b')
            spine.set_linewidth(0.8)
    ax.tick_params(colors=MUTED, which='both', length=3)


def trillions(x, pos):
    """
    Custom tick formatter for y-axes showing dollar amounts in trillions.
    Example: 2511 (billions) → '$2.5T'
    Used on the main debt line chart y-axis.
    """
    return f'${x/1000:.1f}T'


def pct_fmt(x, pos):
    """
    Custom tick formatter for percentage axes.
    Example: 6.55 → '6.6%'
    Used on YoY growth charts and ROA charts.
    """
    return f'{x:.1f}%'


def billions(x, pos):
    """
    Custom tick formatter for y-axes showing dollar amounts in billions.
    Example: 1038 → '$1038B'
    Used on the revolving credit deep-dive chart.
    """
    return f'${x:.0f}B'


# ── FIGURE & LAYOUT SETUP ─────────────────────────────────────────────────────
# Create the master figure — 22 inches wide by 28 inches tall at 180 DPI
# This gives us a large canvas for 11 charts without crowding
fig = plt.figure(figsize=(22, 28), facecolor=BG)
fig.patch.set_facecolor(BG)

# GridSpec divides the figure into a 5-row × 3-column grid
# Each chart occupies one or more cells in this grid
# hspace = vertical spacing between rows
# wspace = horizontal spacing between columns
# top/bottom/left/right = outer margins (as fraction of figure size)
gs = gridspec.GridSpec(
    5, 3,
    figure=fig,
    hspace=0.58,     # vertical gap between chart rows
    wspace=0.38,     # horizontal gap between chart columns
    top=0.88,        # top margin — leaves room for header and KPI strip
    bottom=0.04,     # bottom margin — leaves room for footer
    left=0.06,       # left margin
    right=0.97       # right margin
)


# ── HEADER ────────────────────────────────────────────────────────────────────
# fig.text() places text at absolute position on the figure
# Coordinates are 0.0–1.0 where (0,0) = bottom-left, (1,1) = top-right

# Dashboard title
fig.text(0.06, 0.960,
         'U.S. Financial Health Dashboard',
         fontsize=28, fontweight='bold', color=WHITE, va='top',
         fontfamily='DejaVu Sans')

# Subtitle showing data sources and date range
fig.text(0.06, 0.944,
         'FDIC Bank Performance Data  ×  Federal Reserve G.19 Consumer Credit Report  ·  2010–2025',
         fontsize=10, color=MUTED2, va='top')

# Analyst name and credentials — top right
fig.text(0.97, 0.960,
         'Natheneal Alamrew\nB.S.B.A. Management Information Systems\nChristian Brothers University · 2025',
         fontsize=8, color=MUTED, va='top', ha='right', linespacing=1.6)

# Horizontal rule separating header from KPI strip
fig.add_artist(plt.Line2D(
    [0.06, 0.97], [0.934, 0.934],   # x-coords and y-coords in figure fraction
    transform=fig.transFigure,
    color='#1e293b', linewidth=1.2
))

# ── KPI STRIP ─────────────────────────────────────────────────────────────────
# Five headline metrics displayed as cards across the top of the dashboard
# Each card has: a value, a label, and a colored bottom accent line
kpis = [
    ('$5.01T', 'Total Consumer Debt · 2025', GREEN),
    ('1,690',  'Active FDIC-Insured Banks',  BLUE),
    ('8.37%',  'Peak YoY Growth · 2022',     YELLOW),
    ('0.67%',  'COVID Low · 2020',           RED),
    ('2.84%',  'Unprofitable Banks · 2025',  PURPLE),
]

# Evenly spaced x positions for the 5 KPI cards
kpi_positions = [0.06, 0.25, 0.44, 0.63, 0.82]

for i, ((val, label, color), x) in enumerate(zip(kpis, kpi_positions)):

    # Draw the card background using FancyBboxPatch (rounded rectangle)
    rect = FancyBboxPatch(
        (x, 0.900), 0.175, 0.030,           # (x, y), width, height
        boxstyle="round,pad=0.004",          # rounded corners
        linewidth=0.8, edgecolor='#1e293b',
        facecolor='#0d1220',
        transform=fig.transFigure, zorder=1
    )
    fig.add_artist(rect)

    # Colored bottom accent line — color matches the category (green, blue, etc.)
    fig.add_artist(plt.Line2D(
        [x+0.003, x+0.172], [0.900, 0.900],
        transform=fig.transFigure,
        color=color, linewidth=2, zorder=2
    ))

    # Large KPI value text
    fig.text(x+0.006, 0.926, val,
             fontsize=14, fontweight='bold', color=WHITE,
             transform=fig.transFigure, va='top', zorder=3)

    # Smaller descriptive label below the value
    fig.text(x+0.006, 0.908, label,
             fontsize=7, color=MUTED2,
             transform=fig.transFigure, va='top', zorder=3)


# ── CHART 1: Consumer Debt Line Chart ─────────────────────────────────────────
# Occupies the first 2 columns of row 0 (top-left, spanning 2/3 width)
# Shows all 5 debt categories as separate lines from 2010 to 2025
ax1 = fig.add_subplot(gs[0, :2])
style_ax(ax1, 'Consumer Debt by Category, 2010–2025', ylabel='Outstanding ($)')

# Define each line: (dataframe column, legend label, color, line width, line style)
lines = [
    ('total',        'Total',        BLUE,   2.5, '-'),   # solid thick — most prominent
    ('nonrevolving', 'Nonrevolving', GREEN,  2.0, '-'),   # solid — second most important
    ('student',      'Student Loans',YELLOW, 1.8, '--'),  # dashed — subset of nonrevolving
    ('auto',         'Auto Loans',   RED,    1.5, '--'),  # dashed — subset of nonrevolving
    ('revolving',    'Revolving',    PURPLE, 1.5, ':'),   # dotted — credit cards
]

for col, label, color, lw, ls in lines:
    # Drop rows where this column is None (e.g., student loans missing 2025)
    data = debt_df[['year', col]].dropna()
    ax1.plot(data['year'], data[col],
             color=color, linewidth=lw, linestyle=ls,
             label=label, zorder=3)

    # Add a dollar value label at the end of each line for quick reading
    last = data.iloc[-1]
    ax1.annotate(f'${last[col]:.0f}B',
                 xy=(last['year'], last[col]),
                 xytext=(4, 0), textcoords='offset points',
                 color=color, fontsize=7, va='center')

# Format y-axis as trillions (e.g., $2.5T) using our custom formatter
ax1.yaxis.set_major_formatter(FuncFormatter(trillions))
ax1.set_xlim(2009.5, 2026.5)
ax1.set_xticks(range(2010, 2026, 2))  # show every other year to avoid crowding
ax1.legend(loc='upper left', ncol=5, framealpha=0.3,
           bbox_to_anchor=(0, 1.01), columnspacing=1.0)

# Arrow annotation pointing to the 2020 COVID dip in total debt
ax1.annotate('COVID\ndip',
             xy=(2020, 4103), xytext=(2018.2, 3600),
             color=MUTED2, fontsize=7,
             arrowprops=dict(arrowstyle='->', color=MUTED, lw=0.8),
             ha='center')


# ── CHART 2: YoY Growth Bar Chart ─────────────────────────────────────────────
# Occupies column 2 of row 0 (top-right)
# Shows annual % change in total consumer debt, color-coded by risk level
ax2 = fig.add_subplot(gs[0, 2])
style_ax(ax2, 'Year-over-Year\nGrowth Rate', ylabel='%')

# Drop 2010 since YoY is None (no prior year available)
yoy_data = debt_df.dropna(subset=['yoy'])

# Color each bar based on risk threshold:
# RED = high (≥7%), YELLOW = moderate (4–7%), PURPLE = low (≤1%), BLUE = normal
colors_yoy = [
    RED    if v >= 7 else
    YELLOW if v >= 4 else
    PURPLE if v <= 1 else
    BLUE
    for v in yoy_data['yoy']
]

bars = ax2.bar(yoy_data['year'], yoy_data['yoy'],
               color=colors_yoy, width=0.7, zorder=3, edgecolor='none')

# Add value labels on top of each bar
for bar, val in zip(bars, yoy_data['yoy']):
    ax2.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 0.1,
             f'{val}%', ha='center', va='bottom',
             color=WHITE, fontsize=6, fontweight='bold')

ax2.set_xticks(yoy_data['year'])
ax2.set_xticklabels(yoy_data['year'], rotation=45, ha='right', fontsize=7)
ax2.yaxis.set_major_formatter(FuncFormatter(pct_fmt))

# Manual legend using colored patch objects
legend_patches = [
    mpatches.Patch(color=RED,    label='High (≥7%)'),
    mpatches.Patch(color=YELLOW, label='Moderate (4–7%)'),
    mpatches.Patch(color=BLUE,   label='Normal (1–4%)'),
    mpatches.Patch(color=PURPLE, label='Low (<1%)'),
]
ax2.legend(handles=legend_patches, fontsize=6, loc='upper right',
           framealpha=0.3, ncol=2)


# ── CHART 3: Bank Tier Dual Axis Bar Chart ────────────────────────────────────
# Occupies column 0 of row 1
# Uses TWO y-axes: left = number of banks, right = total assets in $B
# This shows both count and concentration on the same chart
ax3 = fig.add_subplot(gs[1, 0])
style_ax(ax3, 'U.S. Banks by Asset Tier')

x = np.arange(len(tier_df))  # evenly spaced positions for bar groups
width = 0.38                  # width of each individual bar

# Left axis: number of banks (blue bars, shifted left)
bars1 = ax3.bar(x - width/2, tier_df['banks'], width,
                color=BLUE, alpha=0.85, label='# Banks', zorder=3)

# Create a second y-axis sharing the same x-axis
# twinx() mirrors the x-axis and adds an independent right y-axis
ax3_r = ax3.twinx()
ax3_r.set_facecolor(CARD)

# Right axis: total assets in $B (green bars, shifted right)
bars2 = ax3_r.bar(x + width/2, tier_df['assets'], width,
                  color=GREEN, alpha=0.75, label='Assets ($B)', zorder=3)
ax3_r.yaxis.set_major_formatter(FuncFormatter(billions))
ax3_r.tick_params(colors=MUTED, labelsize=7)
ax3_r.spines['right'].set_edgecolor('#1e293b')
ax3_r.set_ylabel('Total Assets ($B)', color=MUTED2, fontsize=7)

ax3.set_xticks(x)
ax3.set_xticklabels(tier_df['tier'], fontsize=6.5)
ax3.set_ylabel('Number of Banks', color=MUTED2, fontsize=7)

# Build a combined legend manually since two axes have separate legends by default
lines1 = mpatches.Patch(color=BLUE,  alpha=0.85, label='# Banks')
lines2 = mpatches.Patch(color=GREEN, alpha=0.75, label='Assets ($B)')
ax3.legend(handles=[lines1, lines2], fontsize=7, loc='upper right', framealpha=0.3)

# Key insight annotation below the chart
ax3.text(0.5, -0.30,
         '6 mega banks = 0.35% of institutions\nbut hold 42% of total sector assets',
         transform=ax3.transAxes, ha='center', fontsize=7,
         color=MUTED2, style='italic')


# ── CHART 4: Top 10 Bank ROA States ──────────────────────────────────────────
# Occupies column 1 of row 1
# Horizontal bar chart — easier to read state names than vertical bars
ax4 = fig.add_subplot(gs[1, 1])
style_ax(ax4, 'Top 10 States · Bank ROA %')

# roa_df is already sorted descending — take top 10 and reverse for bottom-to-top display
top10 = roa_df.head(10).sort_values('roa')

# Color bars by performance tier:
# GREEN = excellent (≥1.5%), BLUE = strong (≥1.2%), MUTED2 = benchmark range
bar_colors = [GREEN if r >= 1.5 else BLUE if r >= 1.2 else MUTED2
              for r in top10['roa']]

bars_h = ax4.barh(top10['state'], top10['roa'],
                  color=bar_colors, height=0.65, zorder=3)

# Add value labels and bank count at end of each bar
for bar, val, n in zip(bars_h, top10['roa'], top10['banks']):
    ax4.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
             f'{val:.4f}%  ({n} banks)',
             va='center', color=WHITE, fontsize=7)

ax4.set_xlim(0, 2.2)
ax4.xaxis.set_major_formatter(FuncFormatter(pct_fmt))

# Dashed reference line at 1.0% — the industry minimum benchmark
ax4.axvline(x=1.0, color=MUTED, linewidth=0.8, linestyle='--', alpha=0.5,
            label='1.0% benchmark')
ax4.legend(fontsize=7, framealpha=0.3)
ax4.grid(axis='x', alpha=0.4)
ax4.grid(axis='y', alpha=0)  # turn off horizontal gridlines for cleaner look


# ── CHART 5: Unprofitable Banks by State ─────────────────────────────────────
# Occupies column 2 of row 1
# Shows top 10 states by % of banks reporting negative net income
ax5 = fig.add_subplot(gs[1, 2])
style_ax(ax5, 'Highest % Unprofitable Banks\n(States with ≥10 banks)')

# Sort ascending so the highest % appears at the top of the horizontal chart
unprof_sorted = unprof_df.sort_values('pct')

# Color by severity: RED ≥ 7%, YELLOW ≥ 5%, BLUE = lower risk
bars_u = ax5.barh(unprof_sorted['state'], unprof_sorted['pct'],
                  color=[RED if p >= 7 else YELLOW if p >= 5 else BLUE
                         for p in unprof_sorted['pct']],
                  height=0.65, zorder=3)

# Label each bar with the exact % and raw counts (unprofitable/total)
for bar, row in zip(bars_u, unprof_sorted.itertuples()):
    ax5.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
             f'{row.pct:.2f}% ({row.unprofitable}/{row.total})',
             va='center', color=WHITE, fontsize=7)

ax5.set_xlim(0, 11)
ax5.xaxis.set_major_formatter(FuncFormatter(pct_fmt))
ax5.grid(axis='x', alpha=0.4)
ax5.grid(axis='y', alpha=0)

# Important caveat footnote — New York's high % is a small-denominator artifact
ax5.text(0.01, -0.18,
         '* NY has only 26 HQ banks. Small denominator inflates %.\n'
         '  Illinois (161 banks, 6 unprofitable) is a larger absolute risk.',
         transform=ax5.transAxes, fontsize=6.5, color=MUTED2, style='italic')


# ── CHART 6: Category YoY Comparison Line Chart ──────────────────────────────
# Occupies first 2 columns of row 2
# Shows YoY growth rate for each debt category as separate lines
# Key events are annotated with arrows to tell the story
ax6 = fig.add_subplot(gs[2, :2])
style_ax(ax6, 'YoY Growth by Debt Category, 2011–2025', ylabel='%')

# Each tuple: (column name, legend label, color, line width, line style)
cats = [
    ('yoy',           'Total',        BLUE,   2.5, '-'),
    ('revolving_yoy', 'Revolving',    PURPLE, 1.8, '--'),
    ('auto_yoy',      'Auto Loans',   RED,    1.5, '--'),
    ('student_yoy',   'Student Loans',YELLOW, 1.5, ':'),
]

for col, label, color, lw, ls in cats:
    data = debt_df[['year', col]].dropna()  # skip years where data is missing
    ax6.plot(data['year'], data[col],
             color=color, linewidth=lw, linestyle=ls, label=label, zorder=3,
             marker='o', markersize=3, markerfacecolor=color)  # dots at each data point

# Zero reference line — anything below means debt in that category is shrinking
ax6.axhline(y=0, color=MUTED, linewidth=0.8, linestyle='-', alpha=0.4)
ax6.yaxis.set_major_formatter(FuncFormatter(pct_fmt))
ax6.set_xlim(2010.5, 2025.5)
ax6.set_xticks(range(2011, 2026))
ax6.set_xticklabels(range(2011, 2026), rotation=45, ha='right', fontsize=7)
ax6.legend(loc='upper left', ncol=4, framealpha=0.3, bbox_to_anchor=(0, 1.02))

# Annotate key events with arrows to guide the reader's eye
ax6.annotate('Revolving surges\n+14.35% (inflation)',
             xy=(2022, 14.35), xytext=(2020.2, 17),
             color=PURPLE, fontsize=7,
             arrowprops=dict(arrowstyle='->', color=PURPLE, lw=0.8))

ax6.annotate('Auto drops\n-15.49%\n(supply chain)',
             xy=(2016, -15.49), xytext=(2013.5, -18),
             color=RED, fontsize=7,
             arrowprops=dict(arrowstyle='->', color=RED, lw=0.8))

ax6.annotate('COVID:\nRevolving -7.76%',
             xy=(2020, -7.76), xytext=(2017.8, -11),
             color=MUTED2, fontsize=7,
             arrowprops=dict(arrowstyle='->', color=MUTED, lw=0.8))


# ── CHART 7: Debt Composition Donut Chart ────────────────────────────────────
# Occupies column 2 of row 2
# Donut chart showing the split between revolving and nonrevolving as of 2025
ax7 = fig.add_subplot(gs[2, 2])
ax7.set_facecolor(CARD)
ax7.set_title('2025 Debt Composition', color=WHITE,
              fontsize=10, fontweight='bold', pad=12, loc='left')

# Only two slices: nonrevolving ($3,742B) and revolving ($1,267B)
# These are 2025 annual averages from the FRED CSV files
sizes    = [3742, 1267]
colors_d = [GREEN, PURPLE]

# width=0.45 creates the donut hole — smaller number = bigger hole
wedge_props = dict(width=0.45, edgecolor='#0a0e1a', linewidth=2)

wedges, texts = ax7.pie(sizes, labels=None, colors=colors_d,
                        wedgeprops=wedge_props, startangle=90)

# Center text inside the donut hole showing the total
ax7.text(0, 0.08, '$5.01T', ha='center', va='center',
         fontsize=14, fontweight='bold', color=WHITE)
ax7.text(0, -0.12, 'Total 2025', ha='center', va='center',
         fontsize=7, color=MUTED2)

# Legend below the donut with exact dollar values and percentages
legend_patches2 = [
    mpatches.Patch(color=GREEN,  label='Nonrevolving  $3,742B  (74.7%)'),
    mpatches.Patch(color=PURPLE, label='Revolving       $1,267B  (25.3%)'),
]
ax7.legend(handles=legend_patches2, loc='lower center',
           bbox_to_anchor=(0.5, -0.12), fontsize=7.5, framealpha=0.3)


# ── CHART 8: Cumulative Growth Since 2010 ────────────────────────────────────
# Occupies column 0 of row 3
# Horizontal bars showing total % growth per category from 2010 baseline
ax8 = fig.add_subplot(gs[3, 0])
style_ax(ax8, 'Cumulative Growth Since 2010')

# Each row: (category label, % growth, bar color)
# Growth is calculated from 2010 baseline to the latest available year
growth_data = pd.DataFrame([
    ('Nonrevolving\n(2010–2025)', 124.6, GREEN),   # largest growth
    ('Student Loans\n(2010–2024)', 112.7, YELLOW), # 2025 not reported
    ('Total Debt\n(2010–2025)',    99.5,  BLUE),    # overall benchmark
    ('Revolving\n(2010–2025)',     49.9,  PURPLE),  # slower growth
    ('Auto Loans\n(2010–2024)',    34.8,  RED),     # 2025 not final
], columns=['cat','pct','color'])

bars_g = ax8.barh(growth_data['cat'], growth_data['pct'],
                  color=growth_data['color'], height=0.55, alpha=0.85, zorder=3)

# Add percentage labels at the end of each bar
for bar, val in zip(bars_g, growth_data['pct']):
    ax8.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             f'+{val}%', va='center', color=WHITE, fontsize=8, fontweight='bold')

ax8.set_xlim(0, 155)
ax8.xaxis.set_major_formatter(FuncFormatter(pct_fmt))
ax8.grid(axis='x', alpha=0.4)
ax8.grid(axis='y', alpha=0)


# ── CHART 9: Capstone Risk Signal ────────────────────────────────────────────
# Occupies column 1 of row 3
# Bar chart showing the systemic risk classification by year
# Color = risk level (RED/YELLOW/GREEN), height = YoY growth rate
ax9 = fig.add_subplot(gs[3, 1])
style_ax(ax9, 'Systemic Risk Signal\n(YoY Debt Growth)', ylabel='%')

# Map each risk signal string to its display color
risk_colors = {'HIGH': RED, 'MODERATE': YELLOW, 'LOW': GREEN}
bar_colors_r = [risk_colors[s] for s in capstone_df['signal']]

bars_r = ax9.bar(capstone_df['year'], capstone_df['growth'],
                 color=bar_colors_r, width=0.65, zorder=3, alpha=0.85)

# Label each bar with its exact growth rate
for bar, val in zip(bars_r, capstone_df['growth']):
    ax9.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 0.08,
             f'{val}%', ha='center', va='bottom',
             color=WHITE, fontsize=6.5, fontweight='bold')

ax9.set_xticks(capstone_df['year'])
ax9.set_xticklabels(capstone_df['year'], rotation=45, ha='right', fontsize=7)
ax9.yaxis.set_major_formatter(FuncFormatter(pct_fmt))

# Manual color legend for the three risk levels
legend_r = [
    mpatches.Patch(color=RED,    label='HIGH (≥7%)'),
    mpatches.Patch(color=YELLOW, label='MODERATE (4–7%)'),
    mpatches.Patch(color=GREEN,  label='LOW (<4%)'),
]
ax9.legend(handles=legend_r, fontsize=7, framealpha=0.3, loc='upper right')

# Footnote clarifying data limitation — important for interview accuracy
ax9.text(0.5, -0.28,
         'Note: Bank stress data available for 2025 only.\n'
         'Risk signal 2016–2024 reflects debt growth rate alone.',
         transform=ax9.transAxes, ha='center', fontsize=6.5,
         color=MUTED2, style='italic')


# ── CHART 10: Bottom 10 Bank ROA States ──────────────────────────────────────
# Occupies column 2 of row 3
# Mirrors Chart 4 but for the lowest-performing states
ax10 = fig.add_subplot(gs[3, 2])
style_ax(ax10, 'Bottom 10 States · Bank ROA %')

# Take the last 10 rows (lowest ROA) and sort for display
bottom10 = roa_df.tail(10).sort_values('roa', ascending=False)

# Color code by how far below benchmark they are
# RED = critically low (<0.6%), YELLOW = weak (<0.8%), MUTED2 = below benchmark
bar_colors_b = [RED if r < 0.6 else YELLOW if r < 0.8 else MUTED2
                for r in bottom10['roa']]

bars_b = ax10.barh(bottom10['state'], bottom10['roa'],
                   color=bar_colors_b, height=0.65, zorder=3, alpha=0.85)

# Label each bar with ROA value and bank count in parentheses
for bar, val, n in zip(bars_b, bottom10['roa'], bottom10['banks']):
    ax10.text(bar.get_width() + 0.005,
              bar.get_y() + bar.get_height()/2,
              f'{val:.4f}%  ({n})',
              va='center', color=WHITE, fontsize=7)

ax10.set_xlim(0, 1.1)
ax10.xaxis.set_major_formatter(FuncFormatter(pct_fmt))

# Dashed reference line at 1.0% benchmark — states to the left are underperforming
ax10.axvline(x=1.0, color=MUTED, linewidth=0.8, linestyle='--',
             alpha=0.5, label='1.0% benchmark')
ax10.legend(fontsize=7, framealpha=0.3)
ax10.grid(axis='x', alpha=0.4)
ax10.grid(axis='y', alpha=0)


# ── CHART 11: Revolving Credit Deep Dive ─────────────────────────────────────
# Spans all 3 columns of row 4 (full width at the bottom)
# Focuses specifically on credit card debt to tell the COVID story
ax11 = fig.add_subplot(gs[4, :])
style_ax(ax11, 'Revolving Credit (Credit Cards) — COVID Collapse & Recovery, 2010–2025',
         ylabel='Outstanding ($B)')

rev_data = debt_df[['year','revolving']].dropna()

# Fill area under the line for visual emphasis
ax11.fill_between(rev_data['year'], rev_data['revolving'],
                  alpha=0.15, color=PURPLE)

# Main line with circle markers at each data point
ax11.plot(rev_data['year'], rev_data['revolving'],
          color=PURPLE, linewidth=2.5, zorder=3,
          marker='o', markersize=5, markerfacecolor=PURPLE,
          markeredgecolor='#0a0e1a', markeredgewidth=1.5)

# Shaded band highlighting the COVID period (2020–2021)
ax11.axvspan(2019.5, 2021.5, alpha=0.06, color=RED, label='COVID period')

# Annotate the four key inflection points on the revolving credit story
for year, val, label, dy in [
    (2019, 1038, 'Pre-COVID\npeak $1,038B', 60),    # peak before COVID
    (2020, 958,  'COVID low\n$958B\n(−7.76%)', -110), # largest single-year drop
    (2022, 1083, 'Recovery\n$1,083B', 60),           # back above pre-COVID levels
    (2025, 1267, 'New high\n$1,267B', 60),           # all-time high as of 2025
]:
    ax11.annotate(label,
                  xy=(year, val),
                  xytext=(year, val + dy),
                  ha='center', fontsize=7.5, color=PURPLE,
                  # only show arrow when annotation is below the data point
                  arrowprops=dict(arrowstyle='->', color=PURPLE, lw=0.8)
                  if dy < 0 else None)

ax11.set_xlim(2009.5, 2025.8)
ax11.set_xticks(range(2010, 2026))
ax11.yaxis.set_major_formatter(FuncFormatter(billions))
ax11.set_ylim(700, 1450)
ax11.legend(fontsize=8, framealpha=0.3)

# Insight box — key analytical takeaway from this chart
ax11.text(0.01, 0.92,
          'Key insight: Revolving credit fell $80B (−7.76%) in 2020 as stimulus payments enabled debt paydown.\n'
          'It surged 14.35% in 2022 as inflation eroded purchasing power, forcing households back to credit cards.',
          transform=ax11.transAxes, fontsize=8, color=MUTED2,
          style='italic', va='top',
          bbox=dict(boxstyle='round,pad=0.4', facecolor='#111827',
                    edgecolor='#1e293b', alpha=0.9))


# ── FOOTER ────────────────────────────────────────────────────────────────────
# Horizontal rule above footer
fig.add_artist(plt.Line2D(
    [0.06, 0.97], [0.028, 0.028],
    transform=fig.transFigure,
    color='#1e293b', linewidth=1.0
))

# Data source credit line
fig.text(0.06, 0.022,
         'Data Sources: FDIC Bank Financial Reports  ·  Federal Reserve G.19 Consumer Credit Release  '
         '·  Processed via PostgreSQL  ·  Visualized with Python (Matplotlib & Seaborn)',
         fontsize=7.5, color=MUTED, va='top')

# LinkedIn URL — right aligned
fig.text(0.97, 0.022,
         'linkedin.com/in/natheneal-alamrew-7b58a5258',
         fontsize=7.5, color=BLUE, va='top', ha='right')


# ── SAVE OUTPUT ───────────────────────────────────────────────────────────────
# Save the figure as a PNG at 180 DPI — high resolution for presentations/portfolios
# bbox_inches='tight' removes excess whitespace around the figure edges
# facecolor=BG applies the dark background to the saved file
output = '/mnt/user-data/outputs/Natheneal_Alamrew_Financial_Dashboard.png'
plt.savefig(output, dpi=180, bbox_inches='tight',
            facecolor=BG, edgecolor='none')
plt.close()  # release memory after saving
print(f"Saved: {output}")
