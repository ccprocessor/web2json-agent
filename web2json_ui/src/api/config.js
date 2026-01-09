/**
 * Config API Client
 * API配置管理
 */
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

export const configAPI = {
  /**
   * 获取当前配置
   * @returns {Promise<Object>} - 配置信息
   */
  async getConfig() {
    try {
      const response = await axios.get(`${API_BASE_URL}/config`)
      return response.data
    } catch (error) {
      throw error.response?.data || { error: error.message }
    }
  },

  /**
   * 更新配置
   * @param {Object} config - 配置信息
   * @returns {Promise<Object>} - 更新结果
   */
  async updateConfig(config) {
    try {
      const response = await axios.post(`${API_BASE_URL}/config`, config)
      return response.data
    } catch (error) {
      throw error.response?.data || { error: error.message }
    }
  }
}
