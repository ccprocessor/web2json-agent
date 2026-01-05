import axios from 'axios'

const API_BASE_URL = '/api'

export const xpathAPI = {
  /**
   * 生成XPath
   * @param {Object} params
   * @param {string} params.html_content - HTML内容（与url二选一）
   * @param {string} params.url - URL（与html_content二选一）
   * @param {Array} params.fields - 字段列表 [{name, description, field_type}]
   */
  async generate(params) {
    try {
      const response = await axios.post(`${API_BASE_URL}/xpath/generate`, params)
      return response.data
    } catch (error) {
      console.error('Generate XPath error:', error)
      throw error.response?.data || error.message
    }
  }
}
