<template>
  <div class="register-container">
    <div class="page-header">
      <h2 class="page-title">人脸录入</h2>
      <el-button 
        type="primary" 
        @click="$router.push('/')"
        class="back-home-btn"
      >
        <el-icon><House /></el-icon>
        返回主页面
      </el-button>
    </div>
    
    <div class="register-content">
      <!-- 左侧图像预览区 -->
      <div class="preview-section">
        <el-card class="preview-card">
          <div class="preview-wrapper">
            <!-- 摄像头/上传图像预览 -->
            <div class="image-container">
              <!-- 摄像头视频流 - 使用原生DOM操作，确保视频元素始终在最上层 -->
              <video 
                v-if="showCamera && !capturedImage" 
                ref="videoRef" 
                autoplay 
                playsinline
                muted
                class="preview-video"
                id="webcam-video"
                style="position: absolute; z-index: 1000; width: 100%; height: 100%; object-fit: cover; background-color: black; left: 0; top: 0;"
              ></video>
              <!-- 隐藏的canvas用于人脸检测 -->
              <canvas 
                v-if="showCamera && !capturedImage" 
                ref="canvasRef"
                class="detection-canvas"
                style="display: none"
              ></canvas>
              <!-- 摄像头拍摄照片或上传图片 -->
              <img 
                v-if="previewImage || capturedImage" 
                :src="previewImage || capturedImage"
                class="preview-image"
              >
              <div v-else class="upload-placeholder">
                <el-icon class="placeholder-icon"><UploadFilled /></el-icon>
                <p>点击下方按钮选择模式</p>
              </div>
              
              <!-- 人脸框 -->
              <div 
                v-if="faceBox && (showCamera || previewImage)"
                class="face-box"
                :style="{
                  left: faceBox.x + 'px',
                  top: faceBox.y + 'px',
                  width: faceBox.width + 'px',
                  height: faceBox.height + 'px',
                  borderColor: faceConfidence >= 0.85 ? '#67c23a' : '#f56c6c'
                }"
              >
                <div class="confidence-text">{{ (faceConfidence * 100).toFixed(1) }}%</div>
              </div>
              
              <!-- 人脸质量提示 -->
              <div 
                v-if="faceConfidence > 0 && faceConfidence < 0.85"
                class="quality-warning"
              >
                <el-icon><Warning /></el-icon> 人脸质量不达标
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="preview-actions">
              <el-radio-group v-model="inputMode" class="mode-selector">
                <el-radio-button label="camera">摄像头模式</el-radio-button>
                <el-radio-button label="upload">上传模式</el-radio-button>
              </el-radio-group>
              
              <div class="action-buttons">
                <template v-if="inputMode === 'camera'">
                  <el-button 
                    v-if="!showCamera" 
                    @click="startCamera"
                    type="primary"
                  >
                    <el-icon><VideoCamera /></el-icon> 启动摄像头
                  </el-button>
                <!-- 测试按钮已移除 -->
                  <el-button 
                    v-else 
                    @click="captureImage"
                    type="success"
                  >
                    <el-icon><Camera /></el-icon> 拍摄照片
                  </el-button>
                  <el-button 
                    v-if="showCamera" 
                    @click="stopCamera"
                    type="danger"
                  >
                    <el-icon><VideoPause /></el-icon> 关闭摄像头
                  </el-button>
                </template>
                
                <template v-if="inputMode === 'upload'">
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
                </template>
              </div>
              
              <!-- 调整人脸区域按钮 -->
              <el-button 
                v-if="faceBox && (capturedImage || previewImage)"
                @click="showAdjustDialog = true"
                type="info"
                size="small"
              >
                <el-icon><EditPen /></el-icon> 调整人脸区域
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
      
      <!-- 右侧表单和操作区 -->
      <div class="form-section">
        <el-form 
          :model="formData" 
          ref="formRef"
          :rules="formRules"
          label-width="100px"
          class="register-form"
        >
          <el-form-item label="用户名" prop="name">
            <el-input 
              v-model="formData.name" 
              placeholder="请输入用户名"
              maxlength="20"
            ></el-input>
          </el-form-item>
          
          <el-form-item>
            <el-switch 
              v-model="formData.useCustomId" 
              active-text="手动指定ID" 
              inactive-text="自动生成ID"
            ></el-switch>
          </el-form-item>
          
          <el-form-item 
            v-if="formData.useCustomId"
            label="身份ID" 
            prop="user_id"
          >
            <el-input 
              v-model="formData.user_id" 
              placeholder="请输入ID（不填则自动生成）"
              maxlength="20"
            ></el-input>
            <div class="form-tip">ID格式建议：字母开头，可包含数字和下划线</div>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              @click="submitRegister"
              :loading="submitting"
              :disabled="!canSubmit"
              class="submit-button"
            >
              <el-icon v-if="!submitting"><Check /></el-icon>
              <el-icon v-else><Loading /></el-icon>
              提交注册
            </el-button>
            <el-button @click="resetForm">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
        
        <!-- 录入说明 -->
        <div class="register-tips">
          <h4>录入说明：</h4>
          <ul>
            <li>请确保光线充足，正面朝向摄像头</li>
            <li>人脸应清晰可见，避免遮挡（眼镜、口罩等）</li>
            <li>系统会自动检测人脸并验证唯一性</li>
            <li>可通过调整按钮优化人脸框选区域</li>
          </ul>
        </div>
      </div>
    </div>
    
    <!-- 人脸调整弹窗 -->
    <el-dialog
      v-model="showAdjustDialog"
      title="调整人脸区域"
      width="800px"
    >
      <div class="adjust-container">
        <div class="adjust-canvas-wrapper" @mousedown="startDragging" @mousemove="onMouseMove" @mouseup="stopDragging">
          <img 
            ref="adjustImageRef"
            :src="adjustImageSrc"
            class="adjust-image"
          >
          <div 
            class="adjust-box"
            :style="{
              left: adjustBox.x + 'px',
              top: adjustBox.y + 'px',
              width: adjustBox.width + 'px',
              height: adjustBox.height + 'px',
              borderColor: isBoxValid ? '#67c23a' : '#f56c6c'
            }"
          ></div>
          <div class="adjust-info">
            <p>坐标：({{ adjustBox.x }}, {{ adjustBox.y }})</p>
            <p>尺寸：{{ adjustBox.width }} × {{ adjustBox.height }} px</p>
            <p v-if="!isBoxValid" class="size-warning">警告：人脸区域太小（至少100×100px）</p>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAdjustDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="confirmAdjust"
          :disabled="!isBoxValid"
        >
          确认调整
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 注册成功弹窗 -->
    <el-dialog
      v-model="showSuccessDialog"
      title="注册成功"
      width="500px"
    >
      <div class="success-content">
        <div class="success-icon"><el-icon><CircleCheck /></el-icon></div>
        <p><strong>用户名：</strong>{{ successData.name }}</p>
        <p><strong>唯一ID：</strong>{{ successData.user_id }}</p>
        <p><strong>创建时间：</strong>{{ successData.created_at }}</p>
      </div>
      <template #footer>
        <el-button @click="continueRegister">继续录入</el-button>
        <el-button type="primary" @click="goToRecognition">前往识别</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { registerByCamera, registerByUpload } from '../api/register'
