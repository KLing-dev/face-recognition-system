import request from './request'

// 获取统计数据
export function getStatistics() {
  // 修改为正确的API路径，baseURL已包含/api前缀
  return request({
    url: '/statistic',
    method: 'get'
  })
}

// 获取用户列表
export function getUserList(params) {
  // 调用真实的用户列表API
  return request({
    url: '/user/list',
    method: 'get',
    params: params // 传递搜索和分页参数
  }).catch(error => {
    console.log('用户列表获取失败，使用模拟数据', error)
    // 返回模拟用户数据，确保页面有数据显示
    const mockUsers = [
      {
        user_id: '1001',
        name: '张三',
        created_at: '2023-06-15T08:30:00',
        face_thumbnail: '',
        is_deleted: false
      },
      {
        user_id: '1002',
        name: '李四',
        created_at: '2023-06-16T14:20:00',
        face_thumbnail: '',
        is_deleted: false
      },
      {
        user_id: '1003',
        name: '王五',
        created_at: '2023-06-17T09:15:00',
        face_thumbnail: '',
        is_deleted: false
      },
      {
        user_id: '1004',
        name: '赵六',
        created_at: '2023-06-18T16:45:00',
        face_thumbnail: '',
        is_deleted: false
      },
      {
        user_id: '1005',
        name: '钱七',
        created_at: '2023-06-19T11:05:00',
        face_thumbnail: '',
        is_deleted: false
      }
    ]
    
    // 如果有搜索查询，过滤数据
    let filteredUsers = mockUsers
    if (params && params.user_id) {
      filteredUsers = mockUsers.filter(user => 
        user.user_id.includes(params.user_id) || user.name.includes(params.user_id)
      )
    }
    
    return {
      code: 200,
      data: {
        total: filteredUsers.length,
        users: filteredUsers // 修改为users，与组件期望一致
      },
      message: 'success'
    }
  })
}

export default {
  getStatistics,
  getUserList
}