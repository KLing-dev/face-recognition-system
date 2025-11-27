<template>
  <div class="camera-test-container">
    <h2>摄像头测试页面</h2>
    
    <!-- 简化的视频容器，确保样式优先 -->
    <div class="simple-video-wrapper">
      <div class="video-box">
        <video 
          id="testVideo" 
          ref="videoRef" 
          autoplay 
          playsinline
          class="test-video"
          @error="handleVideoError"
          @play="handleVideoPlay"
          @loadeddata="handleLoadedData"
        ></video>
      </div>
    </div>
    
    <div class="controls">
      <el-button 
        type="primary" 
        @click="startCameraTest" 
        :disabled="isCameraActive"
      >
        启动摄像头
      </el-button>
      <el-button 
        type="danger" 
        @click="stopCameraTest" 
        :disabled="!isCameraActive"
      >
        停止摄像头
      </el-button>
      <el-button 
        type="info" 
        @click="checkVideoStatus"
      >
        检查状态
      </el-button>
    </div>
    
    <div class="debug-info">
      <h3>调试信息</h3>
      <pre>{{ debugLogs }}</pre>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElButton } from 'element-plus'
import { ElMessage } from 'element-plus'

export default {
  name: 'CameraTest',
  components: {
    ElButton
  },
  setup() {
    const videoRef = ref(null)
    const isCameraActive = ref(false)
    const debugLogs = ref('')
    let stream = null

    // 添加日志
    const addLog = (message) => {
      const timestamp = new Date().toLocaleTimeString()
      debugLogs.value = `${debugLogs.value}\n[${timestamp}] ${message}`
      console.log(`[Camera Test] ${message}`)
    }

    // 启动摄像头测试
    const startCameraTest = async () => {
      try {
        addLog('=== 开始摄像头测试 ===')
        
        // 先检查浏览器支持
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('浏览器不支持摄像头API')
        }
        
        // 请求摄像头权限
        addLog('请求摄像头权限...')
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user'
          }
        })
        
        addLog('摄像头权限已获取')
        addLog('视频轨道信息:', stream.getVideoTracks())
        
        // 使用原生DOM方法直接操作video元素
        const video = videoRef.value || document.getElementById('testVideo')
        
        if (!video) {
          throw new Error('视频元素未找到')
        }
        
        addLog('找到视频元素:', video.tagName)
        
        // 清除之前的流
        if (video.srcObject) {
          video.srcObject.getTracks().forEach(track => track.stop())
        }
        
        // 直接设置视频流
        video.srcObject = stream
        addLog('视频流设置完成')
        
        // 尝试播放视频
        try {
          await video.play()
          addLog('视频播放请求已发送')
          isCameraActive.value = true
        } catch (playError) {
          addLog(`播放错误: ${playError.message}`)
        }
        
        ElMessage.success('摄像头启动成功')
      } catch (error) {
        console.error('摄像头测试错误:', error)
        addLog(`启动失败: ${error.message}`)
        ElMessage.error(`启动失败: ${error.message}`)
      }
    }

    // 停止摄像头测试
    const stopCameraTest = () => {
      try {
        addLog('=== 停止摄像头测试 ===')
        
        // 停止视频流
        if (stream) {
          stream.getTracks().forEach(track => track.stop())
          stream = null
          addLog('视频流已停止')
        }
        
        // 清除video引用
        const video = videoRef.value || document.getElementById('testVideo')
        if (video) {
          video.srcObject = null
        }
        
        isCameraActive.value = false
        addLog('摄像头已完全停止')
        ElMessage.success('摄像头已停止')
      } catch (error) {
        addLog(`停止失败: ${error.message}`)
        ElMessage.error(`停止失败: ${error.message}`)
      }
    }

    // 检查视频状态
    const checkVideoStatus = () => {
      const video = videoRef.value || document.getElementById('testVideo')
      if (!video) {
        addLog('无法找到视频元素')
        return
      }
      
      addLog('--- 视频状态检查 ---')
      addLog(`视频就绪状态: ${video.readyState}`)
      addLog(`视频网络状态: ${video.networkState}`)
      addLog(`视频宽度: ${video.videoWidth}, 高度: ${video.videoHeight}`)
      addLog(`autoplay: ${video.autoplay}`)
      addLog(`paused: ${video.paused}`)
      addLog(`muted: ${video.muted}`)
      addLog(`播放速率: ${video.playbackRate}`)
      addLog(`hasAttribute(playsinline): ${video.hasAttribute('playsinline')}`)
      
      if (video.srcObject) {
        const tracks = video.srcObject.getTracks()
        addLog(`视频轨道数量: ${tracks.length}`)
        tracks.forEach((track, index) => {
          addLog(`轨道 ${index}: kind=${track.kind}, enabled=${track.enabled}, readyState=${track.readyState}`)
        })
      }
    }

    // 处理视频错误
    const handleVideoError = (error) => {
      const videoError = error.target.error
      addLog(`视频错误: ${videoError ? videoError.message : '未知错误'}`)
    }

    // 处理视频播放
    const handleVideoPlay = () => {
      addLog('视频开始播放')
    }

    // 处理视频数据加载
    const handleLoadedData = () => {
      addLog('视频数据已加载')
      checkVideoStatus() // 自动检查状态
    }

    // 页面卸载时清理资源
    onUnmounted(() => {
      stopCameraTest()
    })

    // 页面加载时添加样式检查
    onMounted(() => {
      addLog('测试页面已加载')
      addLog(`视频容器样式检查: ${document.querySelector('.simple-video-wrapper') ? '存在' : '不存在'}`)
    })

    return {
      videoRef,
      isCameraActive,
      debugLogs,
      startCameraTest,
      stopCameraTest,
      checkVideoStatus,
      handleVideoError,
      handleVideoPlay,
      handleLoadedData
    }
  }
}
</script>

<style scoped>
.camera-test-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

/* 简化的视频包装器，使用绝对定位确保视频显示 */
.simple-video-wrapper {
  width: 100%;
  height: 400px;
  position: relative;
  margin-bottom: 30px;
  background-color: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-box {
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 10;
}

/* 关键样式：确保视频元素显示优先 */
.test-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain; /* 使用contain避免拉伸 */
  background-color: #000;
  z-index: 20;
  display: block;
}

/* 确保video元素在DOM中具有最高优先级 */
.test-video {
  transform: translateZ(10px); /* 使用3D变换提升层级 */
}

.controls {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
}

.debug-info {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.debug-info h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
}

.debug-info pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.4;
}

/* 全局视频样式重置，确保无冲突 */
:deep(#testVideo) {
  width: 100% !important;
  height: 100% !important;
  background-color: #000 !important;
  display: block !important;
  position: relative !important;
  z-index: 9999 !important;
}
</style>

<style>
/* 全局样式，避免其他样式影响 */
#testVideo {
  width: 100% !important;
  height: 100% !important;
  background-color: #000 !important;
  display: block !important;
  position: relative !important;
  z-index: 9999 !important;
}
</style>