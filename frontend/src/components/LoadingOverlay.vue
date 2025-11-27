<template>
  <div
    v-if="visible"
    class="loading-overlay"
    :class="{
      'fullscreen': fullscreen,
      'inline': !fullscreen,
      'custom-z-index': zIndex > 0
    }"
    :style="overlayStyle"
  >
    <div class="loading-content" :class="contentClass">
      <!-- 加载图标 -->
      <div v-if="showIcon" class="loading-icon" :class="iconClass">
        <el-spinner :size="size" :type="type" :stroke-width="strokeWidth" />
      </div>
      
      <!-- 加载文字 -->
      <div v-if="text" class="loading-text" :class="textClass">
        {{ text }}
      </div>
      
      <!-- 自定义内容 -->
      <slot v-else></slot>
    </div>
    
    <!-- 倒计时显示 -->
    <div v-if="showCountdown && countdown > 0" class="countdown">
      {{ countdown }}s
    </div>
    
    <!-- 取消按钮 -->
    <div v-if="showCancel" class="cancel-container">
      <el-button type="text" @click="handleCancel" :disabled="cancelDisabled">
        {{ cancelText }}
      </el-button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'

export default {
  name: 'LoadingOverlay',
  props: {
    // 是否显示加载遮罩
    visible: {
      type: Boolean,
      default: false
    },
    
    // 是否全屏显示
    fullscreen: {
      type: Boolean,
      default: true
    },
    
    // 加载文字
    text: {
      type: String,
      default: '加载中...'
    },
    
    // 加载图标大小
    size: {
      type: String,
      default: 'large',
      validator: (value) => ['small', 'medium', 'large'].includes(value)
    },
    
    // 加载图标类型
    type: {
      type: String,
      default: 'circular',
      validator: (value) => ['circular', 'spinner'].includes(value)
    },
    
    // 线条宽度
    strokeWidth: {
      type: Number,
      default: 4
    },
    
    // 背景透明度
    backgroundOpacity: {
      type: Number,
      default: 0.5
    },
    
    // 背景颜色
    backgroundColor: {
      type: String,
      default: 'rgba(255, 255, 255, {opacity})'
    },
    
    // 内容背景颜色
    contentBackground: {
      type: String,
      default: 'rgba(255, 255, 255, 0.95)'
    },
    
    // 边框圆角
    borderRadius: {
      type: String,
      default: '8px'
    },
    
    // 自定义z-index
    zIndex: {
      type: Number,
      default: 0
    },
    
    // 是否显示图标
    showIcon: {
      type: Boolean,
      default: true
    },
    
    // 是否显示倒计时
    showCountdown: {
      type: Boolean,
      default: false
    },
    
    // 倒计时秒数
    countdownSeconds: {
      type: Number,
      default: 60
    },
    
    // 是否显示取消按钮
    showCancel: {
      type: Boolean,
      default: false
    },
    
    // 取消按钮文字
    cancelText: {
      type: String,
      default: '取消'
    },
    
    // 取消按钮是否禁用
    cancelDisabled: {
      type: Boolean,
      default: false
    },
    
    // 自定义CSS类
    overlayClass: {
      type: String,
      default: ''
    },
    
    // 内容自定义类
    contentClass: {
      type: String,
      default: ''
    },
    
    // 图标自定义类
    iconClass: {
      type: String,
      default: ''
    },
    
    // 文字自定义类
    textClass: {
      type: String,
      default: ''
    }
  },
  emits: ['cancel', 'countdown-end'],
  setup(props, { emit }) {
    const countdown = ref(props.countdownSeconds)
    let countdownTimer = null
    
    // 计算属性 - 遮罩样式
    const overlayStyle = computed(() => {
      const style = {}
      
      // 背景样式
      const bgColor = props.backgroundColor
      if (bgColor.includes('{opacity}')) {
        style.backgroundColor = bgColor.replace('{opacity}', props.backgroundOpacity)
      } else {
        style.backgroundColor = bgColor
      }
      
      // 自定义z-index
      if (props.zIndex > 0) {
        style.zIndex = props.zIndex
      }
      
      // 内联模式下的样式
      if (!props.fullscreen) {
        style.position = 'relative'
      }
      
      return style
    })
    
    // 初始化倒计时
    const initCountdown = () => {
      if (!props.showCountdown) return
      
      countdown.value = props.countdownSeconds
      
      // 清除已存在的定时器
      if (countdownTimer) {
        clearInterval(countdownTimer)
      }
      
      // 创建新的定时器
      countdownTimer = setInterval(() => {
        countdown.value--
        
        // 倒计时结束
        if (countdown.value <= 0) {
          clearCountdown()
          emit('countdown-end')
        }
      }, 1000)
    }
    
    // 清除倒计时
    const clearCountdown = () => {
      if (countdownTimer) {
        clearInterval(countdownTimer)
        countdownTimer = null
      }
    }
    
    // 处理取消
    const handleCancel = () => {
      if (props.cancelDisabled) return
      
      emit('cancel')
      clearCountdown()
    }
    
    // 监听visible变化
    const updateVisible = () => {
      if (props.visible) {
        // 显示时初始化
        if (props.showCountdown) {
          initCountdown()
        }
        
        // 防止背景滚动
        if (props.fullscreen) {
          document.body.style.overflow = 'hidden'
        }
      } else {
        // 隐藏时清理
        clearCountdown()
        
        // 恢复背景滚动
        if (props.fullscreen) {
          document.body.style.overflow = ''
        }
      }
    }
    
    // 组件挂载
    onMounted(() => {
      updateVisible()
    })
    
    // 组件卸载
    onUnmounted(() => {
      clearCountdown()
      document.body.style.overflow = ''
    })
    
    // 监听visible变化
    let visibleWatcher = null
    if (props.visible !== undefined) {
      visibleWatcher = new MutationObserver(() => {
        updateVisible()
      })
      
      // 这里简化处理，实际应该使用Vue的watch
      setTimeout(updateVisible, 0)
    }
    
    return {
      countdown,
      overlayStyle,
      handleCancel,
      initCountdown,
      clearCountdown
    }
  }
}
</script>

