import re
from collections import Counter, defaultdict
from typing import Dict, List

import numpy as np
from lxml.html import HtmlComment, HtmlElement, HTMLParser, fromstring
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics.pairwise import cosine_similarity


TAGS_TO_IGNORE = ['script', 'style', 'meta', 'link', 'br', 'noscript']  # , 'b', 'i', 'strong'
TAGS_IGNORE_ATTR = ['a', 'i', 'b', 'li', 'tr', 'td', 'img', 'p', 'body']
RE_MD5 = re.compile(r'^[0-9a-f]{32}$')
RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')
RE_UUID = re.compile(r'^[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}$')
RE_TIMESTAMP = re.compile(r'^\d{10,13}$')  # 时间戳属性值
RE_NUM = re.compile(r'\d+')  # 自定义动态属性值


def html_to_element(html_data: str) -> HtmlElement:
    """构建html树.

    Args:
        html: str: 完整的html源码

    Returns:
        element: lxml.html.HtmlElement: element
    """
    parser = HTMLParser(collect_ids=False, encoding='utf-8', remove_comments=True, remove_pis=True)
    html_bytes = html_data.encode('utf-8')
    root = fromstring(html_bytes, parser=parser)
    return root


def __html_to_valid_element(html_source: str) -> HtmlElement:
    """html转element并获取有效DOM数据
    Args:
        html_source: html源码字符串
    Returns:
        element: lxml.html.HtmlElement
    """
    tree = html_to_element(html_source)
    root = tree.xpath('//body')[0] if tree.xpath('//body') else tree
    return root


def get_feature(html_source: str, is_ignore_tag: bool = True) -> Dict:
    """获取DOM有效tag和attr
    Args:
        html_source: html源码字符串
        is_ignore_tag: bool 是否忽略TAGS_TO_IGNORE可忽略的标签
    Returns:
        dict:
        {
            "tags": {1: ["<body>/div"], 2: [...]},
            "attrs": {1: ["nav", "content", "footer"], 2: [...]}
        }
    """
    doc = __html_to_valid_element(html_source)
    return __recursive_extract_tags(doc, is_ignore_tag)


def __parse_tag_attr(tag_attrs_lst: List[set]) -> Dict:
    tags = []
    attrs = []
    for tag_attrs in tag_attrs_lst:
        for tag_attr in tag_attrs:
            el = html_to_element(tag_attr)
            if el.tag == 'html':
                continue
            tags.append(el.tag)
            attrs.extend([v for k, v in el.attrib.items()])
    return {'tags': tags, 'attrs': attrs}


def __recursive_extract_tags(doc: HtmlElement, is_ignore_tag: bool = True) -> Dict:
    """递归获取标签及属性
        Args:
            doc: lxml.html.HtmlElement
        Returns:
            Dict
            {
                "tags": {1: ["<body>/div"], 2: [...]},
                "attrs": {1: ["content", "footer"], 2: [...]}
            }
    """

    def __get_children(el_lst: List[HtmlElement], layer_n: int, tag_attr: Dict):
        el_tag_attr = list()
        next_el = list()
        for el in el_lst:
            parent_tag_attr = set()
            for child in el.getchildren():
                if isinstance(child, HtmlComment) or child.tag is None:
                    continue
                tag = child.tag.lower()
                if is_ignore_tag and tag in TAGS_TO_IGNORE:
                    continue
                next_el.append(child)
                if tag in TAGS_IGNORE_ATTR:
                    parent_tag_attr.add(f'<{tag}>')
                else:
                    attrs_str = __parse_attributes(child)
                    parent_tag_attr.add(f'<{tag} {attrs_str}>' if attrs_str else f'<{tag}>')

            el_tag_attr.append(parent_tag_attr)

        layer_tag_attr = __parse_tag_attr(el_tag_attr)
        if layer_tag_attr.get('tags'):
            tag_attr['tags'][layer_n] = layer_tag_attr['tags']
        if layer_tag_attr.get('attrs'):
            tag_attr['attrs'][layer_n] = layer_tag_attr['attrs']
        if next_el:
            return __get_children(next_el, layer_n + 1, tag_attr)

    tag_attr = defaultdict(dict)
    __get_children([doc], 1, tag_attr)
    return dict(tag_attr) if tag_attr.get('tags') else None


