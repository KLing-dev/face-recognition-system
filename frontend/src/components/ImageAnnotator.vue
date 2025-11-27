<template>
  <div class="image-annotator">
    <div class="image-container" :class="{ 'loading': loading }">
      <!-- 主图片预览 -->
      <img
        v-if="imageUrl"
        ref="imageRef"
        :src="imageUrl"
        class="main-image"
        :alt="altText"
        @load="handleImageLoad"
        @error="handleImageError"
      />
      
      <!-- 加载占位 -->
      <div v-else-if="loading" class="image-loading">
        <el-spinner size="large" />
        <p class="loading-text">{{ loadingText || '加载图片中...' }}</p>
      </div>
      
      <!-- 错误占位 -->
      <div v-else-if="error" class="image-error">
        <el-icon class="error-icon"><Picture /></el-icon>
        <p class="error-text">{{ errorText || '图片加载失败' }}</p>
      </div>
      
      <!-- 空白占位 -->
      <div v-else class="image-empty">
        <el-icon class="empty-icon"><Picture /></el-icon>
        <p class="empty-text">{{ emptyText || '暂无图片' }}</p>
      </div>
      
      <!-- 人脸标注 -->
      <div v-if="annotations && annotations.length > 0" class="annotations-layer">
        <div
          v-for="(annotation, index) in scaledAnnotations"
          :key="index"
          class="annotation-box"
          :class="getAnnotationClasses(annotation)"
          :style="getAnnotationStyle(annotation)"
          @click="handleAnnotationClick(annotation, index)"
        >
          <!-- 人脸框 -->
          <div class="annotation-border"></div>
          
          <!-- 信息标签 -->
          <div class="annotation-label" v-if="annotation.showLabel !== false">
            <div class="label-content">
              <div v-if="annotation.name" class="label-name">{{ annotation.name }}</div>
              <div v-if="annotation.id" class="label-id">{{ annotation.id }}</div>
              <div v-if="annotation.confidence" class="label-confidence">
                置信度: {{ Math.round(annotation.confidence * 100) }}%
              </div>
              <div v-if="annotation.similarity" class="label-similarity">
                相似度: {{ Math.round(annotation.similarity * 100) }}%
              </div>
            </div>
          </div>
          
          <!-- 点击提示 -->
          <div class="annotation-hint" v-if="annotation.showHint !== false">
            <el-icon class="hint-icon"><ZoomIn /></el-icon>
          </div>
        </div>
      </div>
      
      <!-- 统计信息覆盖层 -->
      <div v-if="showStatsOverlay && stats" class="stats-overlay">
        <div class="stats-card">
          <h4 class="stats-title">识别结果统计</h4>
          <div class="stats-content">
            <div v-for="(value, key) in stats" :key="key" class="stat-item">
              <span class="stat-label">{{ formatStatLabel(key) }}:</span>
              <span class="stat-value">{{ value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 人脸缩略图列表 -->
    <div v-if="showThumbnails && annotations && annotations.length > 0" class="thumbnails-container">
      <h3 class="thumbnails-title">检测到的人脸</h3>
      <div class="thumbnails-list">
        <div
          v-for="(annotation, index) in annotations"
          :key="index"
          class="thumbnail-item"
          :class="{ active: selectedAnnotation === index }"
          @click="selectAnnotation(index)"
        >
          <div class="thumbnail-image-container">
            <img
              v-if="annotation.thumbnail || imageUrl"
              :src="annotation.thumbnail || imageUrl"
              class="thumbnail-image"
              :style="getThumbnailStyle(annotation)"
              alt="人脸缩略图"
            />
          </div>
          <div class="thumbnail-info">
            <div v-if="annotation.name" class="thumbnail-name">{{ annotation.name }}</div>
            <div v-if="annotation.id" class="thumbnail-id">{{ annotation.id }}</div>
            <div v-if="annotation.confidence" class="thumbnail-confidence">
              {{ Math.round(annotation.confidence * 100) }}%
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 放大预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="previewTitle"
      :width="previewWidth"
      :close-on-click-modal="true"
      destroy-on-close
    >
      <div class="preview-container">
        <img
          v-if="selectedAnnotationData"
          :src="getPreviewImage(selectedAnnotationData)"
          class="preview-image"
          alt="放大预览"
        />
        <div v-if="selectedAnnotationData" class="preview-info">
          <template v-for="(value, key) in getPreviewInfo(selectedAnnotationData)" :key="key">
            <div v-if="value !== undefined" class="preview-info-item">
              <strong>{{ formatInfoLabel(key) }}:</strong>
              <span>{{ value }}</span>
            </div>
          </template>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, ZoomIn, ZoomOut } from '@element-plus/icons-vue'

export default {
  name: 'ImageAnnotator',
  components: {
    Picture,
    ZoomIn,
    ZoomOut
  },
  props: {
    // 图片URL
    imageUrl: {
      type: String,
      default: ''
    },
    
    // 标注数据
    annotations: {
      type: Array,
      default: () => []
    },
    
    // 是否显示缩略图
    showThumbnails: {
      type: Boolean,
      default: false
    },
    
    // 是否显示统计覆盖层
    showStatsOverlay: {
      type: Boolean,
      default: false
    },
    
    // 统计数据
    stats: {
      type: Object,
      default: () => ({})
    },
    
    // 图片加载中状态
    loading: {
      type: Boolean,
      default: false
    },
    
    // 自定义属性
    altText: {
      type: String,
      default: '标注图片'
    },
    
    // 自定义文本
    loadingText: {
      type: String,
      default: ''
    },
    errorText: {
      type: String,
      default: ''
    },
    emptyText: {
      type: String,
      default: ''
    },
    
    // 预览配置
    showPreview: {
      type: Boolean,
      default: true
    },
    previewWidth: {
      type: String,
      default: '80%'
    }
  },
  emits: ['image-load', 'image-error', 'annotation-click', 'annotation-select'],
  setup(props, { emit }) {
    // 引用
    const imageRef = ref(null)
    
    // 状态
    const error = ref(false)
    const imageDimensions = ref({ width: 0, height: 0 })
    const selectedAnnotation = ref(-1)
    const previewVisible = ref(false)
    const selectedAnnotationData = ref(null)
    const previewTitle = ref('')
    
    // 计算属性 - 缩放后的标注位置
    const scaledAnnotations = computed(() => {
      if (!props.annotations || props.annotations.length === 0) return []
      if (!imageRef.value || !imageDimensions.value.width) return props.annotations
      
      const image = imageRef.value
      const naturalWidth = image.naturalWidth || imageDimensions.value.width
      const naturalHeight = image.naturalHeight || imageDimensions.value.height
      const displayedWidth = image.clientWidth || imageDimensions.value.width
      const displayedHeight = image.clientHeight || imageDimensions.value.height
      
      // 计算缩放比例
      const scaleX = displayedWidth / naturalWidth
      const scaleY = displayedHeight / naturalHeight
      
      // 返回缩放后的标注
      return props.annotations.map(annotation => {
        if (!annotation.box) return annotation
        
        return {
          ...annotation,
          scaledBox: {
            x: annotation.box.x * scaleX,
            y: annotation.box.y * scaleY,
            width: annotation.box.width * scaleX,
            height: annotation.box.height * scaleY
          }
        }
      })
    })
    
    // 处理图片加载
    const handleImageLoad = () => {
      error.value = false
      
      if (imageRef.value) {
        imageDimensions.value = {
          width: imageRef.value.naturalWidth,
          height: imageRef.value.naturalHeight
        }
      }
      
      emit('image-load', {
        success: true,
        dimensions: imageDimensions.value
      })
    }
    
    // 处理图片错误
    const handleImageError = () => {
      error.value = true
      emit('image-error', { success: false })
    }
    
    // 获取标注样式
    const getAnnotationStyle = (annotation) => {
      const box = annotation.scaledBox || annotation.box
      if (!box) return {}
      
      return {
        left: `${box.x}px`,
        top: `${box.y}px`,
        width: `${box.width}px`,
        height: `${box.height}px`
      }
    }
    
    // 获取标注样式类
    const getAnnotationClasses = (annotation) => {
      const classes = []
      
      // 基于置信度的样式
      if (annotation.confidence) {
        if (annotation.confidence < 0.6) {
          classes.push('low-confidence')
        } else if (annotation.confidence < 0.85) {
          classes.push('medium-confidence')
        } else {
          classes.push('high-confidence')
        }
      }
      
      // 基于相似度的样式（用于识别结果）
      if (annotation.similarity) {
        if (annotation.similarity < 0.7) {
          classes.push('low-similarity')
        } else if (annotation.similarity < 0.9) {
          classes.push('medium-similarity')
        } else {
          classes.push('high-similarity')
        }
      }
      
      // 选中状态
      if (selectedAnnotation.value === annotation.index) {
        classes.push('selected')
      }
      
      return classes
    }
    
    // 处理标注点击
    const handleAnnotationClick = (annotation, index) => {
      if (!props.showPreview) return
      
      selectedAnnotationData.value = {
        ...annotation,
        index
      }
      
      previewTitle.value = annotation.name || `人脸 #${index + 1}`
      previewVisible.value = true
      
      emit('annotation-click', annotation, index)
    }
    
    // 选择标注
    const selectAnnotation = (index) => {
      selectedAnnotation.value = index
      emit('annotation-select', props.annotations[index], index)
    }
    
    // 获取预览图片
    const getPreviewImage = (annotation) => {
      // 如果有缩略图优先使用
      if (annotation.thumbnail) {
        return annotation.thumbnail
      }
      
      // 否则返回原图
      return props.imageUrl
    }
    
    // 获取预览信息
    const getPreviewInfo = (annotation) => {
      const info = {}
      
      // 基础信息
      if (annotation.name) info.name = annotation.name
      if (annotation.id) info.id = annotation.id
      if (annotation.confidence !== undefined) info.confidence = annotation.confidence
      if (annotation.similarity !== undefined) info.similarity = annotation.similarity
      
      // 位置信息
      if (annotation.box) {
        info.position = `X: ${annotation.box.x}, Y: ${annotation.box.y}`
        info.size = `${annotation.box.width}×${annotation.box.height}`
      }
      
      // 其他自定义信息
      Object.keys(annotation)
        .filter(key => !['box', 'scaledBox', 'thumbnail', 'showLabel', 'showHint'].includes(key) && !info[key])
        .forEach(key => {
          info[key] = annotation[key]
        })
      
      return info
    }
    
    // 格式化统计标签
    const formatStatLabel = (key) => {
      const labels = {
        total: '总数',
        matched: '匹配数',
        unmatched: '未匹配数',
        confidence: '平均置信度',
        similarity: '平均相似度'
      }
      
      return labels[key] || key
    }
    
    // 格式化信息标签
    const formatInfoLabel = (key) => {
      const labels = {
        name: '姓名',
        id: 'ID',
        confidence: '置信度',
        similarity: '相似度',
        position: '位置',
        size: '大小'
      }
      
      return labels[key] || key
    }
    
    // 获取缩略图样式
    const getThumbnailStyle = (annotation) => {
      // 如果有位置信息，设置裁剪
      if (annotation.box && props.imageUrl) {
        const { x, y, width, height } = annotation.box
        return {
          objectPosition: `${x}px ${y}px`,
          objectFit: 'none'
        }
      }
      return {}
    }
    
    // 监听图片变化
    watch(() => props.imageUrl, (newUrl) => {
      if (newUrl) {
        error.value = false
        selectedAnnotation.value = -1
      }
    })
    
    // 监听标注变化
    watch(() => props.annotations, () => {
      selectedAnnotation.value = -1
    }, { deep: true })
    
    return {
      imageRef,
      error,
      imageDimensions,
      selectedAnnotation,
      previewVisible,
      selectedAnnotationData,
      previewTitle,
      scaledAnnotations,
      handleImageLoad,
      handleImageError,
      getAnnotationStyle,
      getAnnotationClasses,
      handleAnnotationClick,
      selectAnnotation,
      getPreviewImage,
      getPreviewInfo,
      formatStatLabel,
      formatInfoLabel,
      getThumbnailStyle
    }
  }
}
</script>

<style scoped>
.image-annotator {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.image-container {
  position: relative;
  display: inline-block;
  border-radius: 8px;
  overflow: hidden;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
}

.main-image {
  display: block;
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  transition: opacity 0.3s ease;
}

/* 占位样式 */
.image-loading,
.image-error,
.image-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 40px 20px;
  text-align: center;
}

.loading-text,
.error-text,
.empty-text {
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}

.error-icon,
.empty-icon {
  font-size: 64px;
  color: #c0c4cc;
}

/* 标注层样式 */
.annotations-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.annotation-box {
  position: absolute;
  pointer-events: all;
  cursor: pointer;
  transition: all 0.3s ease;
  opacity: 0.9;
}

.annotation-box:hover {
  opacity: 1;
  transform: scale(1.02);
  z-index: 10;
}

.annotation-box.selected {
  opacity: 1;
  transform: scale(1.05);
  z-index: 20;
}

.annotation-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid #409eff;
  border-radius: 4px;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
  animation: annotation-pulse 2s infinite;
}

