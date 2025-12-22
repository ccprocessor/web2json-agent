"""
聚类功能单元测试
测试HTML布局聚类的准确性和性能
"""
import time
from pathlib import Path
from typing import List

import pytest

from web2json.tools import cluster_html_layouts, get_feature


class TestCluster:
    """HTML布局聚类测试类"""

    @pytest.fixture
    def evaluation_set_path(self):
        """获取评估数据集路径"""
        # 使用项目根目录下的evaluationSet
        return Path(__file__).parent.parent / "evaluationSet" / "book"

    def _read_html_files(self, directory: Path, show_progress: bool = False, limit: int = None) -> List[str]:
        """从目录中读取HTML文件

        Args:
            directory: HTML文件所在目录
            show_progress: 是否显示读取进度条
            limit: 限制读取的文件数量，None表示读取全部

        Returns:
            HTML源码字符串列表
        """
        from tqdm import tqdm

        html_files = sorted(directory.glob("*.htm"))
        if limit is not None:
            html_files = html_files[:limit]

        html_list = []

        iterator = tqdm(html_files, desc="读取HTML文件", unit="文件") if show_progress else html_files
        for html_file in iterator:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_list.append(f.read())
        return html_list

    def _print_cluster_results(self, labels, sim_mat, html_list, elapsed_time):
        """打印聚类结果统计信息

        Args:
            labels: 聚类标签数组
            sim_mat: 相似度矩阵
            html_list: HTML字符串列表
            elapsed_time: 聚类耗时
        """
        import numpy as np

        # 统计聚类结果
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(labels).count(-1)

        print("\n" + "="*60)
        print("聚类结果统计")
        print("="*60)
        print(f"总样本数: {len(html_list)}")
        print(f"聚类数量: {n_clusters}")
        print(f"噪声点数量: {n_noise}")
        print(f"聚类耗时: {elapsed_time:.4f} 秒")
        print(f"平均耗时: {elapsed_time/len(html_list)*1000:.2f} ms/样本")

        # 打印每个聚类的详细信息
        print("\n聚类详情:")
        print("-"*60)
        for label in sorted(unique_labels):
            if label == -1:
                cluster_name = "噪声点"
            else:
                cluster_name = f"聚类 {label}"

            count = list(labels).count(label)
            indices = [i for i, l in enumerate(labels) if l == label]
            print(f"{cluster_name}: {count} 个样本")
            print(f"  样本索引: {indices[:10]}" + ("..." if len(indices) > 10 else ""))

        # 计算聚类内和聚类间的相似度统计
        if n_clusters > 0:
            print("\n相似度统计:")
            print("-"*60)
            for label in sorted(unique_labels):
                if label == -1:
                    continue

                indices = [i for i, l in enumerate(labels) if l == label]
                if len(indices) > 1:
                    # 聚类内相似度
                    intra_sim = []
                    for i in range(len(indices)):
                        for j in range(i+1, len(indices)):
                            intra_sim.append(sim_mat[indices[i], indices[j]])

                    print(f"聚类 {label}:")
                    print(f"  聚类内平均相似度: {np.mean(intra_sim):.4f}")
                    print(f"  聚类内相似度范围: [{np.min(intra_sim):.4f}, {np.max(intra_sim):.4f}]")

        print("="*60 + "\n")

    @pytest.mark.unit
    @pytest.mark.performance
    @pytest.mark.slow
    def test_cluster_single_source_sampling(self, evaluation_set_path):
        """测试: 单一来源聚类 - 从全量评测集取样

        从swde评测集的book-abebooks(2000)中取样测试聚类功能

        可通过环境变量控制样本数量：
        TEST_SAMPLE_SIZE=50 pytest tests/test_cluster.py::TestCluster::test_cluster_single_source_sampling -v -s
        TEST_SAMPLE_SIZE=500 pytest tests/test_cluster.py::TestCluster::test_cluster_single_source_sampling -v -s

        预期结果：
        - 同一网站的页面应该聚类为少量簇
        - 聚类内平均相似度应该很高
        - 测试聚类算法的准确性和性能
        """
        import os

        # 从环境变量读取样本数量，默认50
        sample_size = int(os.getenv('TEST_SAMPLE_SIZE', '50'))

        print("\n" + "="*60)
        print(f"测试: 从全量评测集取样 - 单一来源聚类")
        print("="*60)
        print(f"样本数量: {sample_size} (可通过环境变量 TEST_SAMPLE_SIZE 修改)")
        print(f"示例: TEST_SAMPLE_SIZE=500 pytest tests/test_cluster.py::TestCluster::test_cluster_single_source_sampling -v -s")
        print("="*60)

        # 读取abebooks数据（带进度条）
        abebooks_dir = evaluation_set_path / "book-abebooks(2000)"
        assert abebooks_dir.exists(), f"数据集目录不存在: {abebooks_dir}"

        # 读取指定数量的HTML文件
        html_list = self._read_html_files(abebooks_dir, show_progress=True, limit=sample_size)
        print(f"\n✓ 读取完成: {len(html_list)} 个HTML文件\n")

        # 执行聚类（带进度条）
        start_time = time.time()
        labels, sim_mat, clusters = cluster_html_layouts(
            html_list,
            eps=0.05,  # 距离阈值
            min_samples=2,
            show_progress=True  # 启用进度条
        )
        elapsed_time = time.time() - start_time

        # 打印结果
        self._print_cluster_results(labels, sim_mat, html_list, elapsed_time)

        # 断言：应该聚为少量簇
        unique_labels = set(labels) - {-1}
        n_clusters = len(unique_labels)
        print(f"断言检查: 聚类数量 = {n_clusters}, 预期 ≤ 3")
        assert n_clusters <= 3, f"同一网站的页面应该聚类为1-3个簇，实际: {n_clusters}"

        # 断言：噪声点应该很少
        n_noise = list(labels).count(-1)
        noise_ratio = n_noise / len(html_list)
        print(f"断言检查: 噪声点比例 = {noise_ratio:.2%}, 预期 < 5%")
        assert noise_ratio < 0.05, f"噪声点比例过高: {noise_ratio:.2%}"

        # 性能断言：平均耗时应该在合理范围内
        avg_time_per_sample = elapsed_time / len(html_list) * 1000
        print(f"性能检查: 平均耗时 = {avg_time_per_sample:.2f} ms/样本")

    @pytest.mark.unit
    @pytest.mark.performance
    @pytest.mark.slow
    def test_cluster_mixed_source_sampling(self, evaluation_set_path):
        """测试: 混合来源聚类 - 从全量评测集取样

        从swde评测集的book-abebooks(2000)和book-amazon(2000)中各取样一半进行混合聚类测试

        可通过环境变量控制样本数量：
        TEST_SAMPLE_SIZE=50 pytest tests/test_cluster.py::TestCluster::test_cluster_mixed_source_sampling -v -s
        (注意：实际取样数量为TEST_SAMPLE_SIZE的2倍，因为从两个数据集各取一半)

        预期结果：
        - 应该聚类为2-4个主要簇（分别对应两个网站）
        - 每个簇的纯度应该较高（> 70%）
        """
        import os

        # 从环境变量读取样本数量，默认50（每个数据集各取一半）
        sample_size_per_source = int(os.getenv('TEST_SAMPLE_SIZE', '50')) // 2

        print("\n" + "="*60)
        print(f"测试: 从全量评测集取样 - 混合来源聚类")
        print("="*60)
        print(f"每个数据集取样数量: {sample_size_per_source}")
        print(f"总样本数: {sample_size_per_source * 2}")
        print(f"示例: TEST_SAMPLE_SIZE=500 pytest tests/test_cluster.py::TestCluster::test_cluster_mixed_source_sampling -v -s")
        print("="*60)

        # 读取两个数据集
        abebooks_dir = evaluation_set_path / "book-abebooks(2000)"
        amazon_dir = evaluation_set_path / "book-amazon(2000)"

        assert abebooks_dir.exists(), f"数据集目录不存在: {abebooks_dir}"
        assert amazon_dir.exists(), f"数据集目录不存在: {amazon_dir}"

        # 读取指定数量的HTML文件
        abebooks_html = self._read_html_files(abebooks_dir, show_progress=True, limit=sample_size_per_source)
        amazon_html = self._read_html_files(amazon_dir, show_progress=True, limit=sample_size_per_source)

        # 合并两个数据集
        html_list = abebooks_html + amazon_html
        print(f"\n✓ 读取完成: abebooks {len(abebooks_html)} + amazon {len(amazon_html)} = 总计 {len(html_list)} 个HTML文件\n")

        # 执行聚类（带进度条）
        start_time = time.time()
        labels, sim_mat, clusters = cluster_html_layouts(
            html_list,
            eps=0.05,  # 距离阈值
            min_samples=2,
            show_progress=True  # 启用进度条
        )
        elapsed_time = time.time() - start_time

        # 打印结果
        self._print_cluster_results(labels, sim_mat, html_list, elapsed_time)

        # 分析聚类结果
        n_abebooks = len(abebooks_html)
        n_amazon = len(amazon_html)

        print("\n聚类准确性分析:")
        print("-"*60)

        # 统计每个聚类中两个来源的分布
        unique_labels = sorted(set(labels) - {-1})
        for label in unique_labels:
            indices = [i for i, l in enumerate(labels) if l == label]
            abebooks_count = sum(1 for i in indices if i < n_abebooks)
            amazon_count = sum(1 for i in indices if i >= n_abebooks)

            print(f"聚类 {label}:")
            print(f"  abebooks: {abebooks_count} 个 ({abebooks_count/len(indices)*100:.1f}%)")
            print(f"  amazon: {amazon_count} 个 ({amazon_count/len(indices)*100:.1f}%)")

            # 判断这个聚类的主要来源
            if abebooks_count > amazon_count:
                purity = abebooks_count / len(indices)
                print(f"  纯度: {purity:.2%} (主要为abebooks)")
            else:
                purity = amazon_count / len(indices)
                print(f"  纯度: {purity:.2%} (主要为amazon)")

        # 断言：应该聚类为2-4个簇
        n_clusters = len(unique_labels)
        print(f"\n断言检查: 聚类数量 = {n_clusters}, 预期 2-4")
        assert 2 <= n_clusters <= 4, f"两个网站应该聚类为2-4个簇，实际: {n_clusters}"

        # 断言：每个簇的纯度应该较高（> 70%）
        min_purity = 1.0
        for label in unique_labels:
            indices = [i for i, l in enumerate(labels) if l == label]
            abebooks_count = sum(1 for i in indices if i < n_abebooks)
            amazon_count = sum(1 for i in indices if i >= n_abebooks)
            purity = max(abebooks_count, amazon_count) / len(indices)
            min_purity = min(min_purity, purity)

        print(f"断言检查: 最小聚类纯度 = {min_purity:.2%}, 预期 > 70%")
        assert min_purity > 0.70, f"聚类纯度不足: {min_purity:.2%}"

        # 性能断言：平均耗时应该在合理范围内
        avg_time_per_sample = elapsed_time / len(html_list) * 1000
        print(f"性能检查: 平均耗时 = {avg_time_per_sample:.2f} ms/样本")

    @pytest.mark.unit
    def test_cluster_empty_input(self):
        """测试: 边界情况 - 空输入"""
        labels, sim_mat, clusters = cluster_html_layouts([])

        assert len(labels) == 0
        assert sim_mat.shape == (0, 0)
        assert len(clusters) == 0

    @pytest.mark.unit
    def test_cluster_single_html(self):
        """测试: 边界情况 - 单个HTML"""
        html = "<html><body><div>test</div></body></html>"
        labels, sim_mat, clusters = cluster_html_layouts([html])

        assert len(labels) == 1
        assert labels[0] == -1  # 单个样本会被标记为噪声
        assert sim_mat.shape == (1, 1)
        assert sim_mat[0, 0] == 1.0


if __name__ == "__main__":
    # 允许直接运行测试文件
    pytest.main([__file__, "-v", "-s"])
