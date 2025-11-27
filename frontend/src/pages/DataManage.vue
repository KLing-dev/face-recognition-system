<template>
  <div class="data-manage-container">
    <h2 class="page-title">数据管理</h2>
    
    <!-- 统计卡片区域 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-item">
          <div class="stat-number">{{ statistics.total_users || 0 }}</div>
          <div class="stat-label">总注册数</div>
        </div>
      </el-card>
      <!-- 已删除今日注册数和有效人脸率卡片 -->
    </div>
    
    <!-- 查询区域 -->
    <el-card class="search-card">
      <div class="search-content">
        <el-input
          v-model="searchQuery"
          placeholder="请输入身份ID进行查询（支持模糊查询）"
          clearable
          prefix-icon="Search"
          style="width: 400px; margin-right: 10px"
        ></el-input>
        <el-button 
          type="primary" 
          @click="queryUsers"
          :loading="loading"
        >
          <el-icon><Search /></el-icon> 查询
        </el-button>
        <el-button 
          @click="clearQuery"
          :loading="loading"
        >
          <el-icon><Refresh /></el-icon> 清空查询
        </el-button>
      </div>
    </el-card>
    
    <!-- 数据列表区域 -->
    <el-card class="table-card">
      <div class="table-header">
        <h3>用户数据列表</h3>
        <el-button 
          type="danger" 
          @click="batchDelete"
          :disabled="!selectedRows.length || deleting"
          :loading="deleting"
        >
          <el-icon><Delete /></el-icon> 批量删除
          <span v-if="selectedRows.length" class="selected-count">({{ selectedRows.length }})</span>
        </el-button>
      </div>
      
      <el-table
        v-loading="loading"
        :data="userList"
        style="width: 100%"
        border
        @selection-change="handleSelectionChange"
        @row-click="handleRowClick"
      >
        <el-table-column
          type="selection"
          width="55"
          :selectable="(row) => !row.is_deleted"
        ></el-table-column>
        <el-table-column
          prop="user_id"
          label="身份ID"
          width="200"
          show-overflow-tooltip
        ></el-table-column>
        <el-table-column
          prop="name"
          label="用户名"
          width="150"
        >
          <template #default="scope">
            <el-tag>{{ scope.row.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="创建时间"
          width="200"
          :formatter="dateFormat"
        ></el-table-column>
        <el-table-column
          prop="face_thumbnail"
          label="人脸缩略图"
          width="120"
        >
          <template #default="scope">
            <el-popover
              placement="top"
              title="人脸缩略图"
              width="200"
              trigger="click"
            >
              <img 
                :src="getThumbnailUrl(scope.row.face_thumbnail)" 
                style="width: 100%"
                alt="人脸缩略图"
              >
              <template #reference>
                <img 
                  :src="getThumbnailUrl(scope.row.face_thumbnail)" 
                  class="thumbnail"
                  alt="人脸"
                >
              </template>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column
          prop="status"
          label="状态"
          width="100"
        >
          <template #default="scope">
            <el-tag 
              :type="scope.row.is_deleted ? 'danger' : 'success'"
              :effect="scope.row.is_deleted ? 'dark' : 'light'"
            >
              {{ scope.row.is_deleted ? '已删除' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="120"
          fixed="right"
        >
          <template #default="scope">
            <el-button
              v-if="!scope.row.is_deleted"
              type="danger"
              text
              size="small"
              @click="deleteSingleUser(scope.row)"
              :loading="deleting"
            >
              <el-icon><Delete /></el-icon> 删除
            </el-button>
            <span v-else class="no-operation">-</span>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        ></el-pagination>
      </div>
    </el-card>
    
    <!-- 批量删除确认弹窗 -->
    <el-dialog
      v-model="showBatchDeleteDialog"
      title="确认批量删除"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="batch-delete-content">
        <p class="warning-text">
          <el-icon class="warning-icon"><Warning /></el-icon>
          确认删除选中的 <strong>{{ selectedRows.length }}</strong> 个用户数据吗？
        </p>
        <div class="id-list">
          <h4>待删除用户ID：</h4>
          <div class="id-tags">
            <el-tag 
              v-for="row in selectedRows" 
              :key="row.user_id"
              closable
              @close="removeFromSelection(row)"
            >
              {{ row.user_id }}
            </el-tag>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showBatchDeleteDialog = false">取消</el-button>
        <el-button 
          type="danger" 
          @click="confirmBatchDelete"
          :loading="deleting"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 删除结果弹窗 -->
    <el-dialog
      v-model="showDeleteResultDialog"
      title="删除结果"
      width="400px"
    >
      <div class="delete-result">
        <div class="result-icon">
          <el-icon v-if="deleteResult.success" class="success-icon"><CircleCheck /></el-icon>
          <el-icon v-else class="error-icon"><CircleClose /></el-icon>
        </div>
        <div class="result-content">
          <p class="result-title">{{ deleteResult.success ? '删除成功' : '删除失败' }}</p>
          <p v-if="deleteResult.success" class="result-info">
            成功删除 <strong>{{ deleteResult.success_count }}</strong> 条记录
          </p>
          <p v-if="deleteResult.failed_count > 0" class="result-error">
            失败 <strong>{{ deleteResult.failed_count }}</strong> 条记录
          </p>
          <p v-if="deleteResult.message" class="result-message">{{ deleteResult.message }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDeleteResultDialog = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteSingleUser as apiDeleteSingle, deleteBatchUsers as apiDeleteBatch } from '../api/delete'
import { getStatistics, getUserList } from '../api/statistic'
import { Search, Refresh, Delete, Warning, CircleCheck, CircleClose } from '@element-plus/icons-vue'

export default {
  name: 'DataManage',
  components: {
    Search, Refresh, Delete, Warning, CircleCheck, CircleClose
  },
  setup() {
    // 搜索相关
    const searchQuery = ref('')
    
    // 表格数据
    const userList = ref([])
    const selectedRows = ref([])
    const loading = ref(false)
    const deleting = ref(false)
    
    // 分页数据
    const pagination = reactive({
      currentPage: 1,
      pageSize: 10,
      total: 0
    })
    
    // 统计数据
    const statistics = reactive({
      total_users: 0,
      today_registrations: 0,
      deleted_users: 0
    })
    
    // 弹窗状态
    const showBatchDeleteDialog = ref(false)
    const showDeleteResultDialog = ref(false)
    const deleteResult = reactive({
      success: false,
      success_count: 0,
      failed_count: 0,
      message: ''
    })
    
    // 加载统计数据
    const loadStatistics = async () => {
      try {
        const response = await getStatistics()
        // 从response.data中获取数据，同时兼容之前的直接格式
        const data = response.data || response
        Object.assign(statistics, {
          total_users: data.total_users || 0,
          today_registrations: data.today_registered || data.today_registrations || 0,
          deleted_users: data.total_deleted || data.deleted_users || 0
        })
      } catch (error) {
        ElMessage.error('加载统计数据失败')
        console.error('Load statistics error:', error)
      }
    }
    
    // 加载用户列表
    const loadUserList = async (resetPage = false) => {
      if (resetPage) {
        pagination.currentPage = 1
      }
      
      loading.value = true
      
      try {
        const params = {
          page: pagination.currentPage,
          page_size: pagination.pageSize
        }
        
        if (searchQuery.value) {
          params.user_id = searchQuery.value
        }
        
        const response = await getUserList(params)
        const data = response.data || response
        userList.value = data.users || []
        pagination.total = data.total || 0
      } catch (error) {
        console.error('获取用户列表失败:', error)
        ElMessage.error('加载用户列表失败')
      } finally {
        loading.value = false
      }
    }
    
    // 查询用户
    const queryUsers = () => {
      loadUserList(true)
    }
    
    // 清空查询
    const clearQuery = () => {
      searchQuery.value = ''
      loadUserList(true)
    }
    
    // 处理选择变化
    const handleSelectionChange = (selection) => {
      selectedRows.value = selection
    }
    
    // 处理行点击
    const handleRowClick = (row, column, event) => {
      // 如果点击的是复选框，不触发行的选中/取消
      if (event.target.type === 'checkbox' || event.target.className.includes('el-checkbox')) {
        return
      }
      
      // 模拟点击复选框的效果
      const $table = event.currentTarget.closest('.el-table')
      const $checkbox = $table.querySelector(`.el-table__row[data-row-key="${row.user_id}"] .el-checkbox__inner`)
      if ($checkbox) {
        $checkbox.click()
      }
    }
    
    // 处理分页大小变化
    const handleSizeChange = (size) => {
      pagination.pageSize = size
      loadUserList()
    }
    
    // 处理分页当前页变化
    const handleCurrentChange = (current) => {
      pagination.currentPage = current
      loadUserList()
    }
    
    // 单个删除
    const deleteSingleUser = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确认删除用户「${row.name}」（ID: ${row.user_id}）吗？`,
          '确认删除',
          {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        deleting.value = true
        const response = await apiDeleteSingle(row.user_id)
        
        // 处理删除结果
        deleteResult.success = true
        deleteResult.success_count = 1
        deleteResult.failed_count = 0
        deleteResult.message = ''
        showDeleteResultDialog.value = true
        
        // 重新加载数据
        loadUserList()
        loadStatistics()
        
        ElMessage.success('删除成功')
      } catch (error) {
        if (error !== 'cancel') {
          // 处理注册阻断等特殊错误
          const errorMessage = error.response?.data?.message || '删除失败'
          
          deleteResult.success = false
          deleteResult.success_count = 0
          deleteResult.failed_count = 1
          deleteResult.message = errorMessage
          showDeleteResultDialog.value = true
          
          ElMessage.error(errorMessage)
        }
      } finally {
        deleting.value = false
      }
    }
    
    // 批量删除
    const batchDelete = () => {
      if (!selectedRows.value.length) {
        ElMessage.warning('请选择要删除的用户')
        return
      }
      
      showBatchDeleteDialog.value = true
    }
    
    // 从选择中移除
    const removeFromSelection = (row) => {
      const index = selectedRows.value.findIndex(r => r.user_id === row.user_id)
      if (index > -1) {
        selectedRows.value.splice(index, 1)
      }
      
      // 更新表格选中状态
      const $table = document.querySelector('.el-table')
      if ($table) {
        const $checkbox = $table.querySelector(`.el-table__row[data-row-key="${row.user_id}"] .el-checkbox__input`)
        if ($checkbox && $checkbox.classList.contains('is-checked')) {
          $checkbox.click()
        }
      }
    }
    
    // 确认批量删除
    const confirmBatchDelete = async () => {
      if (!selectedRows.value.length) {
        showBatchDeleteDialog.value = false
        return
      }
      
      deleting.value = true
      showBatchDeleteDialog.value = false
      
      try {
        const userIds = selectedRows.value.map(row => row.user_id)
        const response = await apiDeleteBatch(userIds)
        
        // 处理删除结果
        deleteResult.success = true
        deleteResult.success_count = response.data.deleted || 0
        deleteResult.failed_count = response.data.failed || 0
        deleteResult.message = ''
        showDeleteResultDialog.value = true
        
        // 清空选中
        selectedRows.value = []
        
        // 重新加载数据
        loadUserList()
        loadStatistics()
        
        ElMessage.success(`成功删除 ${deleteResult.success_count} 条记录`)
      } catch (error) {
        deleteResult.success = false
        deleteResult.success_count = 0
        deleteResult.failed_count = selectedRows.value.length
        deleteResult.message = error.response?.data?.message || '批量删除失败'
        showDeleteResultDialog.value = true
        
        ElMessage.error('批量删除失败')
      } finally {
        deleting.value = false
      }
    }
    
    // 获取缩略图URL
    const getThumbnailUrl = (thumbnail) => {
      if (!thumbnail) {
        return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjEyMCIgdmlld0JveD0iMCAwIDEyMCAxMjAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iMTIwIiBmaWxsPSIjZmZmZmZmIi8+CjxwYXRoIGQ9Ik01MCAzMHY2MGg4djEyaC04di0xMmgtMjZ2LTE4aDI2ek0zNiA0MmgzMnYxMmgtMzJ6IiBmaWxsPSIjY2NjY2NjIi8+CjxwYXRoIGQ9Ik00NCA1NmgxMlY2OGgtMTJ6IiBmaWxsPSIjOGE4YTg4Ii8+CjxjaXJjbGUgY3g9Ijg4IiBjeT0iMjAiIHI9IjgiIGZpbGw9IiM4YTg4ODgiLz4KPC9zdmc+Cg=='
      }
      
      // 如果是完整的base64字符串，直接返回
      if (thumbnail.startsWith('data:image/')) {
        return thumbnail
      }
      
      // 否则返回完整的URL（假设后端返回的是相对路径）
      return `http://127.0.0.1:5000${thumbnail}`
    }
    
    // 日期格式化
    const dateFormat = (row, column, cellValue) => {
      if (!cellValue) return ''
      const date = new Date(cellValue)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    // 页面加载时初始化数据
    onMounted(() => {
      loadStatistics()
      loadUserList()
    })
    
    return {
      // 数据
      searchQuery,
      userList,
      selectedRows,
      loading,
      deleting,
      pagination,
      statistics,
      showBatchDeleteDialog,
      showDeleteResultDialog,
      deleteResult,
      
      // 方法
      queryUsers,
      clearQuery,
      handleSelectionChange,
      handleRowClick,
      handleSizeChange,
      handleCurrentChange,
      deleteSingleUser,
      batchDelete,
      removeFromSelection,
      confirmBatchDelete,
      getThumbnailUrl,
      dateFormat
    }
  }
}
</script>

<style scoped>
.data-manage-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  border-left: 4px solid #409eff;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

/* 搜索卡片 */
.search-card {
  margin-bottom: 20px;
}

.search-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* 表格卡片 */
.table-card {
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.table-header h3 {
  margin: 0;
  color: #303133;
}

.selected-count {
  color: #f56c6c;
  margin-left: 5px;
}

/* 缩略图样式 */
.thumbnail {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  object-fit: cover;
  border: 1px solid #dcdfe6;
}

/* 分页样式 */
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 批量删除弹窗 */
.batch-delete-content {
  padding: 10px 0;
}

.warning-text {
  color: #e6a23c;
  margin-bottom: 20px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.warning-icon {
  font-size: 20px;
  margin-top: 2px;
}

.id-list {
  margin-top: 20px;
}

.id-list h4 {
  margin-bottom: 10px;
  color: #303133;
  font-size: 14px;
}

.id-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 150px;
  overflow-y: auto;
}

/* 删除结果弹窗 */
.delete-result {
  text-align: center;
  padding: 20px;
}

.result-icon {
  margin-bottom: 20px;
}

.success-icon {
  font-size: 48px;
  color: #67c23a;
}

.error-icon {
  font-size: 48px;
  color: #f56c6c;
}

.result-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #303133;
}

.result-info {
  color: #67c23a;
}

.result-error {
  color: #f56c6c;
}

.result-message {
  color: #909399;
  margin-top: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .data-manage-container {
    padding: 10px;
  }
  
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .search-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-content .el-input {
    width: 100% !important;
  }
  
  .table-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .pagination-container {
    justify-content: center;
  }
}
</style>