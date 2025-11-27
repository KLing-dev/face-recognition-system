import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const service = axios.create({
  baseURL: '/api', // 添加baseURL设置
  timeout: 10000 // 请求超时时间
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 可以在这里添加token等认证信息
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    
    // 如果响应已经是成功的HTTP状态码(2xx)，我们尝试灵活处理不同格式的响应
    // 1. 如果有code字段，按原来的逻辑处理
    if (typeof res.code !== 'undefined') {
      if (res.code !== 0) {
        // 不在响应拦截器中显示错误消息，统一在业务逻辑中处理
        return Promise.reject(new Error(res.msg || 'Error'))
      }
      return res
    } else {
      // 2. 如果没有code字段，但HTTP状态码是200，我们假设请求成功
      // 这种情况通常发生在后端直接返回数据对象的情况
      return {
        code: 0,
        msg: 'success',
        data: res
      }
    }
  },
  error => {
    // 优化错误日志，在开发环境提供更详细的错误信息
    if (process.env.NODE_ENV === 'development') {
      console.error('API请求错误详情:', error)
      // 显示完整的请求路径，便于调试
      if (error.config) {
        console.error('请求路径:', error.config.url)
        console.error('请求方法:', error.config.method)
      }
    }
    
    // 提取更详细的错误信息
    let errorMessage = '网络请求失败，请检查网络连接'
    
    // 尝试从不同位置获取错误信息
    if (error.response) {
      // 服务器返回了错误响应
      if (error.response.data) {
        // 尝试从data中的不同字段获取错误信息
        if (typeof error.response.data === 'string') {
          errorMessage = error.response.data
        } else if (error.response.data.msg) {
          errorMessage = error.response.data.msg
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message
        } else if (error.response.data.error) {
          errorMessage = error.response.data.error
        } else if (error.response.status === 500) {
          // 对于500错误，尝试从响应文本中提取
          errorMessage = error.response.data || '服务器内部错误'
        }
      } else if (error.response.status === 404) {
        errorMessage = '请求的API接口不存在'
      }
    } else if (error.request) {
      // 请求已发送但未收到响应
      errorMessage = '服务器无响应，请稍后重试'
    } else if (error.message) {
      // 如果有错误消息，使用它
      errorMessage = error.message
    }
    
    // 为所有请求提供友好的错误提示，包括GET请求
    // 只有在开发环境下才显示GET请求的错误，避免生产环境过度干扰用户
    if (process.env.NODE_ENV === 'development' || 
        (error.config && error.config.method && error.config.method.toLowerCase() !== 'get')) {
      ElMessage.error(errorMessage)
    }
    
    // 增强error对象，添加详细错误消息和请求信息
    error.detailedMessage = errorMessage
    if (error.config) {
      error.requestInfo = {
        url: error.config.url,
        method: error.config.method,
        params: error.config.params || {},
        data: error.config.data || {}
      }
    }
    
    return Promise.reject(error)
  }
)

export default service