#!/usr/bin/env python3
"""简单 Demo：调用 html_layout_cosin 的 get_feature 和 similarity

用法示例：
    python demo_layout_cosin.py input_html/1.html input_html/2.html

参数：
    arg1: 第一个 HTML 文件路径
    arg2: 第二个 HTML 文件路径

脚本会：
    1. 读取两个 HTML 文件为字符串
    2. 调用 get_feature 提取 DOM 布局特征
    3. 调用 similarity 计算两个页面布局的余弦相似度
"""

from pathlib import Path

from tools.cluster import cluster_html_layouts


# 默认对比的两个 HTML 文件路径，如需修改，直接改这里即可
DEFAULT_HTML1 = Path("input_html/1.html")
DEFAULT_HTML2 = Path("input_html/2.html")


def read_html(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"HTML 文件不存在: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")

def main() -> None:
    # 如果提供了两个命令行参数，则用命令行；否则使用默认路径
    input_dir = Path("input_html")
    if not input_dir.exists():
        print(f"HTML 目录不存在: {input_dir}")
        return

    html_paths = sorted(input_dir.glob("*.html"))
    if not html_paths:
        print(f"HTML 目录中没有 .html 文件: {input_dir}")
        return

    print(f"在目录 {input_dir} 中找到 {len(html_paths)} 个 HTML 文件:")
    for p in html_paths:
        print(f"  - {p.name}")

    html_list = [read_html(p) for p in html_paths]

    labels, sim_mat, clusters = cluster_html_layouts(html_list)
    print(sim_mat)
    print("\n聚类结果（不含噪声 -1）:")
    unique_labels = sorted(set(labels))
    for lbl in unique_labels:
        if lbl == -1:
            continue
        files = [p.name for p, l in zip(html_paths, labels) if l == lbl]
        print(f"\n簇 {lbl}:")
        for name in files:
            print(f"  - {name}")

    noise_files = [p.name for p, l in zip(html_paths, labels) if l == -1]
    if noise_files:
        print("\n噪声（未归入任何簇，label = -1）:")
        for name in noise_files:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
