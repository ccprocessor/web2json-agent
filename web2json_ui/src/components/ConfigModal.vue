<template>
  <div v-if="show" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h2>⚙️ {{ t('configModal.title') || 'API配置' }}</h2>
        <button @click="closeModal" class="btn-close">✕</button>
      </div>

      <div class="modal-body">
        <!-- API Key -->
        <div class="form-group">
          <label>
            <strong>API Key</strong>
            <span class="required">*</span>
          </label>
          <div class="input-with-action">
            <input
              v-model="formData.api_key"
              :type="showApiKey ? 'text' : 'password'"
              :placeholder="t('configModal.apiKeyPlaceholder') || '请输入API Key'"
              class="form-input"
            />
            <button @click="toggleApiKeyVisibility" class="btn-toggle" type="button">
              {{ showApiKey ? '👁️' : '👁️‍🗨️' }}
            </button>
            <button @click="copyApiKey" class="btn-copy-small" type="button" :title="t('configModal.copy') || '复制'">
              📋
            </button>
          </div>
          <p class="hint-text">{{ t('configModal.apiKeyHint') || 'OpenAI或兼容的API密钥' }}</p>
        </div>

        <!-- API Base URL -->
        <div class="form-group">
          <label>
            <strong>API Base URL</strong>
          </label>
          <input
            v-model="formData.api_base"
            type="text"
            :placeholder="t('configModal.apiBasePlaceholder') || 'https://api.openai.com/v1'"
            class="form-input"
          />
          <p class="hint-text">{{ t('configModal.apiBaseHint') || 'API服务的基础URL' }}</p>
        </div>

        <!-- Iteration Rounds -->
        <div class="form-group">
          <label>
            <strong>{{ t('configModal.iterationRounds') || '迭代学习样本数' }}</strong>
          </label>
          <input
            v-model.number="formData.iteration_rounds"
            type="number"
            min="1"
            max="10"
            :placeholder="t('configModal.iterationRoundsPlaceholder') || '3'"
            class="form-input"
          />
          <p class="hint-text">{{ t('configModal.iterationRoundsHint') || '用于学习的HTML样本数量（默认3个）' }}</p>
        </div>

        <!-- Error message -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <!-- Success message -->
        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="btn-secondary">
          {{ t('configModal.cancel') || '取消' }}
        </button>
        <button @click="saveConfig" :disabled="saving" class="btn-primary">
          {{ saving ? (t('configModal.saving') || '保存中...') : (t('configModal.save') || '保存') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from '../i18n/index.js'
import { configAPI } from '../api/config.js'

const { t } = useI18n()

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'updated'])

// State
const formData = ref({
  api_key: '',
  api_base: '',
  iteration_rounds: 3
})

const originalData = ref({})
const showApiKey = ref(false)
const saving = ref(false)
const error = ref('')
const successMessage = ref('')

// Load config when modal opens
watch(() => props.show, async (newVal) => {
  if (newVal) {
    await loadConfig()
  } else {
    // Reset messages when closing
    error.value = ''
    successMessage.value = ''
  }
})

// Load current configuration
async function loadConfig() {
  try {
    const config = await configAPI.getConfig()
    formData.value = {
      api_key: config.api_key || '',
      api_base: config.api_base || 'https://api.openai.com/v1',
      iteration_rounds: config.iteration_rounds || 3
    }
    originalData.value = { ...formData.value }
    error.value = ''
  } catch (err) {
    console.error('Failed to load config:', err)
    error.value = 'Failed to load configuration'
  }
}

// Save configuration
async function saveConfig() {
  saving.value = true
  error.value = ''
  successMessage.value = ''

  try {
    // Only send changed fields
    const updates = {}
    if (formData.value.api_key !== originalData.value.api_key) {
      updates.api_key = formData.value.api_key
    }
    if (formData.value.api_base !== originalData.value.api_base) {
      updates.api_base = formData.value.api_base
    }
    if (formData.value.iteration_rounds !== originalData.value.iteration_rounds) {
      updates.iteration_rounds = formData.value.iteration_rounds
    }

    if (Object.keys(updates).length === 0) {
      successMessage.value = t('configModal.noChanges') || '没有修改'
      return
    }

    const result = await configAPI.updateConfig(updates)

    if (result.success) {
      successMessage.value = result.message || (t('configModal.saveSuccess') || '保存成功！')
      originalData.value = { ...formData.value }

      // Emit update event
      emit('updated')

      // Auto close after 1.5 seconds
      setTimeout(() => {
        closeModal()
      }, 1500)
    } else {
      error.value = result.message || (t('configModal.saveFailed') || '保存失败')
    }
  } catch (err) {
    console.error('Save config error:', err)
    error.value = err.detail || err.error || (t('configModal.saveFailed') || '保存失败')
  } finally {
    saving.value = false
  }
}

// Toggle API key visibility
function toggleApiKeyVisibility() {
  showApiKey.value = !showApiKey.value
}

// Copy API key to clipboard
async function copyApiKey() {
  try {
    await navigator.clipboard.writeText(formData.value.api_key)
    // Show brief success feedback
    const originalPlaceholder = formData.value.api_key
    successMessage.value = t('configModal.copied') || '已复制！'
    setTimeout(() => {
      if (successMessage.value === (t('configModal.copied') || '已复制！')) {
        successMessage.value = ''
      }
    }, 2000)
  } catch (err) {
    console.error('Copy failed:', err)
    error.value = t('configModal.copyFailed') || '复制失败'
  }
}

// Close modal
function closeModal() {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 30px;
  border-bottom: 2px solid #e0e0e0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.btn-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 24px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.modal-body {
  padding: 30px;
  overflow-y: auto;
  flex: 1;
}

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-size: 0.95rem;
}

.required {
  color: #ef4444;
  margin-left: 4px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s;
  font-family: monospace;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-with-action {
  display: flex;
  gap: 8px;
  align-items: center;
}

.input-with-action .form-input {
  flex: 1;
}

.btn-toggle,
.btn-copy-small {
  padding: 12px 16px;
  background: #f3f4f6;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 18px;
  flex-shrink: 0;
}

.btn-toggle:hover,
.btn-copy-small:hover {
  background: #e5e7eb;
  border-color: #667eea;
}

.hint-text {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #666;
  line-height: 1.4;
}

.error-message {
  padding: 12px 16px;
  background: #fee2e2;
  border: 2px solid #ef4444;
  border-radius: 8px;
  color: #dc2626;
  margin-top: 15px;
  font-weight: 500;
}

.success-message {
  padding: 12px 16px;
  background: #d1fae5;
  border: 2px solid #10b981;
  border-radius: 8px;
  color: #059669;
  margin-top: 15px;
  font-weight: 500;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 20px 30px;
  border-top: 2px solid #e0e0e0;
  background: #f9fafb;
}

.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
}

.btn-secondary:hover {
  background: #f8f9ff;
}

/* Responsive */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 20px;
  }

  .input-with-action {
    flex-wrap: wrap;
  }

  .input-with-action .form-input {
    width: 100%;
  }

  .btn-toggle,
  .btn-copy-small {
    flex: 1;
  }
}
</style>
