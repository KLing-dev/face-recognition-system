import request from './request'

/**
 * 摄像头拍照识别
 * @param {Object} data - 识别数据
 * @param {string} data.image - base64编码的图像
 * @returns {Promise}
 */
export const recognizeByCamera = (data) => {
  return request({
    url: '/recognize/camera',
    method: 'post',
    data
  })
}

/**
 * 本地照片上传识别
 * @param {FormData} formData - 表单数据
 * @returns {Promise}
 */
export const recognizeByUpload = (formData) => {
  return request({
    url: '/recognize/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export default {
  recognizeByCamera,
  recognizeByUpload
}