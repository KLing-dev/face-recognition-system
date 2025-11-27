<template>
  <div class="face-detector">
    <div class="video-container" :class="{ 'has-face': detectedFace }">
      <!-- 摄像头预览 -->
      <video
        v-if="showCamera"
        ref="videoRef"
        :class="['video-preview', { 'loading': initializing }]"
        autoplay
        muted
        playsinline
        :width="containerWidth"
        :height="containerHeight"
      ></video>
      
      <!-- 静态图片预览 -->
      <img
        v-else-if="previewImage"
        ref="imageRef"
        :src="previewImage"
        class="image-preview"
        :width="containerWidth"
        :height="containerHeight"
        @load="handleImageLoad"
      >
      
      <!-- 空白占位符 -->
      <div v-else class="empty-preview">
        <el-icon class="empty-icon"><Camera /></el-icon>
        <p class="empty-text">{{ emptyText || '请启动摄像头或上传图片' }}</p>
      </div>
      
      <!-- 人脸框 -->
      <div
        v-if="faceBox"
        class="face-box"
        :class="faceBoxClasses"
        :style="faceBoxStyle"
      >
        <div class="face-confidence">
          置信度: {{ faceConfidence }}%
        </div>
      </div>
      
      <!-- 加载遮罩 -->
      <div v-if="initializing" class="loading-mask">
        <el-spinner size="large" />
        <p class="loading-text">{{ loadingText || '正在初始化...' }}</p>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="errorMessage" class="error-message">
        <el-icon class="error-icon"><CircleClose /></el-icon>
        <span>{{ errorMessage }}</span>
      </div>
    </div>
    
    <!-- 控制面板 -->
    <div v-if="showControls" class="controls">
      <el-button
        v-if="!isRunning"
        type="primary"
        @click="startCamera"
        :loading="initializing"
      >
        <el-icon><VideoPlay /></el-icon>
        启动摄像头
      </el-button>
      
      <el-button
        v-else
        type="danger"
        @click="stopCamera"
      >
        <el-icon><VideoPause /></el-icon>
        停止摄像头
      </el-button>
      
      <el-button
        v-if="isRunning"
        type="success"
        @click="captureImage"
        :disabled="!detectedFace || !isFaceQualityGood"
      >
        <el-icon><Camera /></el-icon>
        拍照
      </el-button>
      
      <el-upload
        v-if="allowUpload"
        class="upload-btn"
        action=""
        :auto-upload="false"
        :show-file-list="false"
        accept="image/*"
        :on-change="handleImageUpload"
      >
        <el-button type="info">
          <el-icon><Upload /></el-icon>
          上传图片
        </el-button>
      </el-upload>
      
      <el-button
        v-if="detectedFace"
        type="warning"
        @click="$emit('adjust-face', faceBox)"
      >
        <el-icon><EditPen /></el-icon>
        调整人脸区域
      </el-button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Camera,
  VideoPlay,
  VideoPause,
  Upload,
  EditPen,
  CircleClose
} from '@element-plus/icons-vue'

