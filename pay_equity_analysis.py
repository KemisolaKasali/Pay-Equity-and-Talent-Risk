"""Analyze BananaByte employee compensation and save five charts."""

# ============================================================================
# SECTION 1: IMPORTS AND CONFIGURATION
# ============================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from pathlib import Path
warnings.filterwarnings('ignore')

# Configuration
pd.set_option('display.float_format', '{:,.2f}'.format)
plt.style.use('seaborn-v0_8-whitegrid') if 'seaborn-v0_8-whitegrid' in plt.style.available else None

# Color palettes
GENDER_COLORS = {'Male': '#1f77b4', 'Female': '#e377c2'}
LEVEL_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
MARKET_COLORS = {'Below': '#d62728', 'At Market': '#2ca02c', 'Above': '#1f77b4'}

# ============================================================================
# SECTION 2: DATA LOADING AND PREPARATION
# ============================================================================
class PayEquityAnalysis:
    """Run the compensation analyses and save their charts."""

    def __init__(self, file_path, output_dir="reports"):
        self.file_path = Path(file_path)
        self.output_dir = Path(output_dir)
        self.df = None
        self.results = {}

    def load_data(self):
        # """""Load data from CSV file"""""
        df = pd.read_csv(self.file_path)
    
        # Convert performance to numeric
        df['Perf'] = pd.to_numeric(df['Perf'], errors='coerce')
    
        # Calculate compa-ratio
        df['Compa_Ratio'] = (df['Salary'] / df['Market_Median']) * 100
    
        # Calculate salary gap to market
        df['Salary_Gap'] = df['Market_Median'] - df['Salary']
    
        print(f"Loaded {len(df)} employee records")
        print(f"Columns: {list(df.columns)}")
    
        return df

    def prepare_analysis_data(self, df):
        # """""Prepare data for analysis"""""
        # Create performance tiers
        df['Perf_Tier'] = pd.cut(df['Perf'], 
                                  bins=[0, 2, 3.5, 5], 
                                  labels=['Low (1-2)', 'Medium (3-3.5)', 'High (4-5)'])
    
        # Create market position categories
        conditions = [
            df['Compa_Ratio'] < 80,
            (df['Compa_Ratio'] >= 80) & (df['Compa_Ratio'] < 95),
            (df['Compa_Ratio'] >= 95) & (df['Compa_Ratio'] <= 105),
            df['Compa_Ratio'] > 105
        ]
        choices = ['Significantly Underpaid (<80%)', 'Underpaid (80-95%)', 
                   'At Market (95-105%)', 'Above Market (>105%)']
        df['Market_Position'] = np.select(conditions, choices, default='Unknown')
    
        return df

    # ============================================================================
    # SECTION 3: GENDER PAY GAP ANALYSIS
    # ============================================================================
    def analyze_gender_pay_gap(self, df):
        '''Comprehensive gender pay gap analysis'''
        results = {}
    
        # Overall statistics
        male_df = df[df['Gender'] == 'Male']
        female_df = df[df['Gender'] == 'Female']
    
        male_avg = male_df['Salary'].mean()
        female_avg = female_df['Salary'].mean()
        overall_gap = ((male_avg - female_avg) / female_avg) * 100
    
        results['overall_gap'] = overall_gap
        results['male_count'] = len(male_df)
        results['female_count'] = len(female_df)
    
        # By Job Level
        level_order = ['Entry-Level', 'Mid-Level', 'Senior-Level', 'Management-Level', 'Executive-Level']
        results['by_level'] = {}
    
        for level in level_order:
            level_df = df[df['Job_Level'] == level]
            m = level_df[level_df['Gender'] == 'Male']['Salary'].mean()
            f = level_df[level_df['Gender'] == 'Female']['Salary'].mean()
            if pd.notna(m) and pd.notna(f) and f > 0:
                gap = ((m - f) / f) * 100
                results['by_level'][level] = gap
    
        # By Job Family
        results['by_family'] = {}
        family_gaps = []
        for family in df['Job_Family'].unique():
            family_df = df[df['Job_Family'] == family]
            m = family_df[family_df['Gender'] == 'Male']['Salary'].mean()
            f = family_df[family_df['Gender'] == 'Female']['Salary'].mean()
            if pd.notna(m) and pd.notna(f) and f > 0:
                gap = ((m - f) / f) * 100
                family_gaps.append((family, gap, len(family_df)))
    
        family_gaps.sort(key=lambda x: abs(x[1]), reverse=True)
        for family, gap, count in family_gaps[:5]:
            results['by_family'][family] = gap
    
        return results

    def plot_gender_analysis(self, df, results, save_path=None):
        '''Create visualizations for gender pay gap analysis'''
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Gender Pay Gap Analysis', fontsize=14, fontweight='bold')
    
        # 1. Salary Distribution by Gender
        ax1 = axes[0, 0]
        male_salaries = df[df['Gender'] == 'Male']['Salary']
        female_salaries = df[df['Gender'] == 'Female']['Salary']
        ax1.hist([male_salaries, female_salaries], bins=50, label=['Male', 'Female'],
                 color=[GENDER_COLORS['Male'], GENDER_COLORS['Female']], alpha=0.7)
        ax1.set_title('Salary Distribution by Gender')
        ax1.legend()
    
        # 2. Pay Gap by Job Level
        ax2 = axes[0, 1]
        levels = list(results['by_level'].keys())
        gaps = list(results['by_level'].values())
        colors = ['#d62728' if g > 0 else '#2ca02c' for g in gaps]
        ax2.barh(levels, gaps, color=colors, alpha=0.8)
        ax2.axvline(0, color='black')
        ax2.set_title('Pay Gap by Job Level')

        # 3. Largest pay gaps by job family
        ax3 = axes[1, 0]
        families = list(results['by_family'].keys())
        family_gaps = list(results['by_family'].values())
        family_colors = ['#d62728' if gap > 0 else '#2ca02c' for gap in family_gaps]
        ax3.barh(families, family_gaps, color=family_colors)
        ax3.axvline(0, color='black')
        ax3.set_title('Largest Pay Gaps by Job Family')

        # 4. Employee count by job level and gender
        ax4 = axes[1, 1]
        gender_counts = df.groupby(['Job_Level', 'Gender']).size().unstack(fill_value=0)
        gender_counts.plot(
            kind='bar',
            ax=ax4,
            color=[GENDER_COLORS.get(gender, '#999999') for gender in gender_counts.columns],
        )
        ax4.set_title('Employee Count by Level and Gender')
        ax4.set_ylabel('Employees')
        ax4.tick_params(axis='x', rotation=30)
        ax4.legend(title='Gender')
    
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return fig

    # ============================================================================
    # SECTION 4: COMPENSATION VS PERFORMANCE ANALYSIS
    # ============================================================================
    def analyze_compensation_performance(self, df):
        '''Analyze relationship between compensation and performance'''
        results = {}
        df_perf = df[df['Perf'].notna()].copy()
    
        # Average salary by performance rating
        results['by_rating'] = {}
        for rating in sorted(df_perf['Perf'].unique()):
            rating_df = df_perf[df_perf['Perf'] == rating]
            avg_sal = rating_df['Salary'].mean()
            avg_total = rating_df['Total_Compensation'].mean()
            results['by_rating'][rating] = {'salary': avg_sal, 'total_comp': avg_total, 'count': len(rating_df)}
    
        # Correlation
        results['salary_correlation'] = df_perf['Perf'].corr(df_perf['Salary'])
        results['total_comp_correlation'] = df_perf['Perf'].corr(df_perf['Total_Compensation'])
    
        # Gender analysis within high performance levels
        high_perf = df_perf[df_perf['Perf'] >= 4]
        male_high = high_perf[high_perf['Gender'] == 'Male']['Salary'].mean()
        female_high = high_perf[high_perf['Gender'] == 'Female']['Salary'].mean()
        results['high_performer_gap'] = ((male_high - female_high) / female_high) * 100
    
        return results

    def plot_performance_analysis(self, df, results, save_path=None):
        '''Create visualizations for compensation vs performance'''
        df_perf = df[df['Perf'].notna()].copy()
        rating_bands = ['1.x', '2.x', '3.x', '4.x', '5.x']
        df_perf['Perf_Band'] = pd.cut(
            df_perf['Perf'],
            bins=[1, 2, 3, 4, 5, 6],
            labels=rating_bands,
            right=False,
        )
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Compensation vs Performance Analysis', fontsize=14, fontweight='bold')
    
        # 1. Salary by rating band keeps the chart readable.
        ax1 = axes[0, 0]
        perf_data = [
            df_perf[df_perf['Perf_Band'] == band]['Salary'].values
            for band in rating_bands
        ]
        ax1.boxplot(perf_data)
        ax1.set_xticks(range(1, len(perf_data) + 1))
        ax1.set_xticklabels(rating_bands)
        ax1.set_title('Salary by Performance Rating Band')
    
        # 2. Average compensation by rating band
        ax2 = axes[0, 1]
        perf_avg = df_perf.groupby('Perf_Band', observed=False)[['Salary', 'Bonus_FY']].mean()
        x = np.arange(len(perf_avg))
        ax2.bar(x, perf_avg['Salary'], label='Base Salary', color='#1f77b4')
        ax2.bar(x, perf_avg['Bonus_FY'], bottom=perf_avg['Salary'], label='Bonus', color='#ff7f0e')
        ax2.set_xticks(x)
        ax2.set_xticklabels(rating_bands)
        ax2.set_title('Average Compensation by Rating Band')
        ax2.set_ylabel('Dollars')
        ax2.legend()
    
        # 3. Number of records in each rating band
        ax3 = axes[1, 0]
        rating_counts = df_perf['Perf_Band'].value_counts().reindex(rating_bands, fill_value=0)
        ax3.bar(rating_bands, rating_counts.values, color='#4c72b0')
        ax3.set_title('Employee Count by Rating Band')
        ax3.set_ylabel('Employees')
    
        # 4. High Performer Average Salary by Gender
        ax4 = axes[1, 1]
        high_perf = df_perf[df_perf['Perf'] >= 4]
        male_high = high_perf[high_perf['Gender'] == 'Male']['Salary'].mean()
        female_high = high_perf[high_perf['Gender'] == 'Female']['Salary'].mean()
        ax4.bar(['Male', 'Female'], [male_high, female_high], color=[GENDER_COLORS['Male'], GENDER_COLORS['Female']])
        ax4.set_title('High Performer Average Salary by Gender')
    
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return fig

    # ============================================================================
    # SECTION 5: MARKET COMPARISON ANALYSIS
    # ============================================================================
    def analyze_market_comparison(self, df):
        '''Analyze internal salaries vs market medians'''
        results = {}
    
        # Overall compa-ratio
        results['overall_compa'] = df['Compa_Ratio'].mean()
        results['median_compa'] = df['Compa_Ratio'].median()
    
        # Market position distribution
        results['distribution'] = {}
        conditions = [
            ('Significantly Underpaid (<80%)', df['Compa_Ratio'] < 80),
            ('Underpaid (80-95%)', (df['Compa_Ratio'] >= 80) & (df['Compa_Ratio'] < 95)),
            ('At Market (95-105%)', (df['Compa_Ratio'] >= 95) & (df['Compa_Ratio'] <= 105)),
            ('Above Market (>105%)', df['Compa_Ratio'] > 105)
        ]
        for label, mask in conditions:
            count = mask.sum()
            pct = count / len(df) * 100
            results['distribution'][label] = {'count': count, 'pct': pct}
    
        # By Job Level
        results['by_level'] = {}
        for level in ['Entry-Level', 'Mid-Level', 'Senior-Level', 'Management-Level', 'Executive-Level']:
            level_df = df[df['Job_Level'] == level]
            if len(level_df) > 0:
                level_compa = level_df['Compa_Ratio'].mean()
                level_gap = level_df['Salary_Gap'].sum()
                results['by_level'][level] = {'compa': level_compa, 'gap': level_gap}
    
        # Total salary gap
        results['total_gap'] = df['Salary_Gap'].sum()
    
        return results

    def plot_market_analysis(self, df, results, save_path=None):
        '''Create visualizations for market comparison'''
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Market Comparison Analysis', fontsize=14, fontweight='bold')
    
        # 1. Compa-ratio distribution
        ax1 = axes[0, 0]
        ax1.hist(df['Compa_Ratio'], bins=50, color='#1f77b4', alpha=0.7)
        ax1.axvline(100, color='green', linestyle='--', label='Market (100%)')
        ax1.axvline(df['Compa_Ratio'].mean(), color='red', linestyle='--', label='Mean')
        ax1.set_title('Compa-Ratio Distribution')
        ax1.legend()
    
        # 2. Market Position Pie Chart
        ax2 = axes[0, 1]
        labels = list(results['distribution'].keys())
        sizes = [results['distribution'][k]['count'] for k in labels]
        colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']
        ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
        ax2.set_title('Market Position Distribution')
    
        # 3. Compa-Ratio by Job Level
        ax3 = axes[1, 0]
        levels = list(results['by_level'].keys())
        compas = [results['by_level'][l]['compa'] for l in levels]
        colors = ['#d62728' if c < 95 else '#2ca02c' for c in compas]
        ax3.barh(levels, compas, color=colors)
        ax3.axvline(100, color='green', linestyle='--')
        ax3.set_title('Compa-Ratio by Job Level')
    
        # 4. Compa-Ratio by Job Family
        ax4 = axes[1, 1]
        family_compa = df.groupby('Job_Family')['Compa_Ratio'].mean().sort_values()
        family_compa.plot(kind='barh', ax=ax4, color='#1f77b4')
        ax4.axvline(100, color='green', linestyle='--')
        ax4.set_title('Compa-Ratio by Job Family')
    
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return fig

    # ============================================================================
    # SECTION 6: PAY EQUITY & PERFORMANCE IMPACT ANALYSIS
    # ============================================================================
    def analyze_pay_equity_impact(self, df):
        '''Analyze the impact of pay equity on performance'''
        results = {}
        df_perf = df[df['Perf'].notna()].copy()
    
        # Compa-ratio by performance level
        results['by_perf_level'] = {}
        for rating in sorted(df_perf['Perf'].unique()):
            rating_df = df_perf[df_perf['Perf'] == rating]
            results['by_perf_level'][rating] = rating_df['Compa_Ratio'].mean()
    
        # Correlation between pay equity and performance
        results['equity_performance_corr'] = df_perf['Compa_Ratio'].corr(df_perf['Perf'])
    
        # High performers at risk (high perf, low compa)
        high_perf_low_pay = df_perf[(df_perf['Perf'] >= 4) & (df_perf['Compa_Ratio'] < 80)]
        results['high_perf_at_risk'] = len(high_perf_low_pay)
    
        return results

    def plot_equity_impact(self, df, results, save_path=None):
        '''Create visualizations for pay equity impact'''
        df_perf = df[df['Perf'].notna()].copy()
        rating_bands = ['1.x', '2.x', '3.x', '4.x', '5.x']
        df_perf['Perf_Band'] = pd.cut(
            df_perf['Perf'],
            bins=[1, 2, 3, 4, 5, 6],
            labels=rating_bands,
            right=False,
        )
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Pay Equity & Performance Impact Analysis', fontsize=14, fontweight='bold')
    
        # 1. Compa-ratio by rating band
        ax1 = axes[0, 0]
        perf_compa = df_perf.groupby('Perf_Band', observed=False)['Compa_Ratio'].mean()
        ax1.bar(rating_bands, perf_compa.values, color='#1f77b4')
        ax1.axhline(100, color='green', linestyle='--', label='Market (100%)')
        ax1.set_title('Average Compa-Ratio by Rating Band')
        ax1.legend()
    
        # 2. Scatter: Compa-Ratio vs Performance with trend line
        ax2 = axes[0, 1]
        ax2.scatter(df_perf['Compa_Ratio'], df_perf['Perf'], alpha=0.3, s=10)
        z = np.polyfit(df_perf['Compa_Ratio'], df_perf['Perf'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df_perf['Compa_Ratio'].min(), df_perf['Compa_Ratio'].max(), 100)
        ax2.plot(x_line, p(x_line), 'r--', label='Trend')
        ax2.set_title('Compa-Ratio vs Performance')
        ax2.legend()
    
        # 3. Compa-ratio by rating band and gender
        ax3 = axes[1, 0]
        gender_perf_compa = df_perf.groupby(
            ['Perf_Band', 'Gender'], observed=False
        )['Compa_Ratio'].mean().unstack()
        gender_perf_compa.plot(kind='bar', ax=ax3, color=[GENDER_COLORS['Female'], GENDER_COLORS['Male']])
        ax3.axhline(100, color='green', linestyle='--')
        ax3.set_title('Compa-Ratio by Rating Band and Gender')
        ax3.set_xlabel('Performance rating band')
    
        # 4. Market position for employees with ratings of 4 or higher
        ax4 = axes[1, 1]
        high_perf = df_perf[df_perf['Perf'] >= 4]
        risk_counts = [
            (high_perf['Compa_Ratio'] < 80).sum(),
            ((high_perf['Compa_Ratio'] >= 80) & (high_perf['Compa_Ratio'] < 95)).sum(),
            (high_perf['Compa_Ratio'] >= 95).sum()
        ]
        ax4.pie(risk_counts, labels=['Below 80% of market', '80-95% of market', '95%+ of market'],
                colors=['#d62728', '#ff7f0e', '#2ca02c'], autopct='%1.1f%%')
        ax4.set_title('Employees with Ratings 4+ Market Position')
    
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return fig

    # ============================================================================
    # SECTION 7: SALARY ADJUSTMENT RECOMMENDATIONS
    # ============================================================================
    def analyze_salary_adjustments(self, df):
        '''Calculate salary adjustments needed'''
        results = {}
    
        # Identify underpaid employees
        df_underpaid = df[df['Compa_Ratio'] < 100].copy()
        df_underpaid['Adjustment_Needed'] = df_underpaid['Market_Median'] - df_underpaid['Salary']
        df_underpaid['Adjustment_Pct'] = ((df_underpaid['Market_Median'] - df_underpaid['Salary']) / df_underpaid['Salary']) * 100
    
        total_investment = df_underpaid['Adjustment_Needed'].sum()
        avg_adjustment = df_underpaid['Adjustment_Pct'].mean()
    
        results['total_investment'] = total_investment
        results['avg_adjustment_pct'] = avg_adjustment
        results['underpaid_count'] = len(df_underpaid)
    
        # By Job Level
        results['by_level'] = {}
        for level in ['Entry-Level', 'Mid-Level', 'Senior-Level', 'Management-Level', 'Executive-Level']:
            level_df = df_underpaid[df_underpaid['Job_Level'] == level]
            if len(level_df) > 0:
                results['by_level'][level] = {
                    'total': level_df['Adjustment_Needed'].sum(),
                    'count': len(level_df),
                    'avg_pct': level_df['Adjustment_Pct'].mean()
                }
    
        # Phased implementation scenarios
        critical = df_underpaid[df_underpaid['Compa_Ratio'] < 70]
        high_priority = df_underpaid[(df_underpaid['Compa_Ratio'] >= 70) & (df_underpaid['Compa_Ratio'] < 80)]
        medium = df_underpaid[(df_underpaid['Compa_Ratio'] >= 80) & (df_underpaid['Compa_Ratio'] < 90)]
        fine = df_underpaid[df_underpaid['Compa_Ratio'] >= 90]
    
        results['phases'] = {
            'critical': {'cost': critical['Adjustment_Needed'].sum(), 'count': len(critical)},
            'high': {'cost': high_priority['Adjustment_Needed'].sum(), 'count': len(high_priority)},
            'medium': {'cost': medium['Adjustment_Needed'].sum(), 'count': len(medium)},
            'fine': {'cost': fine['Adjustment_Needed'].sum(), 'count': len(fine)}
        }
    
        return results

    def plot_adjustment_analysis(self, df, results, save_path=None):
        '''Create visualizations for salary adjustments'''
        df_underpaid = df[df['Compa_Ratio'] < 100].copy()
        df_underpaid['Adjustment_Needed'] = df_underpaid['Market_Median'] - df_underpaid['Salary']
    
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Salary Adjustment Recommendations', fontsize=14, fontweight='bold')
    
        # 1. Investment by Job Level
        ax1 = axes[0, 0]
        levels = list(results['by_level'].keys())
        investments = [results['by_level'][l]['total'] for l in levels]
        ax1.barh(levels, [i/1e6 for i in investments], color='#d62728')
        ax1.set_xlabel('Investment Needed ($ Millions)')
        ax1.set_title('Investment Needed by Job Level')
    
        # 2. Phased Implementation
        ax2 = axes[0, 1]
        phases = ['Critical\n(<70%)', 'High\n(70-80%)', 'Medium\n(80-90%)', 'Fine-tune\n(90-100%)']
        phase_costs = [results['phases']['critical']['cost'], results['phases']['high']['cost'],
                       results['phases']['medium']['cost'], results['phases']['fine']['cost']]
        ax2.bar(phases, [c/1e6 for c in phase_costs], color=['#d62728', '#ff7f0e', '#f7dc6f', '#2ca02c'])
        ax2.set_ylabel('Investment ($ Millions)')
        ax2.set_title('Phased Implementation Cost')
    
        # 3. Distribution of Adjustment Percentages
        ax3 = axes[1, 0]
        adj_pcts = ((df_underpaid['Market_Median'] - df_underpaid['Salary']) / df_underpaid['Salary']) * 100
        ax3.hist(adj_pcts, bins=50, color='#1f77b4')
        ax3.axvline(adj_pcts.mean(), color='red', linestyle='--', label='Mean')
        ax3.set_title('Distribution of Required Adjustments')
        ax3.legend()
    
        # 4. Investment by Job Family (Top 10)
        ax4 = axes[1, 1]
        family_invest = df_underpaid.groupby('Job_Family')['Adjustment_Needed'].sum().sort_values().tail(10) / 1e6
        family_invest.plot(kind='barh', ax=ax4, color='#d62728')
        ax4.set_xlabel('Investment Needed ($ Millions)')
        ax4.set_title('Top 10 Job Families by Investment Needed')
    
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return fig

    # ============================================================================
    # SECTION 8: MAIN EXECUTION
    # ============================================================================
    def run(self):
        '''Run complete compensation analysis'''
        print('BANANABYTE PAY EQUITY & COMPENSATION ANALYSIS')
        print('Input File:', self.file_path)
    
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load and prepare data
        df = self.load_data()
        df = self.prepare_analysis_data(df)
    
        print(f'Total Employees: {len(df)}')
        print(f'Total Salary: ${df["Salary"].sum():,.2f}')
    
        # Run all analyses
        results = {}
    
        # Analysis 1: Gender Pay Gap
        results['gender'] = self.analyze_gender_pay_gap(df)
        self.plot_gender_analysis(df, results['gender'], self.output_dir / '1_gender_analysis.png')
    
        # Analysis 2: Compensation vs Performance
        results['performance'] = self.analyze_compensation_performance(df)
        self.plot_performance_analysis(df, results['performance'], self.output_dir / '2_performance_analysis.png')
    
        # Analysis 3: Market Comparison
        results['market'] = self.analyze_market_comparison(df)
        self.plot_market_analysis(df, results['market'], self.output_dir / '3_market_analysis.png')
    
        # Analysis 4: Pay Equity Impact
        results['equity'] = self.analyze_pay_equity_impact(df)
        self.plot_equity_impact(df, results['equity'], self.output_dir / '4_equity_impact.png')
    
        # Analysis 5: Salary Adjustments
        results['adjustments'] = self.analyze_salary_adjustments(df)
        self.plot_adjustment_analysis(df, results['adjustments'], self.output_dir / '5_adjustments.png')
    
        # Summary
        print('--- Key Findings ---')
        print(f'1. Overall Gender Pay Gap: {results["gender"]["overall_gap"]:.2f}%')
        print(f'2. Performance-Salary Correlation: {results["performance"]["salary_correlation"]:.4f}')
        print(f'3. Overall Compa-Ratio: {results["market"]["overall_compa"]:.1f}%')
        print(f'4. Total Market Gap: ${results["market"]["total_gap"]:,.2f}')
        print(f'5. Investment for 100% Parity: ${results["adjustments"]["total_investment"]:,.2f}')
    
        self.df = df
        self.results = results
        return df, results



if __name__ == '__main__':
    # Keep the original data file here; generated charts go into reports/.
    data_file = Path(__file__).parent / 'data' / 'raw' / 'BananaByte_Employee_Salary_090923 CleanedData_On_Python.csv'
    analysis = PayEquityAnalysis(data_file)
    analysis.run()
