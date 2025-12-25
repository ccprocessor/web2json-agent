# web2json-agent

**让 AI 自动生成网页解析代码，告别手写 XPath 和 CSS 选择器，轻松得到结构化数据**

## 💡 项目简介

**web2json-agent** 是一个智能数据结构化解析工具，能够**自动分析网页结构并生成高质量的 Python 解析代码，并自动进行数据解析**。

📚 **完整项目总结**：查看 [docs/PROJECT_SUMMARY.md](doc/PROJECT_SUMMARY.md) 了解架构设计、技术流程、性能优化历程等详细信息。

如下图所示，只需提供网页 URL 或 HTML 源码，web2json-agent 会自动智能选取样例、分析页面结构、识别数据模式、生成解析器代码，并对所有网页进行高速批量处理，最终输出结构化数据，让你从繁琐的选择器编写和调试中解放出来。

![img.png](docs/img.png)

### ✨ 核心价值对比

| 对比维度 | 传统结构化 html 数据抽取           | 使用 web2json-agent 数据抽取                        |
|---------|---------------------------|-------------------------------------------|
| **HTML 结构分析** | ❌ 手动分析 HTML 结构，费时费力       | ✅ Agent 自动分析，秒级完成                         |
| **选择器编写** | ❌ 逐个编写 XPath/CSS 选择器，容易出错 | ✅ 🤖 **完全自动化**生成，无需手写                     |
| **调试适配** | ❌ 反复调试选择器，适配不同页面结构        | ✅ 🛡️ **高鲁棒性**：自动生成多个备选路径，智能适配结构变化        |
| **数据处理** | ❌ 处理数据结构和类型转换的繁琐代码        | ✅ 🔄 **智能优化**：自动去除广告/导航等噪音，生成干净代码         |
| **分析能力** | ❌ 依赖人工理解，提取偏主观            | ✅ 🤖 **AI智能分析**：自动理解HTML结构语义，提取更准确         |
| **性能优化** | ❌ 串行处理，速度慢               | ✅ 🚀 **并行加速**：API 调用自动并发，多样本学习提速 70%+    |
| **开发时间** | ⏱️ 几小时到几天                 | ⚡ 分钟级完成                                   |
| **代码可用性** | ❌ 需要配置环境、调试才能使用           | ✅ 📦 **开箱即用**：支持 CLI 和 Python 导入，直接运行     |
| **使用步骤** | ❌ 需要多个繁琐步骤                | ✅ 提供 URL/HTML 源码 → AI 自动完成 → 获得解析代码与结构化数据 |

**节省 80% 的开发时间，从几小时到几分钟！**

### 📋 示例

**输入：26 万字符的杂乱 HTML**（深度嵌套、无意义 class、大量广告和噪音）
```html
<html class="itcauecng idc0_347">
<head>
  <title>海南自贸港12月18日即将封关，「零关税」和「双15%」个税优惠政策...</title>
  <!-- ...省略 50+ 个 meta/link/script 标签... -->
</head>
<body>
  <div id="root" class="_2Jysd8SG _3kRqKz4Q">
    <div class="GlobalSideBar _1mQ9vkP3">...</div>  <!-- 导航栏 -->
    <div class="TopBar _2pWmP1eX">...</div>          <!-- 搜索框 -->

    <main>
      <!-- 问题标题buried在 5 层 div 嵌套中 -->
      <div class="QuestionHeader">
        <div class="QuestionHeader-content">
          <div class="QuestionHeader-main">
            <h1 class="QuestionHeader-title">海南自贸港12月18日即将封关...</h1>
            <div class="QuestionRichText--collapsed">
              <div class="RichText">
                <span>12月18日，海南自由贸易港将正式启动...</span>
      <!-- ...6 层嵌套... -->
              </div></div></div></div></div>

      <!-- 回答列表，每个回答有 5+ 层嵌套 -->
      <div class="List-list">
        <div class="List-item">
          <div class="ContentItem AnswerItem">
            <div class="ContentItem-main">
              <div class="RichContent">
                <div class="AuthorInfo-name">Saka财经</div>
                <div class="AuthorInfo-badge">CPA 注册会计师资格证持证人</div>
                <span class="RichText">海南这次一定要接住这个橄榄枝...</span>
      <!-- ...更多嵌套... -->
              </div></div></div></div>
        <!-- ...省略其他 53 个回答... -->
      </div>

      <aside>
        <div class="AdCard">...</div>  <!-- 广告 -->
        <div class="AdCard">...</div>  <!-- 广告 -->
      </aside>
    </main>
  </div>
  <script>window.__INITIAL_STATE__={"entities":{...}}</script>  <!-- 数万字符 -->
</body>
</html>
```

