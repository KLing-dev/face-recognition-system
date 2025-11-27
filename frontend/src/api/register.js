import request from './request'

/**
 * 摄像头采集录入
 * @param {Object} data - 录入数据
 * @param {string} data.name - 用户名
 * @param {string} data.image - base64编码的图像
 * @param {string} [data.user_id] - 手动指定的用户ID（可选）
 * @param {Object} [data.face_box] - 人脸框坐标（可选）
 * @returns {Promise}
 */
export const registerByCamera = (data) => {
  return request({
    url: '/register/camera',
    method: 'post',
    data
  })
}

/**
 * 照片上传录入
 * @param {FormData} formData - 表单数据
 * @returns {Promise}
 */
export const registerByUpload = (formData) => {
  return request({
    url: '/register/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export default {
  registerByCamera,
  registerByUpload
}