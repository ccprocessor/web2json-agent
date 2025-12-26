from typing import List, Dict, Tuple, Optional

import numpy as np
from sklearn.cluster import DBSCAN

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

from tqdm import tqdm

from .html_layout_cosin import (
    get_feature,
    similarity,
    __get_max_width_layer,
    __parse_valid_layer,
    fuse_features,
)


def _compute_features(html_list: List[str], show_progress: bool = False) -> List[Dict]:
    """从 HTML 源码列表中提取布局特征。

    Args:
        html_list: 多个 HTML 源码字符串列表。
        show_progress: 是否显示进度条。

    Returns:
        每个 HTML 对应的 feature 字典列表（get_feature 的返回值）。
    """

    features: List[Dict] = []
    iterator = tqdm(html_list, desc="提取特征", unit="页") if show_progress else html_list
    for html in iterator:
        feat = get_feature(html)
        features.append(feat)
    return features


def _build_similarity_matrix(features: List[Dict], show_progress: bool = False) -> np.ndarray:
    """基于 demo 中的相似度计算方式构建成对相似度矩阵。

    使用 __get_max_width_layer 计算每个页面的"有效层数"，
    两个页面之间的 similarity 使用它们层数平均值作为 layer_n。

    Args:
        features: 特征列表。
        show_progress: 是否显示进度条。
    """

    n = len(features)
    if n == 0:
        return np.zeros((0, 0), dtype=np.float32)

    tags_list = [f.get("tags", {}) for f in features]
    # 对每个页面，计算其最大宽度所在层，用于估计合适的 layer_n
    layers = [__get_max_width_layer(tags) for tags in tags_list]

    sim_mat = np.zeros((n, n), dtype=np.float32)

    # 计算需要执行的相似度计算次数（上三角矩阵）
    total_comparisons = n * (n - 1) // 2

    iterator = tqdm(range(n), desc="计算相似度矩阵", unit="行") if show_progress else range(n)
    for i in iterator:
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
    show_progress: bool = False,
) -> Tuple[np.ndarray, np.ndarray, List[List[str]]]:
    """对多个 HTML 字符串按布局相似度进行 DBSCAN 聚类。

    Args:
        html_list: HTML 源码字符串列表。
        eps: DBSCAN 的 eps（基于 "距离" 的半径）。这里距离 = 1 - similarity，
             因此 eps 越小，要求相似度越高才会划为同一簇。
        min_samples: DBSCAN 中形成簇所需的最小样本数。
        show_progress: 是否显示进度条（默认False）。

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
    if show_progress:
        print(f"\n{'='*60}")
        print(f"开始聚类分析: {len(html_list)} 个HTML页面")
        print(f"{'='*60}")

    features = _compute_features(html_list, show_progress=show_progress)

    # 2. 计算相似度矩阵（基于 demo 中的 similarity 调用逻辑）
    sim_mat = _build_similarity_matrix(features, show_progress=show_progress)

    # 3. 将相似度转为"距离"矩阵供 DBSCAN 使用
    if show_progress:
        print("执行DBSCAN聚类...")
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

    if show_progress:
        n_clusters = len(unique_labels)
        n_noise = list(labels).count(-1)
        print(f"✓ 聚类完成: {n_clusters} 个簇, {n_noise} 个噪声点")
        print(f"{'='*60}\n")

    return labels, sim_mat, clusters


def cluster_html_layouts_optimized(
    html_list: List[str],
    threshold: float = 0.95,
    k: float = 0.7,
    layer_n: int | None = None,
    metric: str = "cosine",
    min_samples: int = 3,
    strategy: str = "dbscan",
    use_knn_graph: bool = False,
    n_neighbors: int = 50,
) -> Tuple[np.ndarray, np.ndarray, List[List[str]]]:
    """基于融合特征向量的布局聚类（索引优化版）。

    使用 ``fuse_features`` 将 DOM 结构和属性融合为单一向量空间索引，
    再在该向量空间中执行可配置的 DBSCAN 聚类。

    Args:
        html_list: HTML 源码字符串列表。
        threshold: 相似度阈值，默认 0.95。
                   当 metric="cosine" 时，距离 eps = 1 - threshold。
        k: tags 和 attrs 权重占比，k 表示 tags 权重，(1-k) 为 attrs 权重。
        layer_n: DOM 树层级深度；为 None 时根据样本自动估计。
        metric: DBSCAN/近邻图 的距离度量方式，默认 "cosine"。
        min_samples: DBSCAN/近邻图 中形成簇所需的最小样本数。
        strategy: 聚类策略，目前仅支持 "dbscan"。
        use_knn_graph: 是否使用 k 近邻图近似 DBSCAN，适合大数据量时加速。
        n_neighbors: 构建近邻图时每个点保留的近邻个数，越大越接近精确 DBSCAN，
                     但计算/内存开销也越大。

    Returns:
        labels: shape (n, )，每个 HTML 对应的簇编号，-1 表示噪声点。
        sim_mat: shape (n, n) 的相似度矩阵（基于融合向量的 cosine 相似度）。
        clusters: List[List[str]]，按照簇重组后的 HTML 字符串列表，每个子列表是一个簇。
    """

    if not html_list:
        return (
            np.array([], dtype=int),
            np.zeros((0, 0), dtype=np.float32),
            [],
        )

    # 1. 提取布局特征
    features = _compute_features(html_list)

    # 2. 自动估计合适的层级（除非外部显式指定）
    if layer_n is None:
        layer_n = __parse_valid_layer(features)

    # 3. 计算融合特征向量，内部使用 DictVectorizer 构建统一特征空间索引
    fused_vecs = fuse_features(features, layer_n=layer_n, k=k)

    # 3.1 基于融合向量计算 cosine 相似度矩阵（用于返回和部分聚类策略）
    # 数值误差可能导致相似度略超出 [-1, 1]，这里做一次裁剪
    
    sim_mat = None

    # 4. 聚类策略：目前仅支持 DBSCAN 及其基于 kNN 图的近似版本
    if strategy.lower() != "dbscan":
        raise ValueError(f"Unsupported clustering strategy: {strategy}")

    if metric == "cosine":
        # cosine 距离 = 1 - cosine 相似度
        eps = 1.0 - float(threshold)
    else:
        # 非 cosine 度量时，直接将 threshold 视为距离阈值
        eps = float(threshold)

    if use_knn_graph:
        # 使用 k 近邻图近似 DBSCAN，适合大数据量场景
        labels = _approximate_dbscan_with_knn(
            fused_vecs,
            eps=eps,
            min_samples=min_samples,
            metric=metric,
            n_neighbors=n_neighbors,
        )
    else:
        # 使用预先计算好的相似度矩阵，转为距离矩阵供 DBSCAN 使用
        sim_mat = cosine_similarity(fused_vecs)
        # 数值误差可能导致相似度略超出 [-1, 1]，这里做一次裁剪
        # sim_mat = np.clip(sim_mat, -1.0, 1.0)
        # 自己和自己固定视为完全相似，避免受浮点误差影响
        np.fill_diagonal(sim_mat, 1.0)

        dist_mat = 1.0 - sim_mat
        # 数值误差可能导致极小的负值，这里保证距离非负
        dist_mat = np.clip(dist_mat, 0.0, None)
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
        labels = clustering.fit_predict(dist_mat)


    # 5. 按簇重组成 HTML 字符串列表
    clusters: List[List[str]] = []
    unique_labels = sorted(set(labels) - {-1})  # 去掉噪声点 -1
    for lbl in unique_labels:
        cluster_htmls = [html for html, l in zip(html_list, labels) if l == lbl]
        clusters.append(cluster_htmls)

    return labels, sim_mat, clusters


def _approximate_dbscan_with_knn(
    X: np.ndarray,
    eps: float,
    min_samples: int,
    metric: str,
    n_neighbors: int,
) -> np.ndarray:
    """基于 k 近邻图近似 DBSCAN 的聚类实现。

    只在每个点的前 n_neighbors 个近邻中查找 eps 范围内的点，
    用并查集对这些“近邻边”做连通分量划分，并标记包含核心点的连通分量为簇。

    这样可以避免全量 O(n^2) 距离计算，更适合大数据量场景，
    但属于近似聚类：如果某些邻居不在前 n_neighbors 内，可能被忽略。
    """

    n_samples = X.shape[0]
    if n_samples == 0:
        return np.array([], dtype=int)

    n_neighbors = int(max(1, min(n_neighbors, n_samples)))

    # 使用 NearestNeighbors 构建近邻索引
    nn = NearestNeighbors(n_neighbors=n_neighbors, metric=metric)
    nn.fit(X)
    distances, indices = nn.kneighbors(X)

    # 并查集结构
    parent = list(range(n_samples))
    rank = [0] * n_samples
    neighbor_count = [0] * n_samples

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if rank[ra] < rank[rb]:
            parent[ra] = rb
        elif rank[ra] > rank[rb]:
            parent[rb] = ra
        else:
            parent[rb] = ra
            rank[ra] += 1

    # 构建 eps 邻域内的近邻图，并统计每个点的邻居数量
    for i in range(n_samples):
        for dist, j in zip(distances[i], indices[i]):
            if i == j:
                continue
            if dist <= eps:
                neighbor_count[i] += 1
                neighbor_count[j] += 1
                union(i, j)

    # 判定核心点：邻居数量满足 min_samples-1（加上自己）
    core_component = {}
    for i in range(n_samples):
        if neighbor_count[i] + 1 >= min_samples:
            root = find(i)
            core_component[root] = True

    # 为包含核心点的连通分量分配簇编号，其余视为噪声 (-1)
    labels = np.full(n_samples, -1, dtype=int)
    comp_to_label: Dict[int, int] = {}
    next_label = 0
    for i in range(n_samples):
        root = find(i)
        if root in core_component:
            if root not in comp_to_label:
                comp_to_label[root] = next_label
                next_label += 1
            labels[i] = comp_to_label[root]

    return labels