export default {
  name: 'FaceDetector',
  components: {
    Camera,
    VideoPlay,
    VideoPause,
    Upload,
    EditPen,
    CircleClose
  },
  props: {
    // 容器宽度
    width: {
      type: Number,
      default: 640
    },
    // 容器高度
    height: {
      type: Number,
      default: 480
    },
    // 是否自动启动摄像头
    autoStart: {
      type: Boolean,
      default: false
    },
    // 是否显示控制面板
    showControls: {
      type: Boolean,
      default: true
    },
    // 是否允许上传图片
    allowUpload: {
      type: Boolean,
      default: true
    },
    // 人脸质量阈值
    qualityThreshold: {
      type: Number,
      default: 85
    },
    // 预览图片（用于静态模式）
    previewImage: {
      type: String,
      default: ''
    },
    // 是否启用摄像头
    showCamera: {
      type: Boolean,
      default: true
    },
    // 自定义空白文本
    emptyText: {
      type: String,
      default: ''
    },
    // 自定义加载文本
    loadingText: {
      type: String,
      default: ''
    }
  },
  emits: ['capture', 'face-detected', 'adjust-face', 'error', 'initialized', 'image-loaded'],
  setup(props, { emit }) {
    // 引用
    const videoRef = ref(null)
    const imageRef = ref(null)
    let canvasRef = null
    
    // 状态
    const initializing = ref(false)
    const isRunning = ref(false)
    const detectedFace = ref(false)
    const errorMessage = ref('')
    const isProcessing = ref(false)
    
    // 人脸信息
    const faceBox = reactive({
      x: 0,
      y: 0,
      width: 0,
      height: 0
    })
    
    // 计算属性
    const containerWidth = computed(() => props.width)
    const containerHeight = computed(() => props.height)
    
    const faceConfidence = computed(() => {
      const confidence = faceBox.confidence || 0
      return Math.round(confidence * 100)
    })
    
    const isFaceQualityGood = computed(() => {
      return faceConfidence.value >= props.qualityThreshold
    })
    
    const faceBoxClasses = computed(() => {
      const classes = []
      if (faceBox.confidence) {
        if (faceBox.confidence < 0.6) {
          classes.push('low-confidence')
        } else if (faceBox.confidence < 0.85) {
          classes.push('medium-confidence')
        }
        
        if (!isFaceQualityGood.value) {
          classes.push('insufficient-quality')
        }
      }
      return classes
    })
    
    const faceBoxStyle = computed(() => {
      if (!faceBox.x && !faceBox.y) return {}
      
      return {
        left: `${faceBox.x}px`,
        top: `${faceBox.y}px`,
        width: `${faceBox.width}px`,
        height: `${faceBox.height}px`
      }
    })
    
    // 创建Canvas
    const createCanvas = () => {
      const canvas = document.createElement('canvas')
      canvas.width = props.width
      canvas.height = props.height
      canvas.style.display = 'none'
      return canvas
    }
    
    // 初始化摄像头
    const initCamera = async () => {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        errorMessage.value = '浏览器不支持摄像头访问'
        emit('error', { message: errorMessage.value })
        return false
      }
      
      initializing.value = true
      errorMessage.value = ''
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: props.width },
            height: { ideal: props.height },
            facingMode: 'user'
          }
        })
        
        const video = videoRef.value
        if (video) {
          video.srcObject = stream
          video.onloadedmetadata = () => {
            initializing.value = false
            isRunning.value = true
            emit('initialized', { success: true })
            startDetection()
          }
        }
        
        return true
      } catch (error) {
        initializing.value = false
        errorMessage.value = getErrorMessage(error)
        emit('error', { message: errorMessage.value, error })
        return false
      }
    }
    
    // 获取错误信息
    const getErrorMessage = (error) => {
      switch (error.name) {
        case 'NotAllowedError':
          return '摄像头访问被拒绝，请允许访问摄像头'
        case 'NotFoundError':
          return '未找到摄像头设备'
        case 'NotReadableError':
          return '摄像头被占用，请关闭其他使用摄像头的应用'
        case 'OverconstrainedError':
          return '摄像头参数无法满足要求'
        default:
          return '初始化摄像头失败: ' + error.message
      }
    }
    
    // 开始人脸检测
    const startDetection = () => {
      if (!canvasRef) {
        canvasRef = createCanvas()
      }
      
      const detectFrame = () => {
        if (!isRunning.value || !videoRef.value || isProcessing.value) {
          return
        }
        
        isProcessing.value = true
        
        const video = videoRef.value
        const ctx = canvasRef.getContext('2d')
        
        try {
          canvasRef.width = video.videoWidth
          canvasRef.height = video.videoHeight
          ctx.drawImage(video, 0, 0, canvasRef.width, canvasRef.height)
          
          // 模拟人脸检测（实际项目中这里应该调用后端API或前端AI库）
          simulateFaceDetection()
        } catch (error) {
          console.error('检测帧失败:', error)
        } finally {
          isProcessing.value = false
          
          // 继续下一帧检测
          if (isRunning.value) {
            requestAnimationFrame(detectFrame)
          }
        }
      }
      
      // 开始检测循环
      requestAnimationFrame(detectFrame)
    }
    
    // 模拟人脸检测（用于演示）
    const simulateFaceDetection = () => {
      // 随机生成一个人脸框（实际项目中应替换为真实的检测逻辑）
      const hasFace = Math.random() > 0.3 // 70%概率检测到人脸
      
      if (hasFace) {
        // 模拟人脸框坐标（相对于视频/图片容器）
        const centerX = props.width / 2
        const centerY = props.height / 2
        const boxSize = Math.min(props.width, props.height) * 0.3
        
        // 添加一些随机抖动
        const jitter = 20
        const confidence = 0.7 + Math.random() * 0.3 // 0.7-1.0的置信度
        
        Object.assign(faceBox, {
          x: centerX - boxSize / 2 + (Math.random() * jitter - jitter / 2),
          y: centerY - boxSize / 2 + (Math.random() * jitter - jitter / 2),
          width: boxSize,
          height: boxSize,
          confidence: confidence
        })
        
        detectedFace.value = true
        emit('face-detected', { ...faceBox })
      } else {
        // 没有检测到人脸
        detectedFace.value = false
        Object.assign(faceBox, {
          x: 0,
          y: 0,
          width: 0,
          height: 0,
          confidence: 0
        })
      }
    }
    
    // 处理图片加载
    const handleImageLoad = () => {
      if (!imageRef.value) return
      
      // 图片加载后进行人脸检测
      setTimeout(() => {
        simulateFaceDetection()
        emit('image-loaded', { success: true })
      }, 100)
    }
    
    // 拍照
    const captureImage = () => {
      if (!isRunning.value && !previewImage) {
        ElMessage.warning('请先启动摄像头或上传图片')
        return
      }
      
      if (!canvasRef) {
        canvasRef = createCanvas()
      }
      
      const ctx = canvasRef.getContext('2d')
      
      try {
        if (showCamera && videoRef.value) {
          const video = videoRef.value
          canvasRef.width = video.videoWidth
          canvasRef.height = video.videoHeight
          ctx.drawImage(video, 0, 0, canvasRef.width, canvasRef.height)
        } else if (previewImage && imageRef.value) {
          const img = imageRef.value
          canvasRef.width = img.width
          canvasRef.height = img.height
          ctx.drawImage(img, 0, 0, canvasRef.width, canvasRef.height)
        }
        
        // 获取图片数据URL
        const dataUrl = canvasRef.toDataURL('image/jpeg', 0.9)
        
        // 发送拍照事件
        emit('capture', {
          image: dataUrl,
          faceBox: detectedFace.value ? { ...faceBox } : null
        })
        
        return dataUrl
      } catch (error) {
        console.error('拍照失败:', error)
        ElMessage.error('拍照失败')
        return null
      }
    }
    
    // 开始摄像头
    const startCamera = async () => {
      await initCamera()
    }
    
    // 停止摄像头
    const stopCamera = () => {
      if (!videoRef.value || !videoRef.value.srcObject) return
      
      const stream = videoRef.value.srcObject
      const tracks = stream.getTracks()
      
      tracks.forEach(track => {
        track.stop()
      })
      
      videoRef.value.srcObject = null
      isRunning.value = false
      detectedFace.value = false
      
      // 清空人脸框
      Object.assign(faceBox, {
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        confidence: 0
      })
    }
    
    // 处理图片上传
    const handleImageUpload = (file) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        // 这里可以触发一个事件，让父组件处理图片预览
        emit('image-uploaded', { file, dataUrl: e.target.result })
      }
      reader.readAsDataURL(file.raw)
    }
    
    // 更新人脸框（外部调用）
    const updateFaceBox = (newBox) => {
      if (newBox) {
        Object.assign(faceBox, newBox)
        detectedFace.value = true
      }
    }
    
    // 组件挂载
    onMounted(() => {
      if (props.autoStart && props.showCamera) {
        initCamera()
      }
    })
    
    // 组件卸载
    onUnmounted(() => {
      stopCamera()
    })
    
    // 暴露方法给父组件
    return {
      videoRef,
      imageRef,
      initializing,
      isRunning,
      detectedFace,
      errorMessage,
      faceBox,
      faceConfidence,
      isFaceQualityGood,
      faceBoxClasses,
      faceBoxStyle,
      containerWidth,
      containerHeight,
      startCamera,
      stopCamera,
      captureImage,
      handleImageLoad,
      handleImageUpload,
      updateFaceBox
    }
  }
}
</script>

