import { ref, computed } from 'vue'
import zhCN from './zh-CN.js'
import enUS from './en-US.js'

const locales = {
  'zh-CN': zhCN,
  'en-US': enUS
}

// Default language: Chinese
const currentLocale = ref('zh-CN')

// Save to localStorage
if (typeof window !== 'undefined') {
  const savedLocale = localStorage.getItem('locale')
  if (savedLocale && locales[savedLocale]) {
    currentLocale.value = savedLocale
  }
}

export function useI18n() {
  const locale = computed(() => currentLocale.value)

  const t = (key, params = {}) => {
    const keys = key.split('.')
    let value = locales[currentLocale.value]

    for (const k of keys) {
      if (value && typeof value === 'object') {
        value = value[k]
      } else {
        return key
      }
    }

    // Replace parameters like {count}, {index}
    if (typeof value === 'string' && Object.keys(params).length > 0) {
      return value.replace(/\{(\w+)\}/g, (match, key) => {
        return params[key] !== undefined ? params[key] : match
      })
    }

    return value || key
  }

  const setLocale = (newLocale) => {
    if (locales[newLocale]) {
      currentLocale.value = newLocale
      if (typeof window !== 'undefined') {
        localStorage.setItem('locale', newLocale)
      }
    }
  }

  const toggleLocale = () => {
    const newLocale = currentLocale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
    setLocale(newLocale)
  }

  return {
    locale,
    t,
    setLocale,
    toggleLocale
  }
}
