<template>
  <div class="app-container">
    <header class="header">
      <button @click="toggleLocale" class="language-toggle" :title="locale === 'zh-CN' ? 'Switch to English' : '切换到中文'">
        {{ locale === 'zh-CN' ? '🌐 EN' : '🌐 中文' }}
      </button>
      <h1>{{ t('header.title') }}</h1>
      <p>{{ t('header.subtitle') }}</p>
    </header>

    <main class="main-content">
      <!-- Parser Generation -->
      <ParserTab />
    </main>
  </div>
</template>

<script setup>
import { useI18n } from './i18n/index.js'
import ParserTab from './components/ParserTab.vue'

// i18n
const { locale, t, toggleLocale } = useI18n()
</script>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  position: relative;
  text-align: center;
  color: white;
  margin-bottom: 30px;
  padding: 40px 0;
}

.language-toggle {
  position: absolute;
  top: 20px;
  right: 20px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s;
  backdrop-filter: blur(10px);
}

.language-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.8);
  transform: scale(1.05);
}

.header h1 {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.header p {
  font-size: 1.2rem;
  opacity: 0.9;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

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
}

.tab-button.active {
  background: #667eea;
  color: white;
}

.tab-button:hover:not(.active) {
  background: #f0f0f0;
}

/* File Upload */
.input-section {
  margin-top: 10px;
}

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

.file-list {
  margin-top: 15px;
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

/* HTML & URL Lists */
.html-list,
.url-list {
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

.html-header,
.url-item {
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

.url-item {
  gap: 10px;
}

.url-input {
  flex: 1;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.url-input:focus {
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

/* Buttons */
.btn-add,
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

.btn-add:hover,
.btn-add-small:hover {
  background: #059669;
}

.btn-remove,
.btn-remove-small {
  width: 40px;
  height: 40px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  transition: background 0.3s;
}

.btn-remove:hover,
.btn-remove-small:hover {
  background: #dc2626;
}

.btn-remove-small {
  width: 32px;
  height: 32px;
  font-size: 16px;
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

.info-message {
  color: #3b82f6;
  margin-top: 15px;
  padding: 12px;
  background: #dbeafe;
  border-radius: 8px;
  text-align: center;
}

.success-message {
  color: #10b981;
  padding: 12px;
  background: #d1fae5;
  border-radius: 8px;
  margin-bottom: 20px;
  font-weight: 500;
}

/* Results */
.results-section {
  background: #f0fdf4;
  border: 2px solid #10b981;
}

.result-item {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.result-item:last-child {
  margin-bottom: 0;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.result-header h3 {
  font-size: 1.2rem;
  color: #333;
  margin: 0;
}

.result-desc {
  color: #666;
  font-size: 0.9rem;
}

.result-xpath {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.result-xpath code {
  flex: 1;
  padding: 15px;
  background: #f3f4f6;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  word-break: break-all;
}

.btn-copy {
  padding: 10px 15px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  transition: background 0.3s;
  flex-shrink: 0;
}

.btn-copy:hover {
  background: #5568d3;
}

.result-samples {
  padding: 15px;
  background: #fef3c7;
  border-radius: 8px;
  border-left: 4px solid #f59e0b;
}

.result-samples strong {
  color: #92400e;
  display: block;
  margin-bottom: 10px;
}

.result-samples ul {
  margin: 0;
  padding-left: 20px;
  color: #78350f;
}

.result-samples li {
  margin: 5px 0;
}

.more-samples {
  font-style: italic;
  color: #a16207;
}

/* Responsive */
@media (max-width: 768px) {
  .field-row {
    grid-template-columns: 1fr;
  }

  .btn-remove {
    width: 100%;
  }

  .header h1 {
    font-size: 2rem;
  }

  .language-toggle {
    top: 10px;
    right: 10px;
    padding: 8px 16px;
    font-size: 12px;
  }

  .input-tabs {
    flex-direction: column;
  }
}
</style>
