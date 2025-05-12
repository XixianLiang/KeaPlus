import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from matplotlib.ticker import MaxNLocator
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import platform
import matplotlib.font_manager as fm


def setup_fonts():
    """设置全局字体"""
    system = platform.system()

    # 尝试使用更专业的字体
    if system == 'Windows':
        plt.rcParams['font.family'] = 'Segoe UI'
    elif system == 'Darwin':  # macOS
        plt.rcParams['font.family'] = 'Helvetica Neue'
    else:  # Linux
        plt.rcParams['font.family'] = 'DejaVu Sans'

    # 增大默认字体大小以提高可读性
    plt.rcParams['font.size'] = 11

    # 设置轴标签和标题的字体粗细
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['axes.labelweight'] = 'medium'


def parse_coverage_file(file_path):
    """解析覆盖率文件，提取时间戳和覆盖率值"""
    timestamps = []
    coverages = []
    event_counts = []

    pattern = r'\[Fastbot\]\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\].*Coverage: (\d+\.\d+)%'

    with open(file_path, 'r') as file:
        for i, line in enumerate(file):
            match = re.search(pattern, line)
            if match:
                timestamp_str = match.group(1)
                coverage_str = match.group(2)

                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                coverage = float(coverage_str)
                event_count = (i + 1) * 25

                timestamps.append(timestamp)
                coverages.append(coverage)
                event_counts.append(event_count)

    return timestamps, coverages, event_counts


def create_enhanced_chart(timestamps, coverages, event_counts):
    """创建增强的图表"""
    # 设置风格
    plt.style.use('seaborn-v0_8-darkgrid')
    setup_fonts()

    # 创建图形和子图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), dpi=100)
    fig.subplots_adjust(hspace=0.3)

    # 设置图表背景
    fig.patch.set_facecolor('#f8f9fa')
    ax1.set_facecolor('#f1f3f6')
    ax2.set_facecolor('#f1f3f6')

    # 设置自定义颜色
    time_color = '#2c7fb8'
    event_color = '#e63946'
    annotation_color = '#2d3142'
    grid_color = '#ddd'

    # ===== 第一个图表：覆盖率随时间变化 =====

    # 创建渐变填充
    x = mdates.date2num(timestamps)
    points = np.array([x, coverages]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # 主绘图
    line1 = ax1.plot(timestamps, coverages, '-', color=time_color, linewidth=3,
                     marker='o', markersize=7, markerfacecolor='white',
                     markeredgewidth=2, markeredgecolor=time_color, zorder=5)

    # 添加渐变填充
    ax1.fill_between(timestamps, coverages, alpha=0.3, color=time_color)

    # 设置轴和标题
    ax1.set_title('Coverage Over Time', fontsize=16, pad=15)
    ax1.set_ylabel('Coverage (%)', fontsize=14, labelpad=10)

    # 确保y轴从0开始
    ax1.set_ylim(0, max(coverages) * 1.1)  # 留出一些空间

    # 格式化日期轴
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    # 设置网格
    ax1.grid(True, linestyle='--', linewidth=0.7, color=grid_color)

    # 标记最大值点
    max_cov = max(coverages)
    max_idx = coverages.index(max_cov)
    max_time = timestamps[max_idx]

    ax1.annotate(f'Max: {max_cov}%',
                 xy=(max_time, max_cov),
                 xytext=(0, 20),
                 textcoords='offset points',
                 color=annotation_color,
                 fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=annotation_color),
                 bbox=dict(boxstyle='round,pad=0.5', fc='#ffffff', ec='#cccccc', alpha=0.9),
                 ha='center')

    # ===== 第二个图表：覆盖率随事件变化 =====

    # 主绘图
    line2 = ax2.plot(event_counts, coverages, '-', color=event_color, linewidth=3,
                     marker='o', markersize=7, markerfacecolor='white',
                     markeredgewidth=2, markeredgecolor=event_color, zorder=5)

    # 添加渐变填充
    ax2.fill_between(event_counts, coverages, alpha=0.3, color=event_color)

    # 设置轴和标题
    ax2.set_title('Coverage by Event Count', fontsize=16, pad=15)
    ax2.set_xlabel('Event Count', fontsize=14, labelpad=10)
    ax2.set_ylabel('Coverage (%)', fontsize=14, labelpad=10)

    # 确保y轴从0开始，x轴从0开始
    ax2.set_ylim(0, max(coverages) * 1.1)
    ax2.set_xlim(0, max(event_counts) * 1.05)  # 添加一些边距

    # 设置x轴刻度
    ax2.xaxis.set_major_locator(MaxNLocator(integer=True))

    # 设置网格
    ax2.grid(True, linestyle='--', linewidth=0.7, color=grid_color)

    # 找出覆盖率停止增长的点
    stagnation_point = None
    for i in range(1, len(coverages)):
        if coverages[i] == coverages[i - 1]:
            stagnation_point = i - 1
            break

    if stagnation_point is not None:
        stag_event = event_counts[stagnation_point]
        stag_cov = coverages[stagnation_point]

        # 添加停滞点注释
        ax2.annotate(f'Stagnation: {stag_cov}%',
                     xy=(stag_event, stag_cov),
                     xytext=(20, 20),
                     textcoords='offset points',
                     color=annotation_color,
                     fontweight='bold',
                     arrowprops=dict(arrowstyle='->', color=annotation_color),
                     bbox=dict(boxstyle='round,pad=0.5', fc='#ffffff', ec='#cccccc', alpha=0.9))

        # 添加垂直线标记停滞点
        ax2.axvline(x=stag_event, color='#666666', linestyle='--', linewidth=1.5, alpha=0.7)

        # 添加分区域标记（有效测试区和停滞区）
        ax2.axvspan(0, stag_event, alpha=0.15, color='green', label='Effective Testing Zone')
        # 覆盖率停滞区域
        ax2.axvspan(stag_event, max(event_counts), alpha=0.15, color='gray', label='Saturation Zone')

        # 添加图例
        ax2.legend(loc='lower right', frameon=True, framealpha=0.9)

    # 添加标注点，减少标注以避免拥挤
    for i, (event, cov) in enumerate(zip(event_counts, coverages)):
        if i % 3 == 0 or i == len(event_counts) - 1:
            ax2.annotate(f'{event}',
                         xy=(event, cov),
                         xytext=(0, -15),
                         textcoords='offset points',
                         ha='center',
                         fontsize=8,
                         bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#cccccc', alpha=0.7))

    # 添加分析数据表格
    avg_increase = np.mean([coverages[i] - coverages[i - 1] for i in
                            range(1, stagnation_point + 1 if stagnation_point else len(coverages))])
    textstr = '\n'.join((
        f'Maximum Coverage: {max(coverages):.2f}%',
        f'Events to Max: {event_counts[max_idx]}',
        f'Avg. Increase: {avg_increase:.2f}% per step',
        f'Growth Stops: After {stag_event if stagnation_point is not None else "N/A"} events'
    ))

    props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8)
    ax2.text(0.02, 0.98, textstr, transform=ax2.transAxes, fontsize=9,
             verticalalignment='top', bbox=props)

    # 添加水印
    fig.text(0.5, 0.01, 'FastBot Coverage Analysis',
             ha='center', color='gray', alpha=0.5, fontsize=10)

    # 调整布局
    plt.tight_layout(rect=[0, 0.02, 1, 0.98])  # 留出水印空间

    # 保存高质量图表
    plt.savefig('coverage_chart_enhanced.png', dpi=300, bbox_inches='tight')

    return fig


