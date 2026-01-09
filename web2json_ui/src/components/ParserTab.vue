<template>
  <div class="parser-tab">
    <!-- 步骤1: HTML输入 -->
    <section class="card">
      <h2>{{ t('step1.title') }}</h2>
      <p class="hint">{{ t('step1.hint') }}</p>

      <div class="input-tabs">
        <button
          class="tab-button"
          :class="{ active: inputMode === 'file' }"
          @click="inputMode = 'file'"
        >
          {{ t('step1.uploadFiles') }}
        </button>
        <button
          class="tab-button"
          :class="{ active: inputMode === 'html' }"
          @click="inputMode = 'html'"
        >
          {{ t('step1.htmlSource') }}
        </button>
      </div>

      <!-- Mode 1: 文件上传 -->
      <div v-if="inputMode === 'file'" class="input-section">
        <div class="upload-options">
          <div class="upload-option">
            <label class="upload-label">{{ t('step1.selectFiles') }}</label>
            <input
              type="file"
              ref="fileInput"
              @change="handleFileUpload"
              accept=".html,.htm"
              multiple
              style="display: none;"
            />
            <button @click="$refs.fileInput.click()" class="custom-file-button">
              📁 {{ t('step1.clickToSelect') }}
            </button>
            <span class="file-status">{{ fileInputStatus }}</span>
          </div>
          <div class="upload-option">
            <label class="upload-label">{{ t('step1.selectFolder') }}</label>
            <input
              type="file"
              ref="folderInput"
              @change="handleFileUpload"
              accept=".html,.htm"
              webkitdirectory
              directory
              style="display: none;"
            />
            <button @click="$refs.folderInput.click()" class="custom-file-button">
              📂 {{ t('step1.clickToSelectFolder') }}
            </button>
            <span class="file-status">{{ folderInputStatus }}</span>
          </div>
        </div>
        <div v-if="uploadedFiles.length" class="file-list">
          <div v-for="(file, index) in uploadedFiles" :key="index" class="file-item">
            <span>{{ file.name }} ({{ formatFileSize(file.size) }})</span>
            <button @click="removeFile(index)" class="btn-remove-small">✕</button>
          </div>
        </div>
      </div>

      <!-- Mode 2: HTML源码输入 -->
      <div v-if="inputMode === 'html'" class="input-section">
        <div class="html-list">
          <div v-for="(html, index) in htmlContents" :key="index" class="html-item">
            <div class="html-header">
              <span>{{ t('step1.sampleLabel') }} {{ index + 1 }}</span>
              <button @click="removeHtml(index)" class="btn-remove-small">✕</button>
            </div>
            <textarea
              v-model="htmlContents[index]"
              :placeholder="t('step1.pasteHtmlPlaceholder')"
              rows="6"
              class="html-textarea"
            ></textarea>
          </div>
        </div>
        <button @click="addHtmlTextarea" class="btn-add-small">{{ t('step1.addHtmlSample') }}</button>
      </div>

      <div class="sample-count">
        <strong>{{ t('step1.samplesCount') }} {{ sampleCount }}</strong>
        <span v-if="sampleCount > 1"> {{ t('step1.iterationEnabled') }}</span>
      </div>
    </section>

    <!-- 步骤2: Schema模式 -->
    <section class="card">
      <h2>⚙️ {{ t('parserTab.step2') }}</h2>

      <div class="schema-mode-selector">
        <label class="mode-option">
          <input type="radio" v-model="schemaMode" value="predefined" />
          <div class="mode-content">
            <strong>{{ t('parserTab.predefinedMode') }}</strong>
            <span class="hint">{{ t('parserTab.predefinedHint') }}</span>
          </div>
        </label>
        <label class="mode-option">
          <input type="radio" v-model="schemaMode" value="auto" />
          <div class="mode-content">
            <strong>{{ t('parserTab.autoMode') }}</strong>
            <span class="hint">{{ t('parserTab.autoHint') }}</span>
          </div>
        </label>
      </div>

      <!-- 字段定义（predefined模式） -->
      <div v-if="schemaMode === 'predefined'" class="fields-section">
        <h3>{{ t('step2.title') }}</h3>
        <div class="fields-container">
          <div v-for="(field, index) in fields" :key="index" class="field-row">
            <input
              v-model="field.name"
              :placeholder="t('step2.fieldName')"
              class="field-input"
            />
            <input
              v-model="field.description"
              :placeholder="t('step2.fieldDescription')"
              class="field-input"
            />
            <select v-model="field.field_type" class="field-select">
              <option value="string">{{ t('step2.types.string') }}</option>
              <option value="int">{{ t('step2.types.int') }}</option>
              <option value="float">{{ t('step2.types.float') }}</option>
              <option value="bool">{{ t('step2.types.bool') }}</option>
              <option value="array">{{ t('step2.types.array') }}</option>
            </select>
            <button @click="removeField(index)" class="btn-remove-small">✕</button>
          </div>
        </div>
        <button @click="addField" class="btn-add-small">{{ t('step2.addField') }}</button>
      </div>
    </section>

    <!-- 步骤3: 生成按钮 -->
    <section class="card">
      <button
        @click="generateParser"
        :disabled="loading || !canGenerate"
        class="btn-generate"
        :class="{ loading }"
      >
        <span v-if="loading">🔄 {{ t('parserTab.generating') }}</span>
        <span v-else>🚀 {{ t('parserTab.startGenerate') }}</span>
      </button>
      <p v-if="error" class="error-message">{{ error }}</p>
    </section>

    <!-- 进度显示 -->
    <section v-if="taskId && !results" class="card progress-section">
      <h2>⏳ {{ t('parserTab.progressTitle') }}</h2>

      <!-- 错误显示（如果有错误，优先显示） -->
      <div v-if="error" class="error-alert">
        <div class="error-icon">⚠️</div>
        <div class="error-content">
          <h3>{{ t('parserTab.errorOccurred') || '执行出错' }}</h3>
          <p>{{ error }}</p>
          <div v-if="error.includes('API额度不足') || error.includes('insufficient_user_quota')" class="error-solution">
            <strong>💡 解决方案：</strong>
            <ul>
              <li>请检查API密钥的额度余额</li>
              <li>前往API服务商充值</li>
              <li>或更换其他可用的API密钥</li>
            </ul>
          </div>
          <div v-else-if="error.includes('403') || error.includes('权限')" class="error-solution">
            <strong>💡 解决方案：</strong>
            <ul>
              <li>检查.env文件中的API密钥是否正确</li>
              <li>确认API密钥有访问权限</li>
              <li>检查API Base URL配置是否正确</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 进度条（无错误时显示） -->
      <div v-else>
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: `${progress}%` }">
            <span class="progress-text">{{ progress }}%</span>
          </div>
        </div>

        <div class="progress-info">
          <div v-if="currentPhase">
            <strong>{{ t('parserTab.currentPhase') }}:</strong> {{ t(`parserTab.phases.${currentPhase}`) }}
          </div>
          <div v-if="logs.length > 0" class="latest-log">
            {{ logs[logs.length - 1] }}
          </div>
        </div>

        <button @click="cancelTask" class="btn-cancel" :disabled="cancelling">
          {{ cancelling ? t('parserTab.cancelling') : t('parserTab.cancel') }}
        </button>
      </div>
    </section>

    <!-- 结果显示 -->
    <section v-if="results" class="card results-section">
      <h2>✅ {{ t('parserTab.resultsTitle') }}</h2>

      <!-- 下载按钮 -->
      <div class="download-buttons">
        <button @click="downloadJsonl" class="btn-download primary">
          📄 {{ t('parserTab.downloadJsonl') }}
        </button>
        <button @click="downloadCsv" class="btn-download secondary">
          📊 {{ t('parserTab.downloadCsv') }}
        </button>
        <button @click="downloadZip" class="btn-download tertiary">
          📦 {{ t('parserTab.downloadZip') }}
        </button>
      </div>

      <!-- 预览表格 -->
      <div class="results-preview">
        <h3>{{ t('parserTab.previewTitle') }} ({{ t('parserTab.showing10Rows', { total: results.parsed_files.length }) }})</h3>

        <div class="table-container">
          <table class="results-table">
            <thead>
              <tr>
                <th>#</th>
                <th v-for="field in tableFields" :key="field">{{ field }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in tableRows" :key="index">
                <td class="row-number">{{ index + 1 }}</td>
                <td v-for="field in tableFields" :key="field" class="cell-value">
                  {{ formatCellValue(row[field]) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="results.parsed_files.length > 10" class="more-info">
          {{ t('parserTab.moreRows', { count: results.parsed_files.length - 10 }) }}
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useI18n } from '../i18n/index.js'
import { parserAPI } from '../api/parser.js'

const { t } = useI18n()

// State
const inputMode = ref('file')  // 默认为文件上传模式
const uploadedFiles = ref([])
const htmlContents = ref([''])
const schemaMode = ref('predefined')
const fields = ref([{ name: '', description: '', field_type: 'string' }])
const loading = ref(false)
const error = ref('')
const taskId = ref(null)
const progress = ref(0)
const currentPhase = ref('')
const logs = ref([])
const results = ref(null)
const previewFiles = ref([])
const allParsedData = ref([])  // 存储所有解析的数据
const cancelling = ref(false)
const ws = ref(null)

// Computed
const sampleCount = computed(() => {
  if (inputMode.value === 'file') {
    return uploadedFiles.value.length
  } else {
    return htmlContents.value.filter(h => h.trim()).length
  }
})

const canGenerate = computed(() => {
  const hasInput = sampleCount.value > 0
  const hasFields = schemaMode.value === 'auto' || fields.value.some(f => f.name.trim())
  return hasInput && hasFields
})

// 文件选择状态
const fileInputStatus = computed(() => {
  const fileCount = uploadedFiles.value.filter(f => !f.isFolder).length
  if (fileCount === 0) return t('step1.noFileSelected')
  return t('step1.filesSelected', { count: fileCount })
})

const folderInputStatus = computed(() => {
  const folderFileCount = uploadedFiles.value.filter(f => f.isFolder).length
  if (folderFileCount === 0) return t('step1.noFileSelected')
  return t('step1.filesSelected', { count: folderFileCount })
})

// 表格数据
const tableFields = computed(() => {
  if (!previewFiles.value || previewFiles.value.length === 0) return []

  // 获取所有字段名（从第一个结果中）
  const firstResult = previewFiles.value[0]
  if (firstResult && firstResult.content) {
    return Object.keys(firstResult.content)
  }
  return []
})

const tableRows = computed(() => {
  if (!previewFiles.value || previewFiles.value.length === 0) return []

  // 返回前10行数据
  return previewFiles.value.slice(0, 10).map(file => file.content || {})
})

// 文件处理
async function handleFileUpload(event) {
  const files = Array.from(event.target.files)
  const isFolder = event.target.hasAttribute('webkitdirectory')

  for (const file of files) {
    const text = await file.text()
    uploadedFiles.value.push({
      name: file.name,
      size: file.size,
      content: text,
      isFolder: isFolder
    })
  }
}

function removeFile(index) {
  uploadedFiles.value.splice(index, 1)
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// HTML methods
function addHtmlTextarea() {
  htmlContents.value.push('')
}

function removeHtml(index) {
  if (htmlContents.value.length > 1) {
    htmlContents.value.splice(index, 1)
  }
}

// 字段管理
function addField() {
  fields.value.push({ name: '', description: '', field_type: 'string' })
}

function removeField(index) {
  if (fields.value.length > 1) {
    fields.value.splice(index, 1)
  }
}

// 生成解析器
async function generateParser() {
  loading.value = true
  error.value = ''
  results.value = null
  taskId.value = null
  progress.value = 0
  logs.value = []
  allParsedData.value = []  // 清空之前的数据

  try {
    // 构建请求参数
    const params = {
      schema_mode: schemaMode.value,
      domain: 'web_parser',
      iteration_rounds: 3
    }

    // 根据输入模式设置对应的参数
    if (inputMode.value === 'file') {
      params.html_contents = uploadedFiles.value.map(f => f.content)
    } else {
      params.html_contents = htmlContents.value.filter(h => h.trim())
    }

    // 添加字段（predefined模式）
    if (schemaMode.value === 'predefined') {
      params.fields = fields.value.filter(f => f.name.trim())
      if (params.fields.length === 0) {
        throw new Error(t('messages.fieldRequired'))
      }
    } else {
      params.fields = []
    }

    // 创建任务
    const response = await parserAPI.generate(params)

    if (response.success) {
      taskId.value = response.task_id
      connectWebSocket(response.task_id)
    } else {
      error.value = response.error || 'Failed to create task'
    }
  } catch (err) {
    console.error('Generate parser error:', err)
    error.value = err.message || err.detail || 'An error occurred'
  } finally {
    loading.value = false
  }
}

// WebSocket连接
function connectWebSocket(taskIdValue) {
  const wsUrl = `ws://localhost:8000/api/parser/progress/${taskIdValue}`
  console.log('Connecting to WebSocket:', wsUrl)

  ws.value = new WebSocket(wsUrl)

  ws.value.onopen = () => {
    console.log('WebSocket connected')
    logs.value.push('Connected to server')
  }

  ws.value.onmessage = (event) => {
    const message = JSON.parse(event.data)
    console.log('WebSocket message:', message)

    switch (message.type) {
      case 'progress':
        progress.value = message.percentage || 0
        currentPhase.value = message.phase || ''
        if (message.step) {
          logs.value.push(message.step)
        }
        break

      case 'log':
        const logMessage = `[${message.log_level}] ${message.log_message}`
        logs.value.push(logMessage)

        // 如果是错误日志，也显示在错误区域
        if (message.log_level === 'error') {
          error.value = message.log_message
          // 停止加载状态
          loading.value = false
        }
        break

      case 'complete':
        progress.value = 100
        handleComplete(message.result)
        break

      case 'error':
        error.value = message.error || '任务执行失败'
        loading.value = false
        taskId.value = null
        // 关闭WebSocket
        if (ws.value) {
          ws.value.close()
          ws.value = null
        }
        break
    }
  }

  ws.value.onerror = (err) => {
    console.error('WebSocket error:', err)
    error.value = 'WebSocket连接失败，请检查服务器状态'
    loading.value = false
  }

  ws.value.onclose = (event) => {
    console.log('WebSocket disconnected', event)
    // 如果是异常关闭（非正常完成）且没有错误信息，显示警告
    if (!event.wasClean && !error.value && !results.value) {
      error.value = '连接意外断开，任务可能未完成'
      loading.value = false
    }
  }
}

// 处理完成
async function handleComplete(result) {
  console.log('Task completed:', result)
  console.log('Parsed files count:', result.parsed_files?.length)

  results.value = result
  previewFiles.value = []
  allParsedData.value = []

  // 使用新的API获取所有结果数据
  if (taskId.value) {
    console.log('Loading all results via API...')

    try {
      const response = await fetch(`http://localhost:8000/api/parser/results/${taskId.value}`)
      console.log('API response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('API response data:', data)

        if (data.success && data.results) {
          allParsedData.value = data.results
          console.log(`Loaded ${data.results.length} results from API`)

          // 前10个用于预览
          previewFiles.value = data.results.slice(0, 10).map((content, index) => ({
            filename: `result_${index + 1}.json`,
            content: content
          }))

          console.log('Preview files:', previewFiles.value.length)
        } else {
          console.error('API response format error:', data)
        }
      } else {
        console.error('API request failed:', response.status, response.statusText)
        error.value = `Failed to load results: HTTP ${response.status}`
      }
    } catch (err) {
      console.error('Failed to load results from API:', err)
      error.value = 'Failed to load results: ' + err.message
    }
  } else {
    console.warn('No taskId available')
  }

  console.log('Data loading complete:', {
    total: allParsedData.value.length,
    preview: previewFiles.value.length
  })
  console.log('allParsedData sample:', allParsedData.value[0])

  // 关闭WebSocket
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
}

// 取消任务
async function cancelTask() {
  if (!taskId.value) return

  cancelling.value = true
  try {
    await parserAPI.cancel(taskId.value)
    logs.value.push('Task cancellation requested')
  } catch (err) {
    console.error('Cancel task error:', err)
    error.value = 'Failed to cancel task'
  } finally {
    cancelling.value = false
  }
}

// 下载功能
async function downloadJsonl() {
  console.log('downloadJsonl called')
  console.log('allParsedData.value:', allParsedData.value)
  console.log('allParsedData.value.length:', allParsedData.value?.length)

  if (!allParsedData.value || allParsedData.value.length === 0) {
    const errorMsg = 'No data to download. Please wait for results to load.'
    error.value = errorMsg
    console.error(errorMsg)
    alert(errorMsg)
    return
  }

  try {
    console.log('Converting to JSONL...')
    // 将所有数据转换为JSONL格式
    const jsonlLines = allParsedData.value.map(data => JSON.stringify(data))
    const jsonlContent = jsonlLines.join('\n')

    console.log('JSONL content length:', jsonlContent.length)
    console.log('First line:', jsonlLines[0]?.substring(0, 100))

    // 创建JSONL文件并下载
    const blob = new Blob([jsonlContent], { type: 'application/jsonl' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `results_${taskId.value?.substring(0, 8) || 'export'}.jsonl`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    console.log('JSONL downloaded:', jsonlLines.length, 'lines')
    logs.value.push('JSONL downloaded successfully')
  } catch (err) {
    console.error('Download JSONL error:', err)
    error.value = 'Failed to download JSONL: ' + err.message
  }
}

async function downloadCsv() {
  console.log('downloadCsv called')
  console.log('allParsedData.value:', allParsedData.value)
  console.log('allParsedData.value.length:', allParsedData.value?.length)

  if (!allParsedData.value || allParsedData.value.length === 0) {
    const errorMsg = 'No data to download. Please wait for results to load.'
    error.value = errorMsg
    console.error(errorMsg)
    alert(errorMsg)
    return
  }

  try {
    console.log('Converting to CSV...')
    // 获取所有字段名
    const fields = Object.keys(allParsedData.value[0])
    console.log('Fields:', fields)

    // 生成CSV内容
    const csvRows = []
    // 添加表头
    csvRows.push(fields.map(field => `"${field}"`).join(','))
    // 添加数据行
    for (const row of allParsedData.value) {
      const values = fields.map(field => {
        const value = row[field]
        // 处理特殊字符
        if (value === null || value === undefined) return '""'
        const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value)
        return `"${stringValue.replace(/"/g, '""')}"`
      })
      csvRows.push(values.join(','))
    }

    // 创建CSV文件并下载
    const csvContent = csvRows.join('\n')
    console.log('CSV content length:', csvContent.length)
    console.log('First row:', csvRows[0])
    console.log('Second row:', csvRows[1])

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `results_${taskId.value?.substring(0, 8) || 'export'}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    console.log('CSV downloaded:', csvRows.length - 1, 'rows')
    logs.value.push('CSV downloaded successfully')
  } catch (err) {
    console.error('Download CSV error:', err)
    error.value = 'Failed to download CSV: ' + err.message
  }
}

async function downloadZip() {
  if (!taskId.value) return

  try {
    const blob = await parserAPI.downloadZip(taskId.value)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `parser_results_${taskId.value.substring(0, 8)}.zip`
    a.click()
    URL.revokeObjectURL(url)

    logs.value.push('ZIP downloaded successfully')
  } catch (err) {
    console.error('Download ZIP error:', err)
    error.value = 'Failed to download ZIP'
  }
}

// Debug状态检查
function checkStatus() {
  console.log('=== DEBUG STATUS ===')
  console.log('results.value:', results.value)
  console.log('results.value.parsed_files:', results.value?.parsed_files)
  console.log('results.value.parsed_files.length:', results.value?.parsed_files?.length)
  console.log('allParsedData.value:', allParsedData.value)
  console.log('allParsedData.value.length:', allParsedData.value?.length)
  console.log('previewFiles.value:', previewFiles.value)
  console.log('previewFiles.value.length:', previewFiles.value?.length)
  console.log('tableFields:', tableFields.value)
  console.log('tableRows:', tableRows.value)

  alert(`Debug Status:
- Results: ${results.value ? 'YES' : 'NO'}
- Parsed files: ${results.value?.parsed_files?.length || 0}
- All parsed data: ${allParsedData.value?.length || 0}
- Preview files: ${previewFiles.value?.length || 0}

Check console for detailed logs.`)
}

// 格式化单元格值
function formatCellValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.length > 0 ? `[${value.length} items]` : '[]'
    }
    return JSON.stringify(value)
  }
  // 限制字符串长度
  const stringValue = String(value)
  return stringValue.length > 100 ? stringValue.substring(0, 100) + '...' : stringValue
}

// 清理
onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<style scoped>
.parser-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Card 样式 */
.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.card h2 {
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5rem;
}

.hint {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 15px;
  padding: 10px;
  background: #fef3c7;
  border-radius: 6px;
  border-left: 4px solid #f59e0b;
}

/* Tabs */
.input-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tab-button {
  padding: 10px 20px;
  border: 2px solid #667eea;
  background: white;
  color: #667eea;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
  min-width: 120px;
  max-width: 200px;
}

.tab-button.active {
  background: #667eea;
  color: white;
}

.tab-button:hover:not(.active) {
  background: #f0f0f0;
}

/* Input Section */
.input-section {
  margin-top: 10px;
}

/* Upload Options */
.upload-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 15px;
}

.upload-option {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-label {
  font-weight: 600;
  color: #667eea;
  font-size: 0.9rem;
}

/* File Upload */
.file-input {
  display: block;
  width: 100%;
  padding: 15px;
  border: 2px dashed #667eea;
  border-radius: 8px;
  background: #f8f9ff;
  cursor: pointer;
  transition: all 0.3s;
}

.file-input:hover {
  background: #f0f2ff;
  border-color: #5568d3;
}

/* Custom File Button */
.custom-file-button {
  width: 100%;
  padding: 15px;
  border: 2px dashed #667eea;
  border-radius: 8px;
  background: #f8f9ff;
  color: #667eea;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.custom-file-button:hover {
  background: #f0f2ff;
  border-color: #5568d3;
  transform: translateY(-1px);
}

.file-status {
  font-size: 0.85rem;
  color: #666;
  min-height: 20px;
  display: block;
}

.file-list {
  margin-top: 15px;
  max-height: 300px;
  overflow-y: auto;
  padding-right: 5px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f3f4f6;
  border-radius: 8px;
  margin-bottom: 10px;
}

.file-item span {
  font-size: 14px;
  color: #333;
}

/* HTML Lists */
.html-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 15px;
}

.html-item {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  background: #fafafa;
}

.html-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.html-header span {
  font-weight: 600;
  color: #667eea;
}

.html-textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  resize: vertical;
  transition: border-color 0.3s;
}

.html-textarea:focus {
  outline: none;
  border-color: #667eea;
}

.sample-count {
  margin-top: 15px;
  padding: 12px;
  background: #e0e7ff;
  border-radius: 8px;
  text-align: center;
  color: #4338ca;
  font-size: 0.95rem;
}

/* Buttons */
.btn-add-small {
  padding: 12px 24px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.btn-add-small:hover {
  background: #059669;
}

.btn-remove-small {
  width: 32px;
  height: 32px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s;
}

.btn-remove-small:hover {
  background: #dc2626;
}

.btn-generate {
  width: 100%;
  padding: 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.2rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s, opacity 0.3s;
}

.btn-generate:hover:not(:disabled) {
  transform: scale(1.02);
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-generate.loading {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Messages */
.error-message {
  color: #ef4444;
  margin-top: 15px;
  padding: 12px;
  background: #fee2e2;
  border-radius: 8px;
  font-weight: 500;
}

/* Fields */
.fields-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 2fr 120px 40px;
  gap: 10px;
  align-items: center;
}

.field-input,
.field-select {
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.field-input:focus,
.field-select:focus {
  outline: none;
  border-color: #667eea;
}

/* Schema模式选择 */
.schema-mode-selector {
  display: flex;
  flex-direction: row;
  gap: 15px;
  margin: 15px 0;
}

.mode-option {
  display: flex;
  flex: 1;
  align-items: flex-start;
  gap: 12px;
  padding: 15px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.mode-option:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.mode-option input[type="radio"] {
  margin-top: 3px;
}

.mode-content {
  flex: 1;
}

.mode-content strong {
  display: block;
  color: #333;
  margin-bottom: 5px;
}

.mode-content .hint {
  display: block;
  color: #666;
  font-size: 0.9rem;
}

/* 字段部分 */
.fields-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 2px solid #e0e0e0;
}

.fields-section h3 {
  margin-bottom: 15px;
  color: #667eea;
}

/* 进度部分 */
.progress-section {
  background: #f0f9ff;
  border: 2px solid #3b82f6;
}

/* 错误提示 */
.error-alert {
  display: flex;
  gap: 20px;
  padding: 25px;
  background: #fef2f2;
  border: 2px solid #ef4444;
  border-radius: 12px;
  margin-bottom: 20px;
}

.error-icon {
  font-size: 48px;
  flex-shrink: 0;
}

.error-content {
  flex: 1;
}

.error-content h3 {
  color: #dc2626;
  margin: 0 0 10px 0;
  font-size: 1.2rem;
}

.error-content p {
  color: #991b1b;
  margin: 0 0 15px 0;
  line-height: 1.6;
}

.error-solution {
  background: #fff7ed;
  border-left: 4px solid #f59e0b;
  padding: 15px;
  border-radius: 6px;
}

.error-solution strong {
  color: #92400e;
  display: block;
  margin-bottom: 10px;
}

.error-solution ul {
  margin: 0;
  padding-left: 20px;
  color: #78350f;
}

.error-solution li {
  margin: 5px 0;
  line-height: 1.5;
}

.progress-bar-container {
  width: 100%;
  height: 40px;
  background: #e0e0e0;
  border-radius: 20px;
  overflow: hidden;
  margin: 20px 0;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.3s ease;
}

.progress-text {
  color: white;
  font-weight: 700;
  font-size: 16px;
}

.progress-info {
  padding: 15px;
  background: white;
  border-radius: 8px;
  margin-bottom: 15px;
}

.progress-info strong {
  color: #3b82f6;
}

.latest-log {
  margin-top: 10px;
  padding: 10px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #666;
  font-family: monospace;
}

.btn-cancel {
  width: 100%;
  padding: 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.btn-cancel:hover:not(:disabled) {
  background: #dc2626;
}

.btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 结果部分 */
.results-section {
  background: #f0fdf4;
  border: 2px solid #10b981;
}

.download-buttons {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
}

.btn-download {
  flex: 1;
  padding: 15px;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-download.primary {
  background: #10b981;
  color: white;
}

.btn-download.primary:hover {
  background: #059669;
  transform: scale(1.02);
}

.btn-download.secondary {
  background: #667eea;
  color: white;
}

.btn-download.secondary:hover {
  background: #5568d3;
  transform: scale(1.02);
}

.btn-download.tertiary {
  background: #f59e0b;
  color: white;
}

.btn-download.tertiary:hover {
  background: #d97706;
  transform: scale(1.02);
}

.btn-download.debug {
  background: #8b5cf6;
  color: white;
}

.btn-download.debug:hover {
  background: #7c3aed;
  transform: scale(1.02);
}

.results-preview h3 {
  margin-bottom: 20px;
  color: #10b981;
}

/* 表格样式 */
.table-container {
  overflow-x: auto;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  font-size: 14px;
}

.results-table thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.results-table th {
  padding: 12px 15px;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}

.results-table th:first-child {
  width: 50px;
  text-align: center;
}

.results-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
  transition: background-color 0.2s;
}

.results-table tbody tr:hover {
  background-color: #f8f9ff;
}

.results-table tbody tr:last-child {
  border-bottom: none;
}

.results-table td {
  padding: 12px 15px;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.results-table .row-number {
  text-align: center;
  font-weight: 600;
  color: #667eea;
  background: #f8f9ff;
}

.results-table .cell-value {
  color: #333;
}

.more-info {
  text-align: center;
  padding: 15px;
  background: #fef3c7;
  border-radius: 8px;
  color: #92400e;
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 768px) {
  .download-buttons {
    flex-direction: column;
  }

  .field-row {
    grid-template-columns: 1fr;
  }

  .input-tabs {
    flex-direction: column;
  }

  .tab-button {
    width: 100%;
  }

  .upload-options {
    grid-template-columns: 1fr;
  }

  .schema-mode-selector {
    flex-direction: column;
  }

  .results-table {
    font-size: 12px;
  }

  .results-table th,
  .results-table td {
    padding: 8px 10px;
  }

  .results-table td {
    max-width: 150px;
  }
}
</style>
