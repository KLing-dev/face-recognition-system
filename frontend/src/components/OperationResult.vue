<template>
  <div class="operation-result">
    <div class="result-icon" :class="iconClass">
      <el-icon v-if="type === 'success'">
        <CircleCheck />
      </el-icon>
      <el-icon v-else-if="type === 'error'">
        <CircleClose />
      </el-icon>
      <el-icon v-else-if="type === 'warning'">
        <WarningFilled />
      </el-icon>
      <el-icon v-else-if="type === 'info'">
        <InfoFilled />
      </el-icon>
    </div>
    <div class="result-content">
      <h3 class="result-title" :class="titleClass">{{ title || defaultTitle }}</h3>
      <p v-if="message" class="result-message">{{ message }}</p>
      <p v-if="description" class="result-description">{{ description }}</p>
      <div v-if="fields.length > 0" class="result-fields">
        <div 
          v-for="(field, index) in fields" 
          :key="index"
          class="result-field"
        >
          <span class="field-label">{{ field.label }}:</span>
          <span class="field-value" :class="field.class">{{ field.value }}</span>
        </div>
      </div>
    </div>
    <div v-if="showActions" class="result-actions">
      <el-button 
        v-for="(action, index) in actions" 
        :key="index"
        :type="action.type || 'default'"
        :size="action.size || 'default'"
        :loading="action.loading"
        :disabled="action.disabled"
        @click="action.handler"
      >
        <el-icon v-if="action.icon">{{ action.icon }}</el-icon>
        {{ action.text }}
      </el-button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import {
  CircleCheck,
  CircleClose,
  WarningFilled,
  InfoFilled
} from '@element-plus/icons-vue'

export default {
  name: 'OperationResult',
  components: {
    CircleCheck,
    CircleClose,
    WarningFilled,
    InfoFilled
  },
  props: {
    // 结果类型：success, error, warning, info
    type: {
      type: String,
      default: 'success',
      validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
    },
    // 主标题
    title: {
      type: String,
      default: ''
    },
    // 消息内容
    message: {
      type: String,
      default: ''
    },
    // 描述信息
    description: {
      type: String,
      default: ''
    },
    // 字段列表，用于显示键值对信息
    fields: {
      type: Array,
      default: () => []
    },
    // 操作按钮列表
    actions: {
      type: Array,
      default: () => []
    },
    // 是否显示操作按钮
    showActions: {
      type: Boolean,
      default: true
    },
    // 是否显示图标
    showIcon: {
      type: Boolean,
      default: true
    }
  },
  setup(props) {
    // 计算默认标题
    const defaultTitle = computed(() => {
      const titles = {
        success: '操作成功',
        error: '操作失败',
        warning: '警告',
        info: '提示'
      }
      return titles[props.type]
    })
    
    // 计算图标样式类
    const iconClass = computed(() => {
      const classes = [`result-icon-${props.type}`]
      if (!props.showIcon) {
        classes.push('result-icon-hidden')
      }
      return classes
    })
    
    // 计算标题样式类
    const titleClass = computed(() => {
      return `result-title-${props.type}`
    })
    
    return {
      defaultTitle,
      iconClass,
      titleClass
    }
  }
}
</script>

<style scoped>
.operation-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 40px 20px;
  min-height: 200px;
}

.result-icon {
  font-size: 48px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.result-icon-success {
  color: #67c23a;
}

.result-icon-error {
  color: #f56c6c;
}

.result-icon-warning {
  color: #e6a23c;
}

.result-icon-info {
  color: #909399;
}

.result-icon-hidden {
  display: none;
}

.result-content {
  max-width: 600px;
  width: 100%;
}

.result-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 10px;
  transition: color 0.3s ease;
}

.result-title-success {
  color: #67c23a;
}

.result-title-error {
  color: #f56c6c;
}

.result-title-warning {
  color: #e6a23c;
}

.result-title-info {
  color: #909399;
}

.result-message {
  font-size: 16px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.6;
}

.result-description {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
  line-height: 1.5;
}

.result-fields {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 16px;
  margin: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.result-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.result-field:last-child {
  border-bottom: none;
}

.field-label {
  font-weight: 500;
  color: #303133;
  min-width: 80px;
  text-align: right;
  margin-right: 16px;
}

.field-value {
  color: #606266;
  flex: 1;
  text-align: left;
  word-break: break-all;
}

.result-actions {
  margin-top: 30px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .operation-result {
    padding: 30px 15px;
  }
  
  .result-icon {
    font-size: 36px;
    margin-bottom: 15px;
  }
  
  .result-title {
    font-size: 18px;
  }
  
  .result-message {
    font-size: 14px;
  }
  
  .result-fields {
    padding: 12px;
  }
  
  .result-field {
    flex-direction: column;
    align-items: flex-start;
    padding: 6px 0;
  }
  
  .field-label {
    text-align: left;
    margin-right: 0;
    margin-bottom: 4px;
  }
  
  .field-value {
    text-align: left;
  }
  
  .result-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .result-actions .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .operation-result {
    padding: 20px 10px;
  }
  
  .result-icon {
    font-size: 28px;
  }
  
  .result-title {
    font-size: 16px;
  }
  
  .result-content {
    max-width: 100%;
  }
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.operation-result {
  animation: fadeIn 0.3s ease-out;
}

.result-icon {
  animation: scaleIn 0.4s ease-out;
}

/* 自定义主题 */
:deep(.el-button) {
  transition: all 0.3s ease;
}

:deep(.el-button:hover:not(:disabled)) {
  transform: translateY(-1px);
}

:deep(.el-button:active:not(:disabled)) {
  transform: translateY(0);
}
</style>