def analyze_coverage_trend(coverages, event_counts):
    """分析覆盖率趋势并返回统计信息"""
    max_coverage = max(coverages)
    max_coverage_event = event_counts[coverages.index(max_coverage)]

    # 计算覆盖率增长率
    coverage_increases = []
    for i in range(1, len(coverages)):
        increase = coverages[i] - coverages[i - 1]
        events_diff = event_counts[i] - event_counts[i - 1]
        increase_rate = increase / events_diff * 100 if events_diff != 0 else 0
        coverage_increases.append(increase_rate)

    avg_increase_rate = np.mean(coverage_increases) if coverage_increases else 0

    # 找出覆盖率停止增长的点
    stagnation_point = None
    for i in range(1, len(coverages)):
        if coverages[i] == coverages[i - 1]:
            stagnation_point = i
            break

    return {
        "max_coverage": max_coverage,
        "max_coverage_event": max_coverage_event,
        "avg_increase_rate": avg_increase_rate,
        "stagnation_point": stagnation_point
    }


def main():
    """主函数"""
    coverage_file = "../covs_res.txt"

    try:
        timestamps, coverages, event_counts = parse_coverage_file(coverage_file)

        if not timestamps:
            print("No valid coverage data found. Please check the file format.")
            return

        # 分析覆盖率趋势
        trend_analysis = analyze_coverage_trend(coverages, event_counts)

        # 打印分析结果
        print("\nCoverage Analysis Results:")
        print(
            f"Maximum Coverage: {trend_analysis['max_coverage']}% (Event Count: {trend_analysis['max_coverage_event']})")
        print(f"Average Growth Rate: {trend_analysis['avg_increase_rate']:.4f}% per 25 events")

        if trend_analysis['stagnation_point'] is not None:
            stag_idx = trend_analysis['stagnation_point']
            print(f"Coverage stopped growing after {event_counts[stag_idx - 1]} events")

        # 创建增强的图表
        fig = create_enhanced_chart(timestamps, coverages, event_counts)
        plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()