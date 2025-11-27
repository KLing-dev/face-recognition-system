<template>
  <div class="home-container">
    <!-- 项目标题和规则说明 -->
    <div class="header-section">
      <h1 class="project-title">人脸识别系统</h1>
      <div class="rule-card">
        <h3>核心规则：一人一脸一ID</h3>
        <p>每个自然人只能注册一个人脸信息，并分配唯一ID。系统通过人脸唯一性校验机制，严格防止重复注册。</p>
      </div>
    </div>

    <!-- 功能导航按钮 -->
    <div class="nav-section">
      <el-button 
        type="primary" 
        size="large" 
        class="nav-btn"
        @click="navigateTo('/register')"
      >
        <el-icon><Camera /></el-icon>
        人脸录入
      </el-button>
      <el-button 
        type="success" 
        size="large" 
        class="nav-btn"
        @click="navigateTo('/recognition')"
      >
        <el-icon><Search /></el-icon>
        人脸识别
      </el-button>
      <el-button 
        type="info" 
        size="large" 
        class="nav-btn"
        @click="navigateTo('/data-manage')"
      >
        <el-icon><Management /></el-icon>
        数据管理
      </el-button>
    </div>

    <!-- 数据统计卡片 -->
    <div class="stats-section">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon primary"><el-icon><User /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.total_users || 0 }}</div>
            <div class="stat-label">总注册数</div>
          </div>
        </div>
      </el-card>
      
      <!-- 已删除今日注册数卡片 -->
      
      <!-- 已删除有效人脸率卡片 -->
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getStatistics } from '../api/statistic'
import { User, Camera, Search, Management, Calendar, Check } from '@element-plus/icons-vue'

export default {
  name: 'Home',
  components: {
    User,
    Camera,
    Search,
    Management,
    Calendar,
    Check
  },
  setup() {
    const router = useRouter()
    const statistics = ref({
      total_users: 0,
      today_registrations: 0,
      valid_face_rate: 0
    })

    // 页面加载时获取统计数据
    onMounted(() => {
      loadStatistics()
    })

    // 加载统计信息
    const loadStatistics = async () => {
      try {
        console.log('开始获取统计数据...')
        const res = await getStatistics()
        console.log('API响应:', res)
        // 从res.data中获取数据，同时兼容之前的直接格式
        const data = res.data || res
        console.log('提取的数据:', data)
        statistics.value = {
          total_users: data.total_users || 0,
          today_registrations: data.active_today || 0,
          valid_face_rate: data.recognition_count || 0
        }
        console.log('更新后的统计数据:', statistics.value)
      } catch (error) {
        console.error('获取统计数据失败:', error)
        console.error('错误详情:', error.message)
        if (error.response) {
          console.error('响应状态:', error.response.status)
          console.error('响应数据:', error.response.data)
        }
      }
    }

    // 页面跳转
    const navigateTo = (path) => {
      router.push(path)
    }

    return {
      statistics,
      navigateTo
    }
  }
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.header-section {
  text-align: center;
  margin-bottom: 40px;
}

.project-title {
  font-size: 2.5rem;
  color: #303133;
  margin-bottom: 20px;
  font-weight: bold;
}

.rule-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  margin: 0 auto;
  max-width: 800px;
}

.rule-card h3 {
  margin-bottom: 10px;
  font-size: 1.2rem;
}

.rule-card p {
  font-size: 1rem;
  line-height: 1.6;
}

.nav-section {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.nav-btn {
  min-width: 200px;
  height: 80px;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-card {
  height: 100%;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.primary {
  background-color: #409eff;
}

.stat-icon.success {
  background-color: #67c23a;
}

.stat-icon.warning {
  background-color: #e6a23c;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  color: #909399;
  margin-top: 5px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .project-title {
    font-size: 2rem;
  }
  
  .nav-btn {
    min-width: 150px;
    height: 60px;
    font-size: 1rem;
  }
  
  .stats-section {
    grid-template-columns: 1fr;
  }
}
</style>