**输出：干净的结构化 JSON**（内置html精简工具，结合 AI 能力自动识别核心内容，过滤噪音）
```json
{
  "title": "海南自贸港12月18日即将封关，「零关税」和「双15%」个税优惠政策将有什么变化？...",
  "question_author": "每日经济新闻",
  "question_author_badge": "已认证机构号",
  "question_description": "12月18日，海南自由贸易港将正式启动全岛封关运作...",
  "topics": ["投资", "商业", "股票", "海南", "海纳百川开放共赢"],
  "view_count": "183,426",
  "answer_count": "54 个回答",
  "answers": [
    {
      "author": "Saka财经",
      "author_badge": "CPA 注册会计师资格证持证人",
      "content": "海南这次一定要接住这个橄榄枝，飞速发展的机会...",
      "publish_time": "编辑于 2025-12-16 15:42"
    },
    {
      "author": "闻号说经济",
      "author_badge": "CFA 注册金融分析师资格证持证人",
      "content": "2025年12月18日，海南自贸港将正式启动全岛封关运作...",
      "publish_time": "发布于 2025-12-16 12:31"
    },
    {
      "other": "其他回答省略"
    }
  ]
}
```

✨ **自动识别并提取**：标题、作者、话题标签、统计数据、**回答列表**（包含嵌套的作者信息、内容、时间等）

### 🚀 适用场景

- **📊 大规模数据采集** - 自动学习网页模式，批量处理成千上万个同类型页面
- **⚡ 批量爬虫开发** - 快速为博客、产品页、新闻等生成解析器，一次生成处处使用
- **🔬 数据分析项目** - 将海量网页转换为结构化数据，直接用于分析和建模
- **🚀 原型快速验证** - 分钟级验证数据提取可行性，无需手写代码
- **📚 学习参考** - 生成的代码可作为学习 BeautifulSoup 和 XPath 的最佳实践示例

---

## 🚀 快速开始

### 通过 pip 安装

```bash
# 1. 安装包
pip install web2json-agent

# 2. 初始化配置
web2json setup  # 交互式配置（推荐）
# 或手动配置：web2json init && vim .env

# 3. 准备网页目录并一键生成解析器+批量解析
web2json -d html_samples/ -o output/result
# 完成！解析结果自动保存到 output/result/ 目录
```

**执行过程说明**：

1. 系统会自动从 `html_samples/` 目录中选择前 3 个 HTML 文件用于学习（可通过 `--iteration-rounds` 参数调整）
2. 基于样本生成解析器，保存到 `output/blog/parsers/final_parser.py`
3. 自动使用生成的解析器解析**所有** HTML 文件
4. 解析结果保存到 `output/blog/result/` 目录，每个 HTML 对应一个 JSON 文件

---

## 🎯 Schema模式（定制要抽取的字段）

```bash
# 模式1：自动模式 (auto) - 快速探索，不确定需要提取哪些字段
web2json -d html_samples/ -o output/result

# 模式2：预定义模式 (predefined) - 明确知道需要提取哪些字段，需要精确控制输出结构
web2json -d html_samples/ -o output/result --interactive-schema
```

---

## 📄 许可证

MIT License

---

**最后更新**: 2025-12-25
**版本**: 1.1.0