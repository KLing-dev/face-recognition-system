<template>
  <div class="recognition-container">
    <h2 class="page-title">人脸识别</h2>
    
    <!-- 上传区域 -->
    <el-card class="upload-card">
      <h3 class="section-title">选择识别方式</h3>
      
      <div class="upload-content">
        <!-- 左侧图像预览 -->
        <div class="image-preview">
          <div class="preview-wrapper">
          <video 
            id="recognition-video"
            v-if="showCamera && !previewImage" 
            ref="videoRef" 
            autoplay 
            playsinline
            muted
            class="preview-video"
            style="position: absolute; z-index: 1000; width: 100%; height: 100%; object-fit: cover; background-color: black; left: 0; top: 0;"
          ></video>
          <img 
            v-if="recognitionResult && recognitionResult.annotated_image" 
            :src="recognitionResult.annotated_image" 
            class="preview-image"
            alt="识别结果图像"
            style="position: relative; z-index: 1001;"
          >
          <img 
            v-else-if="previewImage || markedImage"
            :src="markedImage || previewImage" 
            class="preview-image"
            alt="待识别图像"
            @error="handleImageError"
          >
          <div v-else-if="imageLoadError" class="preview-placeholder">
            <el-icon class="placeholder-icon"><WarningFilled /></el-icon>
            <p>图像加载失败，请重新上传</p>
          </div>
          <div v-else class="preview-placeholder">
            <el-icon class="placeholder-icon"><Camera /></el-icon>
            <p>选择识别方式并开始识别</p>
          </div>
        </div>
        </div>
        
        <!-- 右侧操作区域 -->
        <div class="operation-section">
          <el-radio-group v-model="recognitionMode" class="mode-selector">
            <el-radio-button label="camera">摄像头拍照</el-radio-button>
            <el-radio-button label="upload">本地上传</el-radio-button>
          </el-radio-group>
          
          <div class="action-buttons">
            <template v-if="recognitionMode === 'camera'">
              <el-button 
                v-if="!showCamera" 
                @click="startCamera"
                type="primary"
              >
                <el-icon><VideoCamera /></el-icon> 启动摄像头
              </el-button>
              <el-button 
                v-else 
                @click="captureAndRecognize"
                type="success"
                :disabled="recognizing"
              >
                <el-icon><Camera /></el-icon> 拍照识别
              </el-button>
              <el-button 
                v-if="showCamera" 
                @click="stopCamera"
                type="danger"
              >
                <el-icon><VideoPause /></el-icon> 关闭摄像头
              </el-button>
            </template>
            
            <template v-if="recognitionMode === 'upload'">
              <el-upload
                class="upload-button"
                :show-file-list="false"
                accept="image/*"
                :http-request="handleUpload"
              >
                <el-button type="primary">
                  <el-icon><UploadFilled /></el-icon> 选择图片
                </el-button>
              </el-upload>
              
              <el-button 
                v-if="previewImage" 
                @click="uploadAndRecognize"
                type="success"
                :disabled="recognizing"
              >
                <el-icon><Search /></el-icon> 开始识别
              </el-button>
            </template>
          </div>
          
          <!-- 加载状态 -->
          <div v-if="recognizing" class="loading-container">
            <el-loading-spinner></el-loading-spinner>
            <p>正在进行人脸识别，请稍候...</p>
          </div>
          
          <!-- 识别提示 -->
          <div class="recognition-tips">
            <h4>识别提示：</h4>
            <ul>
              <li>确保光线充足，人脸清晰可见</li>
              <li>摄像头模式下，请正对摄像头</li>
              <li>上传图片请选择包含人脸的清晰照片</li>
              <li>系统会自动检测并匹配数据库中的人脸</li>
            </ul>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 结果展示区域 -->
    <div v-if="recognitionResult" class="result-section">
      <el-card class="result-card">
        <h3 class="section-title">识别结果</h3>
        
        <!-- 标注图像 -->
        <div class="annotated-image-container">
          <h4>标注图像</h4>
          <div class="image-wrapper">
            <img 
              v-if="markedImage" 
              :src="markedImage" 
              class="annotated-image"
              alt="标注后的图像"
            >
            <div v-else class="no-image">暂无标注图像</div>
          </div>
        </div>
        
        <!-- 统计卡片 -->
        <div class="stats-cards">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-number">{{ recognitionResult.total_faces || 0 }}</div>
              <div class="stat-label">总检测人数</div>
            </div>
          </el-card>
          
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-number">{{ recognitionResult.matched_count || 0 }}</div>
              <div class="stat-label">匹配成功人数</div>
            </div>
          </el-card>
          
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-number">{{ recognitionResult.unmatched_count || 0 }}</div>
              <div class="stat-label">数据库未出现人数</div>
            </div>
          </el-card>
          
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-number">{{ recognitionResult.database_unseen_count || 0 }}</div>
              <div class="stat-label">未出现在图中的数据库中的人数</div>
            </div>
          </el-card>
        </div>
        
        <!-- 匹配结果列表 -->
        <div v-if="recognitionResult.matched_faces && recognitionResult.matched_faces.length > 0" class="matched-section">
          <h4>匹配结果</h4>
          <el-table 
            :data="recognitionResult.matched_faces" 
            style="width: 100%"
            border
          >
            <el-table-column prop="name" label="用户名" width="180">
              <template #default="scope">
                <el-tag type="success">{{ scope.row.name }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="user_id" label="身份ID" width="180"></el-table-column>
            <el-table-column prop="similarity" label="相似度" width="180">
              <template #default="scope">
                <div class="similarity-content">
                  <div class="similarity-bar" :style="{ width: scope.row.similarity * 100 + '%' }"></div>
                  <span class="similarity-text">{{ (scope.row.similarity * 100).toFixed(2) }}%</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="confidence" label="置信度" width="180">
              <template #default="scope">
                <el-progress 
                  :percentage="(scope.row.confidence * 100).toFixed(1)" 
                  :color="getConfidenceColor(scope.row.confidence)"
                  :status="getConfidenceStatus(scope.row.confidence)"
                ></el-progress>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 未匹配提示 -->
        <div v-else-if="recognitionResult && recognitionResult.matched_faces && recognitionResult.matched_faces.length === 0" class="no-match">
          <el-empty description="未找到匹配的人脸" :image-size="120"></el-empty>
        </div>
        
        <!-- 调试信息区域已移除 -->
        
        <!-- 未匹配人员展示区域 -->
        <div class="unmatched-db-section">
          <h4>未匹配人员 <el-tag type="warning">数据库中存在但未出现在当前图片中</el-tag></h4>
          <el-table 
            v-if="recognitionResult && recognitionResult.database_unseen && recognitionResult.database_unseen.length > 0" 
            :data="recognitionResult.database_unseen" 
            style="width: 100%"
            border
          >
            <el-table-column prop="name" label="用户名" width="180">
              <template #default="scope">
                <el-tag type="info">{{ scope.row.name }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="user_id" label="身份ID" width="180"></el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip></el-table-column>
          </el-table>
          <div v-else-if="recognitionResult" class="no-data-tip">
            <el-empty description="数据库中的所有人员均已在当前图片中找到匹配" :image-size="100"></el-empty>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 操作按钮 -->
    <div v-if="recognitionResult" class="result-actions">
      <el-button @click="resetRecognition" type="primary">
        <el-icon><Refresh /></el-icon> 重新识别
      </el-button>
      <el-button @click="saveResult" type="success">
        <el-icon><Download /></el-icon> 保存结果
      </el-button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { recognizeByCamera, recognizeByUpload } from '../api/recognize'
import { Camera, VideoCamera, VideoPause, UploadFilled, Search, Refresh, Download, WarningFilled } from '@element-plus/icons-vue'

export default {
  name: 'Recognition',
  components: {
    Camera, VideoCamera, VideoPause, UploadFilled, Search, Refresh, Download
  },
  setup() {
    // DOM引用
    const videoRef = ref(null)
    
    // 状态管理
    const showCamera = ref(false)
    const previewImage = ref('')
    const recognitionMode = ref('camera')
    const recognizing = ref(false)
    const recognitionResult = ref(null)
    const currentStream = ref(null)
    const markedImage = ref('') // 添加markedImage变量定义
    const saveHistory = ref([]) // 添加保存历史记录
    const imageLoadError = ref(false) // 添加图像加载错误状态
    
    // 生成符合规范的身份ID（USR前缀+10位数字）
    const generateStandardUserId = (index) => {
      // 生成10位随机数字
      const randomDigits = Math.floor(1000000000 + Math.random() * 9000000000).toString();
      return `USR${randomDigits}`;
    };
    
    // Base64转Blob函数
    const base64ToBlob = (base64) => {
      const parts = base64.split(';base64,')
      const contentType = parts[0].split(':')[1]
      const raw = window.atob(parts[1])
      const rawLength = raw.length
      const uInt8Array = new Uint8Array(rawLength)
      
      for (let i = 0; i < rawLength; ++i) {
        uInt8Array[i] = raw.charCodeAt(i)
      }
      
      return new Blob([uInt8Array], { type: contentType })
    }
    
    // 获取置信度颜色
    const getConfidenceColor = (confidence) => {
      if (confidence >= 0.9) return '#67c23a'
      if (confidence >= 0.7) return '#e6a23c'
      return '#f56c6c'
    }
    
    // 获取置信度状态
    const getConfidenceStatus = (confidence) => {
      if (confidence >= 0.9) return 'success'
      if (confidence >= 0.7) return 'warning'
      return 'exception'
    }
    
    // 重置识别功能在文件下方实现
    
    // 保存识别结果功能在文件下方实现
    // 下载结果功能在文件下方实现
    

    

    

    
    // 添加图像标注功能
    const markImageWithFaces = (image, result) => {
      // 使用传入的参数或回退到当前组件状态
      const imgSrc = image || previewImage.value
      const recognitionData = result || recognitionResult.value
      
      console.log('开始标注图像，输入数据:', { imgSrc: !!imgSrc, recognitionData: !!recognitionData })
      
      // 返回Promise以确保正确的异步流程控制
      return new Promise((resolve) => {
        try {
          // 增强的输入验证
          if (!imgSrc) {
            console.warn('标注失败：缺少图像源')
            // 设置默认占位图像作为兜底
            nextTick(() => {
              markedImage.value = getPlaceholderImage()
            })
            resolve(null)
            return
          }
          
          if (!recognitionData) {
            console.warn('标注失败：缺少识别数据')
            // 仅显示原始图像作为兜底
            nextTick(() => {
              markedImage.value = imgSrc
            })
            resolve(imgSrc)
            return
          }
          
          const canvas = document.createElement('canvas')
          // 错误处理：确保canvas创建成功且支持2D上下文
          const ctx = canvas.getContext('2d')
          if (!ctx) {
            console.error('浏览器不支持Canvas 2D上下文')
            // 降级处理：使用原始图像
            nextTick(() => {
              markedImage.value = imgSrc
            })
            resolve(imgSrc)
            return
          }
          
          const img = new Image()
          img.src = imgSrc
          img.crossOrigin = 'anonymous'
          
          // 图像加载超时处理
          const imgLoadTimeout = setTimeout(() => {
            console.error('图像加载超时')
            // 降级处理：使用原始图像
            nextTick(() => {
              markedImage.value = imgSrc
            })
            resolve(imgSrc)
          }, 10000) // 10秒超时
          
          img.onload = () => {
            try {
              // 清除超时定时器
              clearTimeout(imgLoadTimeout)
              
              console.log('图像加载成功，开始绘制标注，尺寸:', img.width, 'x', img.height)
              
              // 验证图像尺寸
              if (img.width <= 0 || img.height <= 0) {
                console.warn('无效的图像尺寸')
                nextTick(() => {
                  markedImage.value = imgSrc
                })
                resolve(imgSrc)
                return
              }
              
              // 设置canvas尺寸并清空画布
              canvas.width = img.width
              canvas.height = img.height
              ctx.clearRect(0, 0, canvas.width, canvas.height)
              
              // 绘制原始图像
              ctx.drawImage(img, 0, 0)
              
              // 绘制人脸框和标签的函数 - 与后端visualize_recognition保持一致
              const drawFaceBox = (faceBox, color, label) => {
                try {
                  if (!faceBox || !Array.isArray(faceBox) || faceBox.length < 4) {
                    console.warn('人脸框数据无效:', faceBox)
                    return false
                  }
                  
                  // 兜底：过滤无效数值
                  const filteredBox = faceBox.map(val => {
                    const num = parseFloat(val)
                    return isNaN(num) ? 0 : num
                  })
                  
                  let x1, y1, width, height;
                  
                  // 处理两种不同的人脸框格式：[x1, y1, x2, y2] 或 [x, y, width, height]
                  if (filteredBox[2] > filteredBox[0] && filteredBox[3] > filteredBox[1]) {
                    // 格式2: [x1, y1, x2, y2]（后端标准格式）
                    [x1, y1, width, height] = [filteredBox[0], filteredBox[1], filteredBox[2] - filteredBox[0], filteredBox[3] - filteredBox[1]]
                  } else {
                    // 格式1: [x, y, width, height]
                    [x1, y1, width, height] = filteredBox
                  }
                  
                  // 边界检查，确保绘制在画布内
                  x1 = Math.max(0, Math.min(x1, canvas.width))
                  y1 = Math.max(0, Math.min(y1, canvas.height))
                  width = Math.max(1, Math.min(width, canvas.width - x1))
                  height = Math.max(1, Math.min(height, canvas.height - y1))
                  
                  // 绘制边框 - 设置为3px，与后端一致
                  ctx.strokeStyle = color || '#409EFF' // 添加默认颜色兜底
                  ctx.lineWidth = 3
                  ctx.strokeRect(x1, y1, width, height)
                  
                  // 计算标签背景宽度
                  try {
                    ctx.font = '14px Arial, sans-serif'
                    ctx.fontWeight = 'bold'
                    const textMetrics = ctx.measureText(label || '未知') // 添加默认标签兜底
                    const labelWidth = textMetrics.width + 20 // 左右各加10px边距
                    const labelHeight = 25
                    
                    // 确保标签不会超出画布边界
                    let labelX = x1
                    let labelY = y1 - labelHeight
                    
                    // 检查标签位置并调整
                    if (labelY < 0) {
                      labelY = y1 + height // 显示在人脸框下方
                    }
                    if (labelX + labelWidth > canvas.width) {
                      labelX = canvas.width - labelWidth
                    }
                    
                    // 绘制标签背景 - 使用半透明背景
                    ctx.fillStyle = (color || '#409EFF').includes('rgb') ? 
                      (color || '#409EFF').replace('rgb', 'rgba').replace(')', ', 0.9)') : 
                      'rgba(64, 158, 255, 0.9)'
                    ctx.fillRect(labelX, labelY, labelWidth, labelHeight)
                    
                    // 绘制标签文字
                    ctx.fillStyle = 'white'
                    ctx.textAlign = 'center'
                    ctx.fillText(label || '未知', labelX + labelWidth / 2, labelY + 18)
                  } catch (fontError) {
                    console.warn('文本渲染错误，跳过标签:', fontError)
                  }
                  
                  return true
                } catch (drawError) {
                  console.error('绘制人脸框失败:', drawError)
                  return false
                }
              }
              
              // 处理match_details数据结构（后端标准格式）
              let hasDrawnAnyFace = false
              let faceCount = 0
              
              // 添加更灵活的数据处理逻辑，支持多种后端数据格式
              const processFaceData = (faceData, index, isMatched) => {
                faceCount++
                
                try {
                  // 尝试从多种可能的字段中获取人脸框数据
                  let faceBox = null
                  
                  // 按优先级尝试不同的字段名
                  if (faceData.bbox && Array.isArray(faceData.bbox) && faceData.bbox.length >= 4) {
                    faceBox = faceData.bbox
                  } else if (faceData.face_box && Array.isArray(faceData.face_box) && faceData.face_box.length >= 4) {
                    faceBox = faceData.face_box
                  } else if (faceData.face_position) {
                    // 处理face_position对象格式
                    const pos = faceData.face_position
                    if (pos.x !== undefined && pos.y !== undefined && pos.width !== undefined && pos.height !== undefined) {
                      faceBox = [pos.x, pos.y, pos.width, pos.height]
                    }
                  } else if (faceData.position) {
                    // 处理position对象格式
                    const pos = faceData.position
                    if (pos.x !== undefined && pos.y !== undefined && pos.width !== undefined && pos.height !== undefined) {
                      faceBox = [pos.x, pos.y, pos.width, pos.height]
                    }
                  } else if (faceData.coordinates) {
                    // 处理coordinates数组格式
                    if (Array.isArray(faceData.coordinates) && faceData.coordinates.length >= 4) {
                      faceBox = faceData.coordinates
                    }
                  }
                  
                  if (faceBox && Array.isArray(faceBox) && faceBox.length >= 4) {
                    const color = isMatched ? '#409EFF' : '#F56C6C'
                    
                    // 构建标签文本，支持多种可能的字段名
                    let label = isMatched ? 
                      (faceData.matched_user || faceData.name || faceData.user || faceData.username || `用户${index + 1}`) : 
                      '非库内人员'
                    
                    // 添加相似度信息（如果存在）
                    if (isMatched) {
                      const similarity = faceData.similarity !== undefined ? faceData.similarity : 
                                       faceData.confidence !== undefined ? faceData.confidence : 0
                      
                      if (similarity > 0) {
                        try {
                          label += ` (${(similarity * 100).toFixed(1)}%)`
                        } catch (numError) {
                          console.warn('格式化相似度失败', numError)
                        }
                      }
                    }
                    
                    // 绘制人脸框，并更新状态
                    if (drawFaceBox(faceBox, color, label)) {
                      hasDrawnAnyFace = true
                    }
                  }
                } catch (processError) {
                  console.warn(`处理第${index}个人脸数据失败`, processError)
                }
              }
              
              // 处理match_details（后端主要格式）
              if (recognitionData.match_details && Array.isArray(recognitionData.match_details)) {
                console.log(`处理${recognitionData.match_details.length}个match_details人脸`)
                
                recognitionData.match_details.forEach((detail, index) => {
                  if (detail) {
                    processFaceData(detail, index, !!detail.matched_user)
                  }
                })
              }
              
              // 如果没有从match_details中处理到人脸，尝试处理其他可能的数据结构
              if (!hasDrawnAnyFace) {
                console.log('未从match_details中处理到人脸，尝试其他数据结构')
                
                // 尝试处理matched_faces（前端内部格式）
                if (recognitionData.matched_faces && Array.isArray(recognitionData.matched_faces)) {
                  console.log(`处理${recognitionData.matched_faces.length}个matched_faces人脸`)
                  recognitionData.matched_faces.forEach((face, index) => {
                    if (face) {
                      processFaceData(face, index, true)
                    }
                  })
                }
                
                // 尝试处理unmatched_faces（前端内部格式）
                if (recognitionData.unmatched_faces && Array.isArray(recognitionData.unmatched_faces)) {
                  console.log(`处理${recognitionData.unmatched_faces.length}个unmatched_faces人脸`)
                  recognitionData.unmatched_faces.forEach((face, index) => {
                    if (face) {
                      processFaceData(face, index, false)
                    }
                  })
                }
                
                // 尝试处理face_boxes（可能的格式）
                if (recognitionData.face_boxes && Array.isArray(recognitionData.face_boxes)) {
                  console.log(`处理${recognitionData.face_boxes.length}个face_boxes人脸`)
                  recognitionData.face_boxes.forEach((faceBox, index) => {
                    if (faceBox && Array.isArray(faceBox) && faceBox.length >= 4) {
                      // 尝试从matched_names获取匹配信息
                      const isMatched = recognitionData.matched_names && 
                                      recognitionData.matched_names[index] && 
                                      recognitionData.matched_names[index].name
                      
                      const faceData = { face_box: faceBox }
                      if (isMatched && recognitionData.matched_names[index]) {
                        faceData.name = recognitionData.matched_names[index].name
                        faceData.similarity = recognitionData.matched_names[index].similarity
                      }
                      
                      processFaceData(faceData, index, isMatched)
                    }
                  })
                }
              }
              
              // 生成标注图像并更新状态
              let markedImageDataUrl = null
              try {
                markedImageDataUrl = canvas.toDataURL('image/jpeg', 0.95)
              } catch (dataUrlError) {
                console.error('生成DataURL失败:', dataUrlError)
                
                // 降级处理：尝试使用更低质量或不同格式
                try {
                  markedImageDataUrl = canvas.toDataURL('image/png', 0.8)
                } catch (fallbackError) {
                  console.error('PNG格式也失败，返回原始图像')
                  markedImageDataUrl = imgSrc
                }
              }
              
              // 确保在Vue的响应式系统中正确更新
              nextTick(() => {
                try {
                  // 确保使用有效的图像URL
                  markedImage.value = markedImageDataUrl || imgSrc // 双重兜底
                  
                  // 创建新对象以触发响应式更新
                  recognitionResult.value = {
                    ...recognitionResult.value,
                    annotated_image: markedImageDataUrl
                  }
                } catch (updateError) {
                  console.error('更新状态失败:', updateError)
                }
                
                console.log('图像标注完成，已更新状态，处理了', faceCount, '个人脸，绘制了', hasDrawnAnyFace ? '人脸' : '无人脸')
              })
              
              resolve(markedImageDataUrl || imgSrc)
            } catch (error) {
              console.error('图像标注过程中出错:', error)
              // 清除超时定时器
              clearTimeout(imgLoadTimeout)
              // 降级处理：使用原始图像
              nextTick(() => {
                markedImage.value = imgSrc
              })
              resolve(imgSrc)
            }
          }
          
          img.onerror = (error) => {
            console.error('标注用图像加载失败:', error)
            // 清除超时定时器
            clearTimeout(imgLoadTimeout)
            // 降级处理：使用占位图像
            nextTick(() => {
              markedImage.value = getPlaceholderImage()
            })
            resolve(null)
          }
          
          // 添加图像加载超时保护
          img.onabort = () => {
            console.error('图像加载被中止')
            clearTimeout(imgLoadTimeout)
            nextTick(() => {
              markedImage.value = getPlaceholderImage()
            })
            resolve(null)
          }
          
          // 添加图像加载时间限制检查
          setTimeout(() => {
            if (img.complete === false && !img.naturalHeight) {
              console.warn('图像加载时间过长，尝试强制中止并使用降级方案')
              try {
                img.src = '' // 尝试中止加载
              } catch (abortError) {
                console.error('中止图像加载失败', abortError)
              }
              
              nextTick(() => {
                markedImage.value = imgSrc
              })
              resolve(imgSrc)
            }
          }, 15000) // 15秒强制检查
        } catch (outerError) {
          console.error('markImageWithFaces函数执行失败:', outerError)
          // 最外层兜底处理
          nextTick(() => {
            try {
              if (imgSrc) {
                markedImage.value = imgSrc
              } else {
                markedImage.value = getPlaceholderImage()
              }
            } catch (finalError) {
              console.error('最终兜底处理也失败', finalError)
            }
          })
          resolve(imgSrc || null)
        }
      })
    }
    
    // 处理识别结果 - 增强版
    const processRecognitionResult = (response) => {
      // 确保正确获取响应数据，处理不同的数据结构
      let resultData = null
      
      // 检查响应数据格式
      if (response && response.data) {
        // 如果response.data中还有data字段（可能是拦截器处理后的格式）
        if (response.data.data) {
          resultData = response.data.data
        } else {
          // 否则直接使用response.data
          resultData = response.data
        }
      } else {
        // 极端情况，直接使用response
        resultData = response
      }
      
      console.log('处理后的识别结果数据:', resultData)
      
      // 创建转换后的数据对象
      const transformedData = { ...resultData }
      
      // 字段映射转换 - 解决前后端数据结构不匹配问题
      // 将后端字段映射到前端期望的字段名
      if (resultData.total_count !== undefined) {
        transformedData.total_faces = resultData.total_count
      }
      
      // 直接使用后端返回的未匹配数据库用户数量，使用更严格的判断避免0值被错误覆盖
      transformedData.database_unseen_count = resultData.unmatched_count_db !== undefined ? resultData.unmatched_count_db : 0
      
      // 处理极端情况，确保不出现负数
      if (transformedData.database_unseen_count < 0) {
        console.warn('数据库未出现人数计算结果为负数，已修正')
        transformedData.database_unseen_count = 0
      }
      
      // 额外的验证，确保数据库未出现人数的一致性
      if (resultData.unseen_users && Array.isArray(resultData.unseen_users)) {
        // 如果有未出现用户详细信息，使用其数量作为额外验证
        const calculatedCount = resultData.unseen_users.length
        if (transformedData.database_unseen_count !== calculatedCount) {
          console.warn(`未匹配数据库用户数量不一致：后端提供(${transformedData.database_unseen_count}) vs 计算值(${calculatedCount})`)
          // 优先使用后端提供的值，但同时记录不一致情况
        }
      }
      
      // 处理未出现在图片中的人员信息 - 优先确保数据一致性
      let databaseUnseen = []
      
      // 1. 首先尝试从unseen_users获取详细信息
      if (resultData.unseen_users && Array.isArray(resultData.unseen_users) && resultData.unseen_users.length > 0) {
        databaseUnseen = resultData.unseen_users.map((user, index) => ({
          name: user.name || `数据库未出现用户 ${index + 1}`,
          user_id: user.user_id || user.id || generateStandardUserId(index + 1),
          age: user.age || '',
          gender: user.gender || '',
          description: user.description || '该用户未出现在当前识别结果中'
        }))
      } 
      // 2. 如果没有详细信息但有ID列表，基于ID创建用户信息
      else if (resultData.unseen_user_ids && Array.isArray(resultData.unseen_user_ids) && resultData.unseen_user_ids.length > 0) {
        databaseUnseen = resultData.unseen_user_ids.map((id, index) => ({
          name: `数据库未出现用户 ${index + 1}`,
          user_id: id,
          age: '',
          gender: '',
          description: '该用户未出现在当前识别结果中'
        }))
      }
      // 3. 如果unmatched_count_db > 0但没有任何用户数据，创建占位用户数据
      else if (transformedData.database_unseen_count > 0) {
        console.log(`数据库未出现用户数:${transformedData.database_unseen_count}，但没有用户详细数据，创建占位数据`)
        databaseUnseen = Array.from({length: transformedData.database_unseen_count}, (_, index) => ({
          name: `数据库未出现用户 ${index + 1}`,
          user_id: generateStandardUserId(index + 1),
          age: '',
          gender: '',
          description: '该用户未出现在当前识别结果中'
        }))
      }
      
      // 最终赋值，确保属性存在
      transformedData.database_unseen = databaseUnseen
      
      // 确保database_unseen_count是非负数
      if (transformedData.database_unseen_count < 0) {
        transformedData.database_unseen_count = 0
        console.log('修正database_unseen_count为0，因为计算结果为负数')
      }
      
      // 确保数据一致性：当database_unseen_count > 0但数组为空时，初始化空数组
      if (transformedData.database_unseen_count > 0 && (!transformedData.database_unseen || transformedData.database_unseen.length === 0)) {
        console.log(`数据库未出现用户数:${transformedData.database_unseen_count}，初始化空数组`)
        transformedData.database_unseen = []
      }
      
      // 处理匹配结果数据
        // 1. 首先处理total_faces和matched_count
        if (resultData.total_count !== undefined) {
          transformedData.total_faces = resultData.total_count
        }
        
        if (resultData.matched_count !== undefined) {
          transformedData.matched_count = resultData.matched_count
        }
        
        // 2. 计算unmatched_count（图片中未匹配到数据库中任何用户的人脸数量）
        // 公式：unmatched_count = total_faces - matched_count
        if (transformedData.total_faces !== undefined && transformedData.matched_count !== undefined) {
          transformedData.unmatched_count = transformedData.total_faces - transformedData.matched_count
        } else {
          transformedData.unmatched_count = 0
        }
        
        // 3. 处理match_details（如果存在）
        if (resultData.match_details) {
          console.log('处理match_details数据，长度:', resultData.match_details.length)
          transformedData.matched_faces = []
          transformedData.unmatched_faces = []
          
          // 首先尝试使用bbox字段作为人脸位置（后端标准格式）
          resultData.match_details.forEach((detail, index) => {
            // 为每个detail创建数据对象
            const faceData = {
              face_index: detail.face_index,
              similarity: detail.similarity || detail.confidence,
              confidence: detail.confidence || detail.similarity,
              // 优先使用bbox字段（后端标准格式）
              bbox: detail.bbox,
              face_box: detail.face_box,
              // 保持face_position兼容性
              face_position: null,
              // 添加原始数据引用
              _original_detail: detail
            }
            
            // 计算face_position，优先从bbox获取
            if (detail.bbox && detail.bbox.length >= 4) {
              faceData.face_position = {
                x: detail.bbox[0],
                y: detail.bbox[1],
                width: detail.bbox[2],
                height: detail.bbox[3]
              }
            } 
            // 如果没有bbox，尝试从face_box获取
            else if (detail.face_box && detail.face_box.length >= 4) {
              faceData.face_position = {
                x: detail.face_box[0],
                y: detail.face_box[1],
                width: detail.face_box[2],
                height: detail.face_box[3]
              }
            } 
            // 如果有face_position，直接使用
            else if (detail.face_position) {
              faceData.face_position = detail.face_position
            }
            
            // 处理匹配用户信息 - 只根据matched_user字段判断是否匹配
            if (detail.matched_user) {
              // 添加详细的调试信息
              console.log(`处理匹配用户 ${index + 1}:`, {
                matched_user: detail.matched_user,
                detail_keys: Object.keys(detail),
                name_from_matched_user: typeof detail.matched_user === 'object' ? detail.matched_user.name : detail.matched_user,
                user_id_from_matched_user: typeof detail.matched_user === 'object' ? detail.matched_user.user_id : null
              })
              
              // 设置用户信息，支持多种可能的字段名
              // 正确处理matched_user对象，提取其中的name属性
              faceData.name = typeof detail.matched_user === 'object' && detail.matched_user !== null ? 
                            detail.matched_user.name || detail.name || '未知用户' : 
                            detail.matched_user || detail.name || '未知用户'
              
              // 正确处理user_id，确保符合USR+8位数字的规范
              if (typeof detail.matched_user === 'object' && detail.matched_user !== null) {
                // 如果后端返回的user_id已符合规范，则直接使用；否则生成新的标准ID
                const existingUserId = detail.matched_user.user_id;
                if (existingUserId && /^USR\d{10}$/.test(existingUserId)) {
                  faceData.user_id = existingUserId;
                } else {
                  faceData.user_id = generateStandardUserId(index);
                  console.log(`为用户 ${faceData.name} 生成标准ID: ${faceData.user_id}`)
                }
              } else {
                // 对于非对象类型的matched_user，生成标准ID
                faceData.user_id = generateStandardUserId(index);
                console.log(`为非对象用户 ${faceData.name} 生成标准ID: ${faceData.user_id}`)
              }
              
              // 将匹配结果添加到matched_faces数组
              transformedData.matched_faces.push(faceData)
            } else {
              // 为未匹配的人脸添加默认名称和符合规范的ID
              if (!faceData.name || faceData.name === "未知用户") {
                faceData.name = `未识别用户 ${index + 1}`
              }
              
              // 生成符合规范的身份ID，使用USR前缀+8位数字格式
              faceData.user_id = generateStandardUserId(index + 1);
              
              // 添加调试信息
              console.log(`处理未匹配用户 ${index + 1}:`, {
                name: faceData.name,
                user_id: faceData.user_id,
                detail_keys: Object.keys(detail)
              })
              
              // 将未匹配结果添加到unmatched_faces数组
              transformedData.unmatched_faces.push(faceData)
            }
          })
          
          // 按相似度排序匹配结果
          transformedData.matched_faces.sort((a, b) => b.similarity - a.similarity)
          
          // 更新统计信息（如果match_details提供了更准确的数据）
          if (!transformedData.total_faces) {
            transformedData.total_faces = transformedData.matched_faces.length + transformedData.unmatched_faces.length
          }
          if (!transformedData.matched_count) {
            transformedData.matched_count = transformedData.matched_faces.length
          }
          if (!transformedData.unmatched_count) {
            transformedData.unmatched_count = transformedData.unmatched_faces.length
          }
          
          console.log(`处理完成，matched_faces: ${transformedData.matched_faces.length}, unmatched_faces: ${transformedData.unmatched_faces.length}`)
        } else {
          // 4. 如果没有match_details，创建基本的matched_faces和unmatched_faces数组
          transformedData.matched_faces = []
          transformedData.unmatched_faces = []
          
          // 从matched_names创建matched_faces（如果存在）
          if (resultData.matched_names && Array.isArray(resultData.matched_names)) {
            resultData.matched_names.forEach((nameInfo, index) => {
              // 确保name和user_id有效
              const name = nameInfo.name || `用户${index + 1}`
              let user_id = nameInfo.user_id
              
              // 如果user_id为空或为N/A，生成符合规范的ID
                if (!user_id || user_id === "N/A") {
                  user_id = generateStandardUserId(index + 1)
                  console.log(`为用户 ${name} 生成标准ID: ${user_id}`)
                }
              
              transformedData.matched_faces.push({
                name: name,
                user_id: user_id,
                similarity: nameInfo.similarity || 0,
                confidence: nameInfo.confidence || 0,
                face_index: nameInfo.face_index || index,
                face_position: null,
                _original_detail: nameInfo
              })
            })
          }
          
          // 不创建模拟数据，保持unmatched_faces为空数组
          
          console.log(`处理完成，matched_faces: ${transformedData.matched_faces.length}, unmatched_faces: ${transformedData.unmatched_faces.length}`)
        }
      
      // 映射其他字段
      if (resultData.matched_count !== undefined && !transformedData.matched_count) {
        transformedData.matched_count = resultData.matched_count
      }
      
      if (resultData.unmatched_count_db !== undefined && transformedData.database_unseen_count === undefined) {
        transformedData.database_unseen_count = resultData.unmatched_count_db
      }
      
      // 处理匹配到的用户列表，确保user_id正确
        if (resultData.matched_names && Array.isArray(resultData.matched_names)) {
          // 过滤掉空用户或名称
          resultData.matched_names = resultData.matched_names.filter(user => user && user.name)
          console.log(`处理后的匹配用户列表：`, resultData.matched_names)
          
          // 为匹配用户设置更有意义的user_id，而不是使用默认的"N/A"
          resultData.matched_names.forEach((user, index) => {
            // 如果后端返回的user_id为空、undefined或"N/A"，我们生成一个符合规范的ID
                if (!user.user_id || user.user_id === "N/A") {
                  user.user_id = generateStandardUserId(index + 1)
                }
          })
        }
        
        // 确保数据库中未在图片中出现的人员信息完整
        // 优先使用后端返回的unmatched_names_db字段
        if (resultData.unmatched_names_db && Array.isArray(resultData.unmatched_names_db) && resultData.unmatched_names_db.length > 0) {
          console.log(`使用后端返回的unmatched_names_db，长度：${resultData.unmatched_names_db.length}`)
          transformedData.database_unseen = resultData.unmatched_names_db.map((name, index) => ({
            name: name,  // 使用数据库中真实存在的用户名
            user_id: generateStandardUserId(index + 1),  // 为未匹配用户生成符合规范的ID
            age: '',
            gender: '',
            description: '该用户未出现在当前识别结果中'
          }))
          transformedData.database_unseen_count = transformedData.database_unseen.length
        }
      // 如果我们已经设置了database_unseen但没有设置database_unseen_count，使用其长度
      else if (transformedData.database_unseen && Array.isArray(transformedData.database_unseen) && 
          transformedData.database_unseen_count === undefined) {
        transformedData.database_unseen_count = transformedData.database_unseen.length
        console.log(`数据库未匹配人数：${transformedData.database_unseen_count}，未匹配用户列表：`, transformedData.database_unseen)
      }
      // 如果我们有database_unseen_count但没有database_unseen，创建一个基础的未出现用户列表
      else if (transformedData.database_unseen_count > 0 && !transformedData.database_unseen) {
        console.log(`根据计数创建未匹配用户列表，计数：${transformedData.database_unseen_count}`)
        transformedData.database_unseen = []
        // 从用户匹配数据中查找数据库中存在但未在当前识别结果中出现的用户
        // 这里暂时使用数据库中存在的用户作为基础，但实际应该通过额外API获取完整用户列表
        const timestamp = Date.now()
        for (let i = 1; i <= transformedData.database_unseen_count; i++) {
          transformedData.database_unseen.push({
            name: `数据库中存在的用户 ${i}`,  // 修改为更准确的描述
            user_id: generateStandardUserId(i),  // 使用标准ID生成函数
            age: '',
            gender: '',
            description: '该用户未出现在当前识别结果中'
          })
        }
        console.log('创建的未匹配用户列表：', transformedData.database_unseen)
      } else if (transformedData.database_unseen && Array.isArray(transformedData.database_unseen)) {
        console.log('已存在未匹配用户列表，长度：', transformedData.database_unseen.length)
      } else {
        console.log('未设置database_unseen和database_unseen_count，将创建空数组')
        transformedData.database_unseen = []
        transformedData.database_unseen_count = 0
      }
      
      // 确保数据库未出现在图片中的人数不为负数
      transformedData.database_unseen_count = Math.max(0, transformedData.database_unseen_count)
      
      // 更新recognitionResult并返回处理后的数据
      recognitionResult.value = transformedData
      return transformedData
    }
    
    // 统一的识别处理函数
    const performRecognition = async ({ mode, data }) => {
      // 输入验证
      if (!mode || !data) {
        ElMessage.error('识别参数不完整')
        return Promise.reject(new Error('识别参数不完整'))
      }
      
      // 重置状态
      recognizing.value = true
      recognitionResult.value = null
      markedImage.value = '' // 重置markedImage
      imageLoadError.value = false // 重置错误状态
      
      try {
        // 根据模式调用不同的API
        let result
        if (mode === 'camera') {
          // 摄像头模式：确保传递包含image属性的对象，与API期望一致
          if (!data.image || typeof data.image !== 'string') {
            throw new Error('摄像头识别需要有效的图像数据')
          }
          
          // 检查图像数据格式
          if (!data.image.startsWith('data:image/')) {
            throw new Error('图像数据格式不正确')
          }
          
          console.log('执行摄像头识别，图像数据已准备好')
          try {
            result = await recognizeByCamera({ image: data.image })
          } catch (apiError) {
            // 增强API错误处理
            console.error('摄像头识别API调用失败:', apiError)
            const errorMsg = apiError.detailedMessage || '摄像头识别请求失败'
            throw new Error(errorMsg)
          }
        } else if (mode === 'upload') {
          // 上传模式：验证FormData并使用
          if (!data || !(data instanceof FormData)) {
            throw new Error('上传模式需要有效的FormData对象')
          }
          // 检查FormData是否包含file字段
          if (!data.has('file')) {
            throw new Error('未提供图像文件')
          }
          
          console.log('执行上传识别，FormData已准备好')
          try {
            result = await recognizeByUpload(data)
          } catch (apiError) {
            // 增强API错误处理
            console.error('上传识别API调用失败:', apiError)
            const errorMsg = apiError.detailedMessage || '上传识别请求失败'
            throw new Error(errorMsg)
          }
        } else {
          throw new Error('不支持的识别模式')
        }
        
        // 验证API响应数据
        if (!result) {
          throw new Error('API返回空响应')
        }
        
        // 处理识别结果
        if (result && (result.code === 0 || result.success === true)) {
          try {
            const processedResult = processRecognitionResult(result)
            
            // 确保original_image有效
            if (previewImage.value) {
              try {
                // 调用增强版的markImageWithFaces并正确处理Promise
                console.log('开始图像标注流程')
                const markedImageResult = await markImageWithFaces(previewImage.value, processedResult)
                
                // 增强的结果处理
                if (markedImageResult) {
                  console.log('图像标注成功完成')
                  markedImage.value = markedImageResult
                  
                  // 确保在recognitionResult中更新annotated_image
                  if (recognitionResult.value) {
                    recognitionResult.value = {
                      ...recognitionResult.value,
                      annotated_image: markedImageResult
                    }
                  }
                } else {
                  console.warn('markImageWithFaces返回空结果，但可能已在函数内部更新了状态')
                  
                  // 即使返回空，也尝试使用函数内部可能设置的markedImage.value
                  if (!markedImage.value && previewImage.value) {
                    // 降级方案：如果没有标注成功，至少显示原始图像
                    console.log('使用原始图像作为降级方案')
                    markedImage.value = previewImage.value
                    ElMessage.warning('图像标注未完成，显示原始图像')
                  }
                }
              } catch (markError) {
                console.error('图像标注失败:', markError)
                // 标注失败时的降级处理
                if (previewImage.value) {
                  markedImage.value = previewImage.value
                  ElMessage.warning('图像标注过程中发生错误，显示原始图像')
                }
              }
            } else {
              console.warn('previewImage.value为空，无法进行图像标注')
            }
          } catch (processError) {
            console.error('结果处理失败:', processError)
            ElMessage.warning('识别结果处理失败，但识别已完成')
            // 即使结果处理失败，也尽量显示原始图像
            if (previewImage.value) {
              markedImage.value = previewImage.value
            }
          }
          
          return recognitionResult.value
        } else {
          // API返回错误码
          const errorMessage = result.message || '识别失败，请重试'
          throw new Error(errorMessage)
        }
      } catch (error) {
        console.error('识别过程出错:', error)
        
        // 统一错误处理
        ElMessage.error(error.message || '识别过程发生错误')
        
        // 失败状态下的兜底处理
        if (previewImage.value) {
          markedImage.value = previewImage.value
        }
        
        return Promise.reject(error)
      } finally {
        // 确保无论如何都将recognizing设置为false
        try {
          recognizing.value = false
        } catch (finallyError) {
          console.error('设置recognizing状态失败:', finallyError)
        }
      }
    }
    
    // 重置识别
    const resetRecognition = () => {
      previewImage.value = ''
      recognitionResult.value = null
      markedImage.value = ''
      imageLoadError.value = false
    }
    
    // 处理图像加载错误
    const handleImageError = () => {
      console.error('图像加载失败')
      imageLoadError.value = true
      ElMessage.warning('图像加载失败，显示占位图')
    }
    
    // 获取占位图
    const getPlaceholderImage = () => {
      // 这里可以返回一个默认的占位图base64或URL
      // 简单实现为显示占位符区域
      return null
    }
    
    // 保存结果
    const saveResult = async () => {
      try {
        if (!markedImage.value) {
          ElMessage.warning('没有可保存的标注图像')
          return
        }
        
        // 下载到本地
        downloadResultLocally()
      } catch (error) {
        console.error('保存结果失败:', error)
        ElMessage.error(`保存失败: ${error.message || '未知错误'}`)
      }
    }
    
    // 本地下载结果作为降级方案
    const downloadResultLocally = () => {
      try {
        // 构建文件名
        const timestamp = new Date().toISOString().replace(/[-:.]/g, '')
        const filename = `recognition_result_${timestamp.slice(0, 14)}.jpg`
        
        // 转换base64为Blob
        const blob = base64ToBlob(markedImage.value)
        const url = URL.createObjectURL(blob)
        
        // 创建下载链接
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        // 清理URL
        URL.revokeObjectURL(url)
        
        // 更新保存历史
        const saveRecord = {
          id: Date.now(),
          filename,
          timestamp: new Date().toLocaleString(),
          path: `本地下载`
        }
        saveHistory.value.unshift(saveRecord)
        
        ElMessage.success(`结果已保存: ${filename}`)
      } catch (error) {
        console.error('本地下载失败:', error)
        throw error
      }
    }
    
    // 启动摄像头函数
    const startCamera = async () => {
      try {
        // 先设置showCamera为true，确保视频元素被渲染
        showCamera.value = true;
        
        // 等待Vue更新DOM
        await nextTick();
        
        console.log('开始初始化摄像头...');
        
        // 使用原生DOM获取视频元素，避免Vue引用问题
        const videoElement = document.querySelector('.preview-video') || videoRef.value;
        if (!videoElement) {
          ElMessage.error('视频元素未找到');
          console.error('视频元素未找到');
          showCamera.value = false;
          return;
        }
        
        // 清除之前的视频流
        if (currentStream.value) {
          stopCamera();
        }
        
        // 请求摄像头权限
        console.log('请求摄像头权限...');
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        });
        
        // 保存当前流
        currentStream.value = stream;
        
        // 设置视频流
        videoElement.srcObject = stream;
        
        // 确保视频元素样式正确
        videoElement.style.position = 'absolute';
        videoElement.style.zIndex = '1000';
        videoElement.style.width = '100%';
        videoElement.style.height = '100%';
        videoElement.style.objectFit = 'cover';
        videoElement.style.backgroundColor = 'black';
        videoElement.style.left = '0';
        videoElement.style.top = '0';
        
        console.log('摄像头启动成功，视频流已设置');
        ElMessage.success('摄像头已启动');
      } catch (error) {
        console.error('启动摄像头失败:', error);
        ElMessage.error('无法访问摄像头，请检查权限设置');
        showCamera.value = false;
      }
    }
    
    // 停止摄像头函数
    const stopCamera = () => {
      if (currentStream.value) {
        currentStream.value.getTracks().forEach(track => {
          track.stop()
        })
        currentStream.value = null
      }
      
      if (videoRef.value) {
        videoRef.value.srcObject = null
      }
      
      showCamera.value = false
      ElMessage.info('摄像头已关闭')
    }
    
    // 拍照并识别
    const captureAndRecognize = async () => {
      if (!videoRef.value) {
        ElMessage.warning('摄像头未初始化，请先启动摄像头')
        return
      }
      
      try {
        // 重置错误状态
        imageLoadError.value = false
        
        // 创建canvas并绘制当前视频帧
        const canvas = document.createElement('canvas')
        canvas.width = videoRef.value.videoWidth
        canvas.height = videoRef.value.videoHeight
        const ctx = canvas.getContext('2d')
        
        // 捕获视频帧
        ctx.drawImage(videoRef.value, 0, 0, canvas.width, canvas.height)
        
        // 检查是否捕获到有效图像
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        let isEmpty = true
        for (let i = 0; i < imageData.data.length; i += 4) {
          if (imageData.data[i] !== 0 || imageData.data[i+1] !== 0 || imageData.data[i+2] !== 0) {
            isEmpty = false
            break
          }
        }
        
        if (isEmpty) {
          throw new Error('未能捕获到有效图像，请调整摄像头位置')
        }
        
        // 转换为base64
        const imageDataUrl = canvas.toDataURL('image/jpeg', 0.95)
        
        // 保存预览图
        previewImage.value = imageDataUrl
        
        // 执行识别
        await performRecognition({
          mode: 'camera',
          data: { image: imageDataUrl }
        })
      } catch (error) {
        console.error('拍照或识别过程出错:', error)
        imageLoadError.value = true
        ElMessage.error(error.message || '拍照识别失败，请重试')
      }
    }
    
    // 处理文件上传
    const handleUpload = async (req) => {
      console.log('开始处理文件上传请求:', req)
      const file = req.file
      
      // 重置错误状态
      imageLoadError.value = false
      
      // 验证文件对象是否存在
      if (!file) {
        ElMessage.error('文件无效，请重新选择')
        console.error('无效的文件对象:', file)
        imageLoadError.value = true
        return
      }
      
      // 验证文件类型
      const fileType = file.type
      console.log('上传文件类型:', fileType)
      
      const isImage = fileType.startsWith('image/')
      if (!isImage) {
        ElMessage.error('请上传有效的图片文件')
        console.warn('文件类型无效:', fileType)
        imageLoadError.value = true
        return
      }
      
      // 验证文件大小 (限制10MB)
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        ElMessage.error('图片大小不能超过10MB')
        console.warn('文件大小超过限制:', file.size, 'bytes')
        imageLoadError.value = true
        return
      }
      
      // 重置上一次的识别结果
      recognitionResult.value = null
      console.log('已重置之前的识别结果')
      
      // 显示预览图
      console.log('读取文件内容并生成预览')
      const reader = new FileReader()
      reader.onload = (e) => {
        console.log('文件读取完成，设置预览图片')
        const imageData = e.target.result
        
        // 验证图片数据是否有效
        if (!imageData || imageData.length < 100) {
          console.error('无效的图片数据')
          ElMessage.error('图片数据无效，请重新选择')
          imageLoadError.value = true
          return
        }
        
        previewImage.value = imageData
        imageLoadError.value = false
        console.log('预览设置完成，previewImage存在:', !!previewImage.value)
        
        // 验证图片是否能正确加载
        const img = new Image()
        img.onload = () => {
          console.log('图片预览验证成功')
        }
        img.onerror = () => {
          console.error('图片无法加载，可能已损坏')
          ElMessage.warning('图片可能已损坏，请尝试其他图片')
          imageLoadError.value = true
        }
        img.src = imageData
      }
      reader.onerror = (error) => {
        console.error('文件读取失败:', error)
        ElMessage.error('图片读取失败，请重试')
        imageLoadError.value = true
      }
      reader.readAsDataURL(file)
      
      ElMessage.success('图片已选择，请点击开始识别')
      console.log('文件上传预处理完成')
    }
    
    // 上传图片并识别
    const uploadAndRecognize = async () => {
      if (!previewImage.value) {
        ElMessage.warning('请先选择一张图片')
        return
      }
      
      try {
        console.log('开始上传识别流程')
        
        // 将Base64图片转换为Blob
        console.log('将Base64图片转换为Blob')
        const blob = base64ToBlob(previewImage.value)
        
        if (!blob) {
          throw new Error('Base64转换为Blob失败')
        }
        
        // 创建FormData
        console.log('创建FormData并添加图片文件')
        const formData = new FormData()
        formData.append('file', blob, 'face.jpg')
        
        // 验证FormData
        if (!formData.has('file')) {
          throw new Error('FormData中未正确添加图片文件')
        }
        
        // 执行识别
        console.log('调用performRecognition执行识别')
        await performRecognition({
          mode: 'upload',
          data: formData
        })
      } catch (error) {
        console.error('上传识别失败:', error)
        ElMessage.error(`上传识别失败: ${error.message || '未知错误'}`)
        throw error
      }
    }
    
    // 组件卸载时停止摄像头
    onUnmounted(() => {
      stopCamera()
    })
    
    return {
      videoRef,
      showCamera,
      previewImage,
      recognitionMode,
      recognizing,
      recognitionResult,
      startCamera,
      stopCamera,
      captureAndRecognize,
      handleUpload,
      uploadAndRecognize,
      resetRecognition,
      saveResult,
      getConfidenceColor,
      getConfidenceStatus,
      markedImage,
      imageLoadError
    }
  }
}
</script>