def __parse_attributes(element: HtmlElement):
    """解析标签属性值."""
    class_s = None
    id_s = None
    class_attr = element.get('class')
    if class_attr:
        class_d = class_attr.split()
        if len(class_d) > 1:
            class_s = ' '.join([i for i in class_d if not RE_NUM.search(i)])
        elif len(class_d) == 1:
            class_s = __standardizing_dynamic_attributes(class_d[0])

    id_attr = element.get('id')
    if id_attr:
        id_d = id_attr.split()
        if len(id_d) > 1:
            id_s = ' '.join([i for i in id_d if not RE_NUM.search(i)])
        elif len(id_d) == 1:
            id_s = __standardizing_dynamic_attributes(id_d[0])

    if not class_s and not id_s:
        return None
    else:
        return ' '.join([f'{k}= "{v}"' for k, v in {'class': class_s, 'id': id_s}.items() if v])


def __standardizing_dynamic_attributes(attr_value):
    """将动态属性值标准化为统一表示."""
    if RE_MD5.fullmatch(attr_value):
        return '[MD5]'
    if RE_SHA1.fullmatch(attr_value):
        return '[SHA1]'
    if RE_UUID.fullmatch(attr_value):
        return '[UUID]'
    if RE_TIMESTAMP.fullmatch(attr_value):
        return '[TIMESTAMP]'
    if RE_NUM.search(attr_value):
        return re.sub(r'\d+', '', attr_value)

    return attr_value  # 不是可识别的哈希则返回原值


def __list_to_dict(lst: List[Dict]) -> dict:
    """列表转字典
    Args:
        lst: list
        [{'<body>/div': 1}, {'<div>[1]/div': 1, '<div>[2]/div': 1, '<div>[3]/ul': 1}, ...]
    Returns:
        dict {'<body>/div': 1, '<div>[1]/div': 1, '<div>[2]/div': 1, '<div>[3]/ul': 1, ...}
    """
    res = defaultdict(int)
    for idx, d in enumerate(lst):
        for k, v in d.items():
            res[f'{idx}_{k}'] += 1

    return dict(res)


def __cosin_simil(feature1: Dict, feature2: Dict, k: float = 0.7) -> np.float32:
    """余弦相似度计算，入参为向量化后的数据
    Args:
        feature1: dict {"tags": [0,0,1,1,1,1,0...], "attrs": [1,1,1...]}
        feature2: dict {"tags": [1,0,1,0,1,1,0...], "attrs": [1,0,1...]}
        k: tags 和 attrs 权重占比，默认1:1
    Returns:
        np.float32: cosine similarity
    """
    tag_sim = cosine_similarity(np.array([feature1.get('tags', []), feature2.get('tags', [])]))[0][1]
    if feature1.get('attrs').size == 0 or feature2.get('attrs').size == 0:
        k = 1
        return round(tag_sim * k, 8)
    else:
        attr_sim = cosine_similarity(np.array([feature1.get('attrs', []), feature2.get('attrs', [])]))[0][1]
        return round(tag_sim * k + attr_sim * (1 - k), 8)


def __simp_tags(d: dict, layer_n: int) -> dict:
    """根据layer_n获取有效内容，并合并有效层级内容为一个list
    Args:
        d: dict
        {
            1: ['<body>/div'],
            2: ['<div>[1]/div', '<div>[2]/div', '<div>[3]/ul'],
            ...
        }
        layer_n: int 有效层级的限制条件
    Returns:
        dict {'<body>/div': 1, '<div>[1]/div': 1, '<div>[2]/div': 1, '<div>[3]/ul': 1, ...}
    """
    return __list_to_dict([{tag: 1 for tag in v} for k, v in d.items() if int(k) <= layer_n])


