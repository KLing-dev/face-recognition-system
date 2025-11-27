import request from './request'

/**
 * 删除单个用户
 * @param {Object} data - 删除数据
 * @param {string} data.user_id - 用户ID
 * @returns {Promise}
 */
export const deleteSingleUser = (data) => {
  return request({
    url: '/delete/single',
    method: 'post',
    data
  })
}

/**
 * 批量删除用户
 * @param {Object} data - 删除数据
 * @param {Array<string>} data.user_ids - 用户ID数组
 * @returns {Promise}
 */
export const deleteBatchUsers = (data) => {
  return request({
    url: '/delete/batch',
    method: 'post',
    data
  })
}

export default {
  deleteSingleUser,
  deleteBatchUsers
}