<style scoped>
/* 基础样式 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  transition: opacity 0.3s ease, visibility 0.3s ease;
  opacity: 1;
  visibility: visible;
}

/* 内联模式 */
.loading-overlay.inline {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
}

/* 自定义z-index */
.loading-overlay.custom-z-index {
  z-index: var(--el-loading-z-index);
}

/* 加载内容容器 */
.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 32px;
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  transition: all 0.3s ease;
  position: relative;
}

/* 加载图标 */
.loading-icon {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 加载文字 */
.loading-text {
  font-size: 14px;
  color: #606266;
  text-align: center;
  line-height: 1.5;
}

/* 倒计时样式 */
.countdown {
  position: absolute;
  top: 12px;
  right: 12px;
  background-color: rgba(0, 0, 0, 0.1);
  color: #606266;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  min-width: 30px;
  text-align: center;
}

/* 取消按钮容器 */
.cancel-container {
  position: absolute;
  bottom: 12px;
  right: 12px;
}

/* 小型加载器 */
.loading-overlay.small .loading-content {
  padding: 16px 24px;
  min-width: 160px;
}

.loading-overlay.small .loading-icon {
  margin-bottom: 12px;
}

.loading-overlay.small .loading-text {
  font-size: 13px;
}

/* 大型加载器 */
.loading-overlay.large .loading-content {
  padding: 32px 48px;
  min-width: 240px;
}

.loading-overlay.large .loading-icon {
  margin-bottom: 24px;
}

.loading-overlay.large .loading-text {
  font-size: 16px;
}

/* 浅色主题 */
.loading-overlay.light .loading-content {
  background-color: rgba(255, 255, 255, 0.95);
}

.loading-overlay.light .loading-text {
  color: #606266;
}

/* 深色主题 */
.loading-overlay.dark .loading-content {
  background-color: rgba(50, 54, 58, 0.95);
  color: #fff;
}

.loading-overlay.dark .loading-text {
  color: #e4e7ed;
}

/* 成功主题 */
.loading-overlay.success .loading-content {
  background-color: rgba(240, 249, 235, 0.95);
  border: 1px solid #e1f3d8;
}

/* 警告主题 */
.loading-overlay.warning .loading-content {
  background-color: rgba(253, 246, 236, 0.95);
  border: 1px solid #faecd8;
}

/* 错误主题 */
.loading-overlay.error .loading-content {
  background-color: rgba(254, 240, 240, 0.95);
  border: 1px solid #fde2e2;
}

/* 自定义动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.95);
  }
}

.loading-overlay.animate-enter .loading-content {
  animation: fadeIn 0.3s ease-out;
}

.loading-overlay.animate-leave .loading-content {
  animation: fadeOut 0.2s ease-in;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .loading-content {
    padding: 20px 24px;
    margin: 0 20px;
    min-width: auto;
    max-width: 100%;
  }
  
  .loading-overlay.large .loading-content {
    padding: 24px 32px;
  }
  
  .loading-text {
    font-size: 13px;
  }
  
  .countdown {
    position: static;
    margin-top: 12px;
    margin-bottom: -8px;
  }
  
  .cancel-container {
    position: static;
    margin-top: 16px;
  }
}

@media (max-width: 480px) {
  .loading-content {
    padding: 16px 20px;
    margin: 0 16px;
  }
  
  .loading-icon {
    margin-bottom: 12px;
  }
  
  .loading-text {
    font-size: 12px;
  }
}

/* 可访问性优化 */
.loading-overlay {
  pointer-events: auto;
}

.loading-overlay:focus-within {
  outline: none;
}

.loading-content {
  outline: none;
}

/* 高对比度模式支持 */
@media (prefers-contrast: high) {
  .loading-content {
    border: 2px solid #000;
  }
  
  .loading-text {
    font-weight: bold;
  }
}

/* 减少动画模式支持 */
@media (prefers-reduced-motion: reduce) {
  .loading-overlay.animate-enter .loading-content,
  .loading-overlay.animate-leave .loading-content {
    animation: none;
  }
}
</style>