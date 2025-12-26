#!/usr/bin/env python3
"""
进度条功能演示脚本
使用少量数据快速演示聚类进度条效果
"""
from pathlib import Path
from web2json.tools import cluster_html_layouts

def demo_small_scale():
    """演示：使用50个样本的小规模测试"""
    print("\n" + "="*60)
    print("进度条功能演示 - 小规模测试 (50个样本)")
    print("="*60)

    # 读取数据
    data_dir = Path(__file__).parent.parent / "evaluationSet" / "book" / "book-abebooks(2000)"
    if not data_dir.exists():
        print(f"错误: 数据目录不存在 {data_dir}")
        return

    html_files = sorted(data_dir.glob("*.htm"))[:50]
    html_list = []

    print(f"\n正在读取 {len(html_files)} 个HTML文件...")
    for f in html_files:
        with open(f, 'r', encoding='utf-8') as file:
            html_list.append(file.read())

    # 执行聚类（带进度条）
    import time
    start_time = time.time()

    labels, sim_mat, clusters = cluster_html_layouts(
        html_list,
        eps=0.05,
        min_samples=2,
        show_progress=True  # 启用进度条
    )

    elapsed_time = time.time() - start_time

    # 打印结果
    print("\n" + "="*60)
    print("聚类结果")
    print("="*60)
    n_clusters = len(set(labels) - {-1})
    n_noise = list(labels).count(-1)

    print(f"总样本数: {len(html_list)}")
    print(f"聚类数量: {n_clusters}")
    print(f"噪声点数: {n_noise}")
    print(f"总耗时: {elapsed_time:.2f} 秒")
    print(f"平均耗时: {elapsed_time/len(html_list)*1000:.2f} ms/样本")
    print("="*60 + "\n")


def demo_medium_scale():
    """演示：使用200个样本的中等规模测试"""
    print("\n" + "="*60)
    print("进度条功能演示 - 中等规模测试 (200个样本)")
    print("="*60)

    # 读取数据
    data_dir = Path(__file__).parent.parent / "evaluationSet" / "book" / "book-abebooks(2000)"
    if not data_dir.exists():
        print(f"错误: 数据目录不存在 {data_dir}")
        return

    html_files = sorted(data_dir.glob("*.htm"))[:200]
    html_list = []

    print(f"\n正在读取 {len(html_files)} 个HTML文件...")
    for f in html_files:
        with open(f, 'r', encoding='utf-8') as file:
            html_list.append(file.read())

    # 执行聚类（带进度条）
    import time
    start_time = time.time()

    labels, sim_mat, clusters = cluster_html_layouts(
        html_list,
        eps=0.05,
        min_samples=2,
        show_progress=True  # 启用进度条
    )

    elapsed_time = time.time() - start_time

    # 打印结果
    print("\n" + "="*60)
    print("聚类结果")
    print("="*60)
    n_clusters = len(set(labels) - {-1})
    n_noise = list(labels).count(-1)

    print(f"总样本数: {len(html_list)}")
    print(f"聚类数量: {n_clusters}")
    print(f"噪声点数: {n_noise}")
    print(f"总耗时: {elapsed_time:.2f} 秒")
    print(f"平均耗时: {elapsed_time/len(html_list)*1000:.2f} ms/样本")
    print("="*60 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        scale = sys.argv[1]
        if scale == "medium":
            demo_medium_scale()
        elif scale == "small":
            demo_small_scale()
        else:
            print("用法: python demo_progress.py [small|medium]")
            print("  small  - 50个样本（快速演示）")
            print("  medium - 200个样本（中等规模）")
    else:
        print("选择测试规模:")
        print("1. small  - 50个样本（快速演示，约10秒）")
        print("2. medium - 200个样本（中等规模，约1-2分钟）")
        print()
        choice = input("请选择 (1/2): ").strip()

        if choice == "1":
            demo_small_scale()
        elif choice == "2":
            demo_medium_scale()
        else:
            print("无效选择")
