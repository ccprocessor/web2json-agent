export default {
  header: {
    title: 'Web2JSON',
    subtitle: 'AI 驱动的 智能网页解析 Agent'
  },
  step1: {
    title: '📄 步骤 1: 输入 HTML 样本',
    hint: '💡 提示：提供 2-5 个相似页面以获得更准确的解析效果',
    uploadFiles: '📁 上传文件',
    htmlSource: '📝 HTML 源码',
    selectFiles: '选择文件',
    selectFolder: '选择文件夹',
    sampleLabel: '样本',
    addHtmlSample: '+ 添加 HTML 样本',
    pasteHtmlPlaceholder: '在此粘贴 HTML 内容...',
    samplesCount: '样本数：',
    iterationEnabled: '(已启用迭代模式 ✨)'
  },
  step2: {
    title: '🏷️ 步骤 2: 定义字段',
    fieldName: '字段名称 *',
    fieldDescription: '描述（可选，填写后解析更准确）',
    addField: '+ 添加字段',
    types: {
      string: 'string',
      int: 'int',
      float: 'float',
      bool: 'bool',
      array: 'array'
    }
  },
  step3: {
    generateButton: '✨ 生成 XPath',
    generating: '🔄 正在生成 XPath...',
    processing: '正在处理 {count} 个样本，请稍候...'
  },
  step4: {
    title: '✅ 生成的 XPaths',
    noXpath: '(未生成 XPath)',
    copyTooltip: '复制 XPath',
    sampleValues: '示例值：',
    moreValues: '...还有 {count} 个'
  },
  messages: {
    copied: '✅ XPath 已复制到剪贴板！',
    copyFailed: '❌ 复制失败',
    fieldRequired: '请至少添加一个字段'
  },
  common: {
    remove: '删除'
  },
  tabs: {
    xpathGeneration: 'XPath 生成',
    parserGeneration: '结构化数据生成'
  },
  parserTab: {
    step1: '步骤 1: 输入 HTML 样本',
    hint: '提供 HTML 样本,AI 将自动分析并生成完整的解析器代码',
    step2: '步骤 2: 选择 Schema 模式',
    step3: '步骤 3: 选择输出类型',
    autoMode: '自动模式',
    autoHint: 'AI 智能选取字段',
    predefinedMode: '预定义模式',
    predefinedHint: '您指定要提取的字段名称',
    structuredDataMode: '生成结构化数据',
    structuredDataHint: '生成完整的解析器代码并输出JSON格式的结构化数据',
    xpathMode: '生成 XPath',
    xpathHint: '仅生成字段的XPath表达式',
    generate: '生成结构化数据',
    startGenerate: '开始生成',
    generating: '正在生成...',
    progressTitle: '生成进度',
    currentPhase: '当前阶段',
    phases: {
      planning: '规划中',
      schema_iteration: '提取和合并 Schema',
      code_generation: '生成解析器代码',
      batch_parsing: '批量解析 HTML 文件',
      packaging: '打包结果'
    },
    cancel: '取消任务',
    cancelling: '取消中...',
    resultsTitle: '生成结果',
    downloadJsonl: '下载 JSONL',
    downloadCsv: '下载 CSV',
    downloadZip: '下载 ZIP（JSON格式）',
    downloadParser: '下载 parser.py',
    previewTitle: '结果预览',
    showing10Rows: '显示前 10 行，共 {total} 行',
    moreRows: '...还有 {count} 行（请下载文件查看全部）',
    moreResults: '...还有 {count} 个文件（请下载 ZIP 查看全部）'
  }
}
