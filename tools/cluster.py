from typing import List, Dict, Tuple

import numpy as np
from sklearn.cluster import DBSCAN

from .html_layout_cosin import get_feature, similarity, __get_max_width_layer


def _compute_features(html_list: List[str]) -> List[Dict]:
    """从 HTML 源码列表中提取布局特征。

    Args:
        html_list: 多个 HTML 源码字符串列表。

    Returns:
        每个 HTML 对应的 feature 字典列表（get_feature 的返回值）。
    """

    features: List[Dict] = []
    for html in html_list:
        feat = get_feature(html)
        features.append(feat)
    return features


def _build_similarity_matrix(features: List[Dict]) -> np.ndarray:
    """基于 demo 中的相似度计算方式构建成对相似度矩阵。

    使用 __get_max_width_layer 计算每个页面的“有效层数”，
    两个页面之间的 similarity 使用它们层数平均值作为 layer_n。
    """

    n = len(features)
    if n == 0:
        return np.zeros((0, 0), dtype=np.float32)

    tags_list = [f.get("tags", {}) for f in features]
    # 对每个页面，计算其最大宽度所在层，用于估计合适的 layer_n
    layers = [__get_max_width_layer(tags) for tags in tags_list]

    sim_mat = np.zeros((n, n), dtype=np.float32)

    for i in range(n):
        sim_mat[i, i] = 1.0
        for j in range(i + 1, n):
            # 按 demo 中逻辑：两页的 layer_n 取平均再取整
            layer_n = int((layers[i] + layers[j]) / 2)
            sim = similarity(features[i], features[j], layer_n)
            sim_mat[i, j] = sim
            sim_mat[j, i] = sim

    # 数值稳定处理，裁剪在 [0,1] 范围内
    sim_mat = np.clip(sim_mat, 0.0, 1.0)
    return sim_mat


def cluster_html_layouts(
    html_list: List[str],
    eps: float = 0.05,
    min_samples: int = 2,
) -> Tuple[np.ndarray, np.ndarray, List[List[str]]]:
    """对多个 HTML 字符串按布局相似度进行 DBSCAN 聚类。

    Args:
        html_list: HTML 源码字符串列表。
        eps: DBSCAN 的 eps（基于 "距离" 的半径）。这里距离 = 1 - similarity，
             因此 eps 越小，要求相似度越高才会划为同一簇。
        min_samples: DBSCAN 中形成簇所需的最小样本数。

    Returns:
        labels: shape (n,)，每个 HTML 对应的簇编号，-1 表示噪声点。
        sim_mat: shape (n, n) 的相似度矩阵，方便调试或可视化。
        clusters: List[List[str]]，按照簇重组后的 HTML 字符串列表，每个子列表是一个簇。
    """

    if not html_list:
        return (
            np.array([], dtype=int),
            np.zeros((0, 0), dtype=np.float32),
            [],
        )

    # 1. 提取特征
    features = _compute_features(html_list)

    # 2. 计算相似度矩阵（基于 demo 中的 similarity 调用逻辑）
    sim_mat = _build_similarity_matrix(features)

    # 3. 将相似度转为“距离”矩阵供 DBSCAN 使用
    dist_mat = 1.0 - sim_mat

    # 4. 进行 DBSCAN 聚类
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    labels = clustering.fit_predict(dist_mat)

    # 5. 按簇重组成 HTML 字符串的 list[list]
    clusters: List[List[str]] = []
    unique_labels = sorted(set(labels) - {-1})  # 去掉噪声点 -1
    for lbl in unique_labels:
        cluster_htmls = [html for html, l in zip(html_list, labels) if l == lbl]
        clusters.append(cluster_htmls)

    return labels, sim_mat, clusters