<style scoped>
.recognition-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}

.upload-card {
  margin-bottom: 30px;
}

.section-title {
  margin-bottom: 20px;
  color: #606266;
}

.upload-content {
  display: flex;
  gap: 30px;
}

.image-preview {
  flex: 1;
  min-width: 500px;
}

.preview-wrapper {
      position: relative;
      width: 100%;
      height: 400px;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      overflow: hidden;
      background-color: #000;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .preview-video {
      width: 100%;
      height: 100%;
      object-fit: cover;
      position: absolute;
      top: 0;
      left: 0;
    }

    .preview-image {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.operation-section {
  width: 350px;
}

.mode-selector {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 30px;
}

.loading-container {
  text-align: center;
  padding: 20px;
  color: #606266;
}

.loading-container .el-loading-spinner {
  margin: 0 auto 10px;
}

.recognition-tips {
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 4px;
  padding: 15px;
  color: #409eff;
}

.recognition-tips h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 14px;
}

.recognition-tips ul {
  margin: 0;
  padding-left: 20px;
}

.recognition-tips li {
  margin-bottom: 5px;
  font-size: 13px;
}

.result-section {
  margin-top: 30px;
}

.result-card {
  margin-bottom: 20px;
}

.annotated-image-container {
  margin-bottom: 30px;
}

.image-wrapper {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f5f7fa;
  padding: 10px;
}

.annotated-image {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}

.no-image {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-item {
  padding: 20px;
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.matched-section, .unseen-section, .unmatched-db-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.debug-info {
  margin: 20px 0;
  padding: 15px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 6px;
  font-family: monospace;
  font-size: 14px;
}

.debug-info > div {
  margin: 5px 0;
  color: #1890ff;
}

.matched-section h4,
.unseen-section h4,
.unmatched-db-section h4 {
  margin-bottom: 15px;
  color: #606266;
}

.similarity-content {
  position: relative;
  height: 20px;
  background-color: #f0f2f5;
  border-radius: 10px;
  overflow: hidden;
}

.similarity-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background-color: #409eff;
  transition: width 0.3s;
}

.similarity-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #fff;
  font-size: 12px;
  font-weight: bold;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.5);
}

.no-match {
  text-align: center;
  padding: 40px;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}

@media (max-width: 768px) {
  .upload-content {
    flex-direction: column;
  }
  
  .image-preview {
    min-width: unset;
  }
  
  .operation-section {
    width: 100%;
  }
  
  .stats-cards {
    grid-template-columns: 1fr 1fr;
  }
}
</style>