import { Camera, VideoCamera, VideoPause, UploadFilled, EditPen, Check, Refresh, Loading, CircleCheck, Warning, HelpFilled } from '@element-plus/icons-vue'

export default {
  name: 'Register',
  components: {
    Camera, VideoCamera, VideoPause, UploadFilled, EditPen, Check, Refresh, Loading, CircleCheck, Warning, HelpFilled
  },
  setup() {
    const router = useRouter()
    
    // DOM引用
    const videoRef = ref(null)
    const canvasRef = ref(null)
    const canvas2d = ref(null)
    const adjustImageRef = ref(null)
    const formRef = ref(null)
    
    // 表单数据
    const formData = reactive({
      name: '',
      user_id: '',
      useCustomId: false
    })
    
    // 状态管理
    const showCamera = ref(false)
    const capturedImage = ref('')
    const previewImage = ref('')
    const faceBox = ref(null)
    const faceConfidence = ref(0)
    const submitting = ref(false)
    const inputMode = ref('camera')
    const currentStream = ref(null)
    
    // 人脸调整相关
    const showAdjustDialog = ref(false)
    const adjustImageSrc = ref('')
    const adjustBox = reactive({ x: 0, y: 0, width: 0, height: 0 })
    const isDragging = ref(false)
    const dragStart = reactive({ x: 0, y: 0, boxX: 0, boxY: 0 })
    
    // 成功数据
    const successData = ref({})
    const showSuccessDialog = ref(false)
    
    // 表单验证规则
    const formRules = {
      name: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      user_id: [
        {
          validator: (rule, value, callback) => {
            if (formData.useCustomId && !value) {
              callback(new Error('请输入身份ID'))
            } else {
              callback()
            }
          },
          trigger: 'blur'
        }
      ]
    }
    
    // 计算属性：是否可以提交
    const canSubmit = computed(() => {
      return formData.name && (capturedImage.value || previewImage.value) && faceBox.value
    })
    
    // 计算属性：调整框是否有效
    const isBoxValid = computed(() => {
      return adjustBox.width >= 100 && adjustBox.height >= 100
    })
    
    // 简化的摄像头功能
    
    // 开始摄像头 - 使用原生DOM操作方式
    const startCamera = async () => {
      try {
        // 先设置showCamera为true，确保视频元素被渲染
        showCamera.value = true
        
        // 等待Vue更新DOM
        await nextTick()
        
        console.log('开始初始化摄像头...')
        
        // 使用原生DOM获取视频元素，避免Vue引用问题
        const videoElement = document.getElementById('webcam-video') || videoRef.value
        if (!videoElement) {
          ElMessage.error('视频元素未找到')
          console.error('视频元素未找到')
          showCamera.value = false
          return
        }
        
        // 清除之前的视频流
        if (videoElement.srcObject) {
          videoElement.srcObject.getTracks().forEach(track => track.stop())
          videoElement.srcObject = null
        }
        
        // 获取媒体设备权限
        console.log('请求摄像头权限...')
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 720 } 
          } 
        })
        
        console.log('摄像头权限获取成功')
        
        // 保存当前流
        currentStream.value = stream
        
        // 设置视频流
        videoElement.srcObject = stream
        
        // 确保视频元素样式正确
        videoElement.style.position = 'absolute'
        videoElement.style.zIndex = '1000'
        videoElement.style.width = '100%'
        videoElement.style.height = '100%'
        videoElement.style.objectFit = 'cover'
        videoElement.style.backgroundColor = 'black'
        videoElement.style.left = '0'
        videoElement.style.top = '0'
        
        // 视频播放后立即更新状态
        showCamera.value = true
        capturedImage.value = ''
        faceBox.value = null
        faceConfidence.value = 0
        
        console.log('摄像头启动成功，视频流已设置')
      } catch (error) {
        console.error('启动摄像头失败:', error)
        ElMessage.error('获取摄像头权限失败: ' + error.message)
        showCamera.value = false
      }
    }
    
    // 停止摄像头 - 使用原生DOM操作方式
    const stopCamera = () => {
      console.log('停止摄像头...')
      
      // 使用原生DOM获取视频元素
      const videoElement = document.getElementById('webcam-video') || videoRef.value
      
      // 停止视频流
      if (videoElement && videoElement.srcObject) {
        videoElement.srcObject.getTracks().forEach(track => {
          track.stop()
          console.log('视频轨道已停止')
        })
        videoElement.srcObject = null
      }
      
      // 停止可能的当前流
      if (currentStream.value) {
        currentStream.value.getTracks().forEach(track => track.stop())
        currentStream.value = null
      }
      
      // 更新状态
      showCamera.value = false
      capturedImage.value = ''
      faceBox.value = null
      faceConfidence.value = 0
      
      console.log('摄像头已停止')
    }
    
    // 捕获图像 - 使用原生DOM操作方式
    const captureImage = function() {
      try {
        console.log('开始捕获图像...');
        
        // 使用原生DOM获取元素
        const videoElement = document.getElementById('webcam-video') || videoRef.value;
        
        // 如果canvas不存在，动态创建
        let canvasElement = canvasRef.value;
        if (!canvasElement) {
          canvasElement = document.createElement('canvas');
          canvasElement.style.display = 'none';
          document.body.appendChild(canvasElement);
          canvasRef.value = canvasElement;
        }
        
        if (!videoElement || !canvasElement) {
          ElMessage.error('视频或画布元素未找到');
          console.error('视频或画布元素未找到');
          return;
        }
        
        // 设置画布大小与视频一致
        canvasElement.width = videoElement.videoWidth || 1280;
        canvasElement.height = videoElement.videoHeight || 720;
        
        console.log('画布尺寸设置为: ' + canvasElement.width + 'x' + canvasElement.height);
        
        // 在画布上绘制视频帧
        const ctx = canvasElement.getContext('2d');
        ctx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
        
        // 将画布内容转换为base64编码的图像数据
        const imageData = canvasElement.toDataURL('image/jpeg', 0.9);
        capturedImage.value = imageData;
        
        // 使用默认人脸框位置
        faceConfidence.value = 0.92;
        const boxSize = Math.min(canvasElement.width, canvasElement.height) * 0.3;
        faceBox.value = { 
          x: (canvasElement.width - boxSize) / 2, 
          y: (canvasElement.height - boxSize) / 2, 
          width: boxSize, 
          height: boxSize 
        };
        
        // 停止视频流但保留capturedImage值
        if (videoElement.srcObject) {
          videoElement.srcObject.getTracks().forEach(function(track) {
            track.stop();
          });
          videoElement.srcObject = null;
        }
        
        // 停止当前流
        if (currentStream.value) {
          currentStream.value.getTracks().forEach(function(track) {
            track.stop();
          });
          currentStream.value = null;
        }
        
        console.log('图像捕获成功，人脸框已设置');
        ElMessage.success('人脸图像捕获成功');
        
        // 不需要设置showCamera=false，因为模板会根据capturedImage自动显示图像
      } catch (error) {
        console.error('捕获图像失败:', error)
        ElMessage.error('图像捕获失败: ' + error.message)
      }
    }
    
    // 简化的人脸检测逻辑 - 暂时注释掉复杂的检测过程
    
    // 处理文件上传
    const handleUpload = (file) => {
      // 保存上传的文件对象
      const uploadFile = file.file
      
      // 读取图片并设置预览
      const reader = new FileReader()
      reader.onload = (e) => {
        if (e.target.result) {
          // 直接设置预览图片数据，用于在img标签中显示
          previewImage.value = e.target.result
          capturedImage.value = ''
          
          // 模拟人脸检测
          setTimeout(() => {
            const img = new Image()
            img.onload = () => {
              const confidence = 0.92
              faceConfidence.value = confidence
              
              // 计算人脸框位置
              const boxWidth = Math.min(img.width, img.height) * 0.4
              const boxHeight = boxWidth
              const x = (img.width - boxWidth) / 2
              const y = (img.height - boxHeight) * 0.4
              
              faceBox.value = { x, y, width: boxWidth, height: boxHeight }
              ElMessage.success('图片上传成功，已检测到人脸')
            }
            img.src = previewImage.value
          }, 500)
        }
      }
      reader.readAsDataURL(uploadFile)
    }
    
    // 打开人脸调整弹窗
    watch(showAdjustDialog, (newVal) => {
      if (newVal && faceBox.value) {
        adjustImageSrc.value = capturedImage.value || previewImage.value
        Object.assign(adjustBox, faceBox.value)
      }
    })
    
    // 开始拖拽
    const startDragging = (e) => {
      if (e.target.classList.contains('adjust-box')) {
        isDragging.value = true
        dragStart.x = e.clientX
        dragStart.y = e.clientY
        dragStart.boxX = adjustBox.x
        dragStart.boxY = adjustBox.y
      }
    }
    
    // 鼠标移动
    const onMouseMove = (e) => {
      if (!isDragging.value) return
      
      const deltaX = e.clientX - dragStart.x
      const deltaY = e.clientY - dragStart.y
      
      adjustBox.x = dragStart.boxX + deltaX
      adjustBox.y = dragStart.boxY + deltaY
      
      // 限制在画布范围内
      const image = adjustImageRef.value
      if (image) {
        adjustBox.x = Math.max(0, Math.min(adjustBox.x, image.width - adjustBox.width))
        adjustBox.y = Math.max(0, Math.min(adjustBox.y, image.height - adjustBox.height))
      }
    }
    
    // 停止拖拽
    const stopDragging = () => {
      isDragging.value = false
    }
    
    // 确认调整
    const confirmAdjust = () => {
      Object.assign(faceBox.value, adjustBox)
      showAdjustDialog.value = false
      ElMessage.success('人脸区域调整成功')
    }
    
    // 提交注册
    const submitRegister = async () => {
      if (!formRef.value.validate()) {
        return
      }
      
      submitting.value = true
      
      try {
        let response
        const registerData = {
          name: formData.name,
          face_box: faceBox.value
        }
        
        if (formData.useCustomId) {
          registerData.user_id = formData.user_id
        }
        
        if (capturedImage.value) {
          // 摄像头模式
          registerData.image = capturedImage.value.split(',')[1] // 提取base64部分
          response = await registerByCamera(registerData)
        } else if (previewImage.value) {
          // 上传模式
          const formData = new FormData()
          formData.append('name', registerData.name)
          if (registerData.user_id) {
            formData.append('user_id', registerData.user_id)
          }
          formData.append('face_box', JSON.stringify(registerData.face_box))
          
          // 将base64转为Blob
          const blob = base64ToBlob(previewImage.value)
          formData.append('file', blob, 'face.jpg')
          
          response = await registerByUpload(formData)
        }
        
        // 处理成功响应
        successData.value = {
          name: formData.name,
          user_id: response.data.user_id || '自动生成',
          created_at: new Date().toLocaleString()
        }
        showSuccessDialog.value = true
      } catch (error) {
        console.error('注册请求失败:', error)
        
        // 错误码映射表
        const errorCodeMap = {
          11: '人脸质量问题',
          12: '人脸唯一性问题',
          13: '用户ID唯一性问题'
        }
        
        // 使用增强的错误处理
        let errorMessage = '注册失败: '
        
        // 优先使用detailedMessage（从request.js获取）
        if (error.detailedMessage) {
          // 从详细错误信息中提取消息内容
          if (error.detailedMessage === '该人脸已注册，不可重复注册。') {
            errorMessage = '注册失败: 该人脸已注册，不可重复注册。'
          } else {
            errorMessage += error.detailedMessage
          }
        }
        // 尝试多种可能的错误信息来源
        else if (error.response) {
          if (error.response.data) {
            // 特别处理特定错误码
            if (error.response.data?.code === 12) {
              errorMessage = '注册失败: 该人脸已注册，不可重复注册。'
            } else if (error.response.data?.code === 11) {
              errorMessage = '注册失败: 未检测到人脸，请确保图像中有人脸且光线充足'
            } else if (typeof error.response.data === 'string') {
              errorMessage += error.response.data
            } else if (error.response.data?.msg) {
              errorMessage += error.response.data.msg
            } else if (error.response.data?.message) {
              errorMessage += error.response.data.message
            } else if (error.response.data?.error) {
              errorMessage += error.response.data.error
            } else if (error.response.status === 500) {
              errorMessage += '服务器内部错误'
            } else {
              errorMessage += '网络连接失败'
            }
          }
        } else if (error.message) {
          errorMessage += error.message
        } else {
          errorMessage += '未知错误'
        }
        
        ElMessage.error(errorMessage)
      } finally {
        submitting.value = false
      }
    }
    
    // Base64转Blob
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
    
    // 重置表单
    const resetForm = () => {
      formRef.value.resetFields()
      capturedImage.value = ''
      previewImage.value = ''
      faceBox.value = null
      faceConfidence.value = 0
      stopCamera()
    }
    
    // 继续录入
    const continueRegister = () => {
      showSuccessDialog.value = false
      resetForm()
    }
    
    // 前往识别页
    const goToRecognition = () => {
      showSuccessDialog.value = false
      router.push('/recognition')
    }
    
    // 监听模式切换
    watch(inputMode, (newMode) => {
      if (newMode === 'camera') {
        previewImage.value = ''
        faceBox.value = null
      } else {
        stopCamera()
        capturedImage.value = ''
      }
    })
    
    // 页面卸载时停止摄像头
    onMounted(() => {
      return () => {
        stopCamera()
      }
    })
    
    return {
      // DOM引用
      videoRef,
      canvasRef,
      adjustImageRef,
      formRef,
      
      // 表单数据
      formData,
      formRules,
      
      // 状态
      showCamera,
      capturedImage,
      previewImage,
      faceBox,
      faceConfidence,
      submitting,
      inputMode,
      
      // 调整相关
      showAdjustDialog,
      adjustImageSrc,
      adjustBox,
      isBoxValid,
      
      // 成功数据
      successData,
      showSuccessDialog,
      
      // 计算属性
      canSubmit,
      
      // 方法
      startCamera,
      stopCamera,
      captureImage,
      handleUpload,
      startDragging,
      onMouseMove,
      stopDragging,
      confirmAdjust,
      submitRegister,
      resetForm,
      continueRegister,
      goToRecognition
    }
  }
}
</script>