/* 置信度/相似度样式 */
.annotation-box.high-confidence .annotation-border,
.annotation-box.high-similarity .annotation-border {
  border-color: #67c23a;
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.3);
}

.annotation-box.medium-confidence .annotation-border,
.annotation-box.medium-similarity .annotation-border {
  border-color: #e6a23c;
  box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.3);
}

.annotation-box.low-confidence .annotation-border,
.annotation-box.low-similarity .annotation-border {
  border-color: #f56c6c;
  box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.3);
  animation: annotation-warning 1s infinite;
}

/* 信息标签 */
.annotation-label {
  position: absolute;
  bottom: -28px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  pointer-events: none;
}

.label-content {
  background-color: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.label-name {
  font-weight: bold;
}

.label-id {
  font-size: 11px;
  opacity: 0.9;
}

.label-confidence,
.label-similarity {
  font-size: 10px;
  opacity: 0.8;
}

/* 提示图标 */
.annotation-hint {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 24px;
  height: 24px;
  background-color: rgba(64, 158, 255, 0.9);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.annotation-box:hover .annotation-hint {
  opacity: 1;
}

/* 统计覆盖层 */
.stats-overlay {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 100;
}

.stats-card {
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  min-width: 200px;
}

.stats-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.stat-value {
  font-weight: bold;
  color: #303133;
}

/* 缩略图容器 */
.thumbnails-container {
  margin-top: 20px;
}

.thumbnails-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.thumbnails-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.thumbnail-item {
  flex: 0 0 auto;
  width: 140px;
  border: 2px solid transparent;
  border-radius: 8px;
  padding: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #f5f7fa;
}

.thumbnail-item:hover {
  border-color: #dcdfe6;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.thumbnail-item.active {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.thumbnail-image-container {
  width: 100%;
  height: 120px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
  background-color: #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-info {
  text-align: center;
}

.thumbnail-name {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
  margin-bottom: 2px;
}

.thumbnail-id {
  font-size: 12px;
  color: #909399;
  margin-bottom: 2px;
}

.thumbnail-confidence {
  font-size: 12px;
  font-weight: bold;
  color: #409eff;
}

/* 预览弹窗 */
.preview-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-image {
  max-width: 100%;
  max-height: 500px;
  margin: 0 auto;
  border-radius: 4px;
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-info-item {
  font-size: 14px;
  color: #606266;
}

/* 动画 */
@keyframes annotation-pulse {
  0%, 100% {
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.1);
  }
}

@keyframes annotation-warning {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.3);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 4px rgba(245, 108, 108, 0.4);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .annotation-label {
    display: none;
  }
  
  .thumbnails-list {
    flex-wrap: wrap;
    overflow-x: visible;
  }
  
  .thumbnail-item {
    width: calc(50% - 6px);
  }
  
  .stats-overlay {
    top: 10px;
    right: 10px;
    left: 10px;
  }
  
  .stats-card {
    min-width: auto;
  }
  
  .preview-info {
    font-size: 12px;
  }
}

/* 滚动条样式 */
.thumbnails-list::-webkit-scrollbar {
  height: 6px;
}

.thumbnails-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.thumbnails-list::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.thumbnails-list::-webkit-scrollbar-thumb:hover {
  background: #909399;
}
</style>