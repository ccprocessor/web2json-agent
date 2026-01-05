/**
 * Parser API Client
 * 完整解析器生成API调用
 */
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

export const parserAPI = {
  /**
   * 创建解析器生成任务
   * @param {Object} params - 请求参数
   * @returns {Promise<Object>} - 包含task_id和websocket_url
   */
  async generate(params) {
    try {
      const response = await axios.post(`${API_BASE_URL}/parser/generate`, params)
      return response.data
    } catch (error) {
      throw error.response?.data || { error: error.message }
    }
  },

  /**
   * 查询任务状态
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} - 任务状态
   */
  async getStatus(taskId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/parser/status/${taskId}`)
      return response.data
    } catch (error) {
      throw error.response?.data || { error: error.message }
    }
  },

  /**
   * 取消任务
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} - 取消结果
   */
  async cancel(taskId) {
    try {
      const response = await axios.post(`${API_BASE_URL}/parser/cancel/${taskId}`)
      return response.data
    } catch (error) {
      throw error.response?.data || { error: error.message }
    }
  },

  /**
   * 下载ZIP文件
   * @param {string} taskId - 任务ID
   * @returns {Promise<Blob>} - ZIP文件Blob
   */
  async downloadZip(taskId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/parser/download/${taskId}?type=zip`, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      throw error.response?.data || { error: error.message }
    }
  },

  /**
   * 下载parser.py文件
   * @param {string} taskId - 任务ID
   * @returns {Promise<Blob>} - parser.py文件Blob
   */
  async downloadParser(taskId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/parser/download/${taskId}?type=parser`, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      throw error.response?.data || { error: error.message }
    }
  },

  /**
   * 获取parser代码内容（用于预览）
   * @param {string} taskId - 任务ID
   * @returns {Promise<string>} - parser.py代码
   */
  async getParserCode(taskId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/parser/download/${taskId}?type=parser`, {
        responseType: 'text'
      })
      return response.data
    } catch (error) {
      throw error.response?.data || { error: error.message }
    }
  }
}