def __simp_features(features_list: List) -> List[Dict]:
    """根据有效层级参数layer_n获取有效数据并向量化
    Args:
        features_list: list
        [
            {
            'tags': {1: ['<body>/div'], 2: ['<div>[2]/div', '<div>[1]/div', '<div>[3]/ul'], ...},
            "attrs": {1: ['nav nav-fixed', 'content', 'footer'], 2: ['foot', 'container'], ...}
            },
            {...}
        ]
    Returns:
        List[Dict]
        [
            {'tags': array([0, 1, 1, ...]), 'attrs': array([0, 1, 1, ...])},
            {...}
        ]
    """
    layer_n = __parse_valid_layer(features_list)
    tags_vec = __parse_vectors([__simp_tags(feature.get('tags', {}), layer_n) for feature in features_list])
    attrs_vec = __parse_vectors([__simp_tags(feature.get('attrs', {}), layer_n) for feature in features_list])
    return layer_n, [{'tags': tags_vec[i], 'attrs': attrs_vec[i]} for i in range(len(tags_vec))]


def __parse_vectors(data_lst: List) -> np.array:
    """数据向量化
    Args:
        data_lst: list [{'<body>/div': 1, '<div>[3]/ul': 1, '<div>[2]/div': 1, '<div>[1]/div': 1, ...]
    Returns:
        np.array 向量结果
    """
    vectorizer = DictVectorizer(sparse=False)
    X = vectorizer.fit_transform(data_lst).astype(np.float32)
    return X


def __parse_valid_layer(features: List[Dict]) -> int:
    """计算最大众数，获取有效层级限制条件
    Args:
        features: List
        [
            {
            'tags': {1: ['<body>/div'], 2: ['<div>[2]/div', '<div>[1]/div', '<div>[3]/ul'], ...},
            'attrs': {1: ['footer', 'content', 'nav nav-fixed'], 2: ['foot', 'container'], ...}
            },
            {...}
        ]
    Returns:
        int layser_n 限制层级最大深度
    """
    layer_max_l = []
    for data in features:
        max_key = int(max(data['tags'], key=lambda k: len(data['tags'][k])))
        layer_max_l.append(max_key)
    counter = Counter(layer_max_l)
    layer_n = counter.most_common(1)[0][0]
    return layer_n if layer_n > 1 else len(features[0]['tags'])


def cluster_html_struct(sampled_list: List[Dict], threshold=0.95) -> List[Dict]:
    """批量domain数据计算layout
    Args:
        sampled_list: list [{"features": {}}]
        threshold: 有效相似度限制条件，默认0.95
    Returns:
        List
    """
    success = []
    layout_list = []
    features = [tt['feature'] for tt in sampled_list]

    layer_n, features_vec = __simp_features(features)
    features_num = len(features)
    similarity_matrix = np.zeros((features_num, features_num))
    for i in range(features_num):
        for j in range(i, features_num):
            if i == j:
                simil_rate = 1.0
            else:
                simil_rate = __cosin_simil(features_vec[i], features_vec[j])
            similarity_matrix[i, j] = simil_rate
            similarity_matrix[j, i] = simil_rate
    similarity_matrix = np.clip(similarity_matrix, 0, 1)
    clustering = DBSCAN(eps=1 - threshold, min_samples=2, metric='precomputed')
    layout_ids = clustering.fit_predict(1 - similarity_matrix)
    for idd, data in zip(layout_ids, sampled_list):
        layout_list.append(int(idd))
        data['layout_id'] = int(idd)
        data['max_layer_n'] = layer_n
        success.append(data)
    return success, list(set(layout_list))