<style scoped>
.face-detector {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.video-container {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background-color: #000;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
}

.video-container.has-face {
  border-color: #67c23a;
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.2);
}

.video-preview,
.image-preview {
  display: block;
  object-fit: cover;
  width: 100%;
  height: 100%;
  background-color: #000;
}

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f5f7fa;
}

.empty-icon {
  font-size: 64px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.empty-text {
  color: #909399;
  font-size: 16px;
}

/* 人脸框样式 */
.face-box {
  position: absolute;
  border: 2px solid #67c23a;
  border-radius: 4px;
  pointer-events: none;
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.3);
  transition: all 0.3s ease;
  animation: pulse 2s infinite;
}

.face-box.low-confidence {
  border-color: #f56c6c;
  box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.3);
}

.face-box.medium-confidence {
  border-color: #e6a23c;
  box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.3);
}

.face-box.insufficient-quality {
  border-color: #e6a23c;
  animation: warning-pulse 1s infinite;
}

.face-confidence {
  position: absolute;
  top: -25px;
  left: 0;
  background-color: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

/* 加载遮罩 */
.loading-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-text {
  color: #fff;
  margin-top: 16px;
  font-size: 14px;
}

/* 错误消息 */
.error-message {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(245, 108, 108, 0.9);
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 10;
  max-width: 80%;
}

.error-icon {
  font-size: 16px;
}

/* 控制面板 */
.controls {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

.upload-btn {
  display: inline-block;
}

/* 动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@keyframes warning-pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 4px rgba(230, 162, 60, 0.4);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .error-message {
    font-size: 12px;
    padding: 6px 12px;
  }
  
  .face-confidence {
    font-size: 10px;
  }
}
</style>