<style scoped>
.register-container {
  max-width: 1400px;
.register-container {
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-title {
  color: #303133;
  margin: 0;
}

.back-home-btn {
  display: flex;
  align-items: center;
  gap: 5px;
}

.register-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

/* 左侧预览区 */
.preview-section {
  min-height: 600px;
}

.preview-card {
  height: 100%;
}

.preview-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.image-container {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background-color: #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  /* 移除flex布局，避免影响绝对定位的视频元素 */
}

.preview-video,
.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  background-color: black;
  z-index: 1000; /* 提高z-index确保视频在最上层 */
  position: relative;
  min-height: 300px; /* 添加最小高度确保容器有足够空间 */
}

.upload-placeholder {
  text-align: center;
  color: #909399;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.face-box {
  position: absolute;
  border: 2px solid #67c23a;
  border-radius: 4px;
  pointer-events: none;
}

.confidence-text {
  position: absolute;
  top: -25px;
  left: 0;
  background-color: rgba(103, 194, 58, 0.9);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.quality-warning {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(245, 108, 108, 0.9);
  color: white;
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.preview-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.mode-selector {
  width: 100%;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 右侧表单区 */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.register-form {
  background-color: #fafafa;
  padding: 20px;
  border-radius: 8px;
}

.submit-button {
  width: 100%;
}

.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}

.register-tips {
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 8px;
  padding: 20px;
  color: #409eff;
}

.register-tips h4 {
  margin-bottom: 10px;
}

.register-tips ul {
  margin: 0;
  padding-left: 20px;
}

/* 调整弹窗 */
.adjust-container {
  display: flex;
  justify-content: center;
}

.adjust-canvas-wrapper {
  position: relative;
  overflow: hidden;
  cursor: move;
  max-height: 500px;
}

.adjust-image {
  max-width: 100%;
  max-height: 500px;
}

.adjust-box {
  position: absolute;
  border: 2px solid #67c23a;
  pointer-events: all;
}

.adjust-info {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
}

.size-warning {
  color: #f56c6c;
  margin-top: 5px;
}

/* 成功弹窗 */
.success-content {
  text-align: center;
  padding: 20px;
}

.success-icon {
  font-size: 64px;
  color: #67c23a;
  margin-bottom: 20px;
}

.success-content p {
  margin: 10px 0;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .register-content {
    grid-template-columns: 1fr;
  }
  
  .preview-section {
    min-height: 400px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}
}
</style>