def sum_tags(tags: Dict):
    """统计feature DOM每层的tag量级和总tag量级
    Args:
        tags: dict
        {
            "tags": {1: ["<body>/div"], 2: [...]},
        }
    Return:
        l_s: DOM每层的tag量级
        s： 总tag量级
    """
    l_s = {k: len(v) for k, v in tags.items()}
    s = sum(l_s.values())
    return l_s, s


def similarity(feature1: Dict, feature2: Dict, layer_n=5, k=0.7) -> float:
    """余弦相似度计算，入参为feature字典
    Args:
        feature1: dict
        {
            "tags": {1: ["<body>/div"], 2: [...]},
            "attrs": {1: ["nav", "content", "footer"], 2: [...]}
        }
        feature2: dict
        {
            "tags": {1: ["<body>/div"], 2: [...]},
            "attrs": {1: ["nav", "content", "footer"], 2: [...]}
        }
        layer_n: 相似度计算DOM树层级深度，默认为5
        k: tags 和 attrs 权重占比，k表示tags权重，(1-k)为attrs权重，默认0.7:0.3
    Return:
        np.float32: cosine similarity
    """
    if not isinstance(feature1, dict) or not isinstance(feature2, dict):
        raise Exception('feature1 and feature2 must be dictionaries')

    def process_feature(feat):
        return {
            'tags': __simp_tags(feat.get('tags', {}), layer_n),
            'attrs': __simp_tags(feat.get('attrs', {}), layer_n)
        }

    f1 = process_feature(feature1)
    f2 = process_feature(feature2)

    f1_tag = f1.get('tags', {})
    f2_tag = f2.get('tags', {})
    if not f1_tag or not f2_tag:
        return 0.0
    tag_vecs = __parse_vectors([f1_tag, f2_tag])
    tag_sim = cosine_similarity(tag_vecs)[0][1]

    f1_attr = f1.get('attrs', {})
    f2_attr = f2.get('attrs', {})
    if not f1_attr or not f2_attr:
        return round(tag_sim, 8)

    attr_vecs = __parse_vectors([f1_attr, f2_attr])
    attr_sim = cosine_similarity(attr_vecs)[0][1]
    return round(tag_sim * k + attr_sim * (1 - k), 8)


def fuse_features(features: List[Dict], layer_n=5, k=0.7) -> np.ndarray:
    """计算融合特征向量
    Args:
        features: List[Dict]
        [
            {
                "tags": {1: ["<body>/div"], 2: [...]},
                "attrs": {1: ["nav", "content", "footer"], 2: [...]}
            },
            {...}
        ]
        layer_n: 相似度计算DOM树层级深度，默认为5
        k: tags 和 attrs 权重占比，k 表示 tags 权重，(1-k) 为 attrs 权重，默认 0.7:0.3
    Return:
        np.ndarray: 每个 feature 对应一条融合后的向量
    """
    if not features:
        return np.empty((0, 0), dtype=np.float32)

    fused_dicts = []
    for feature in features:
        tags_dict = __simp_tags(feature.get('tags', {}), layer_n)
        attrs_dict = __simp_tags(feature.get('attrs', {}), layer_n)

        combined = {}
        # tag 维度加权
        for key, value in tags_dict.items():
            combined[f't:{key}'] = float(value) * float(k)

        # attr 维度加权
        if attrs_dict:
            attr_weight = 1.0 - float(k)
            for key, value in attrs_dict.items():
                combined[f'a:{key}'] = float(value) * attr_weight

        fused_dicts.append(combined)

    # 统一做一次向量化，保证在同一特征空间
    return __parse_vectors(fused_dicts)


def __get_max_width_layer(tags):
    max_length = 0
    max_width_layer = 0
    for layer_n, layer in tags.items():
        if len(layer) > max_length:
            max_width_layer = layer_n
            max_length = len(layer)

    return max_width_layer - 2 if max_width_layer > 4 else 3
