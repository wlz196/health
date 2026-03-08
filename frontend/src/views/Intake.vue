<template>
  <div class="p-4 bg-gray-50 min-h-screen pb-20">
    <h1 class="text-3xl font-extrabold text-gray-800 tracking-tight mb-2 mt-2">饮食摄入分析</h1>
    <p class="text-gray-500 text-sm mb-6">通过图像或者纯文本描述，让 AI 营养师为你推算热量与营养元素。</p>

    <!-- 顶部的视觉区块 -->
    <div class="bg-gradient-to-r from-orange-400 to-red-500 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden mb-6 flex flex-col justify-center items-center py-6">
       <div class="absolute top-0 right-0 -mt-8 -mr-8 w-32 h-32 bg-white opacity-10 rounded-full blur-xl"></div>
       <van-icon name="photograph" class="text-5xl opacity-90 mb-4" />
       
       <van-uploader 
          :after-read="onRead" 
          :before-read="beforeRead"
          accept="image/*"
          :max-count="1"
          capture="camera"
          v-model="fileList"
       >
         <van-button icon="plus" round type="primary" color="rgba(255,255,255,0.2)" class="font-bold border-2 border-white backdrop-blur-md">拍照或选图分析</van-button>
       </van-uploader>
    </div>

    <div class="bg-white rounded-3xl p-5 shadow-sm mb-6">
        <h3 class="font-bold text-gray-700 mb-3 text-sm">或者告诉 AI 营养师你吃了什么：</h3>
        <van-cell-group inset class="!m-0 border border-gray-100 mb-3">
          <van-field
            v-model="foodText"
            rows="2"
            autosize
            type="textarea"
            placeholder="例如：一盘西兰花，或者 200g 鸡胸肉加一碗米饭"
            class="bg-gray-50"
          />
        </van-cell-group>
        <van-button block round type="primary" color="linear-gradient(to right, #fb923c, #ef4444)" @click="onAnalyzeText" :disabled="!foodText">
           一键AI文本识别
        </van-button>
    </div>

    <!-- 分析中遮罩区 -->
    <div v-if="analyzing" class="text-center py-10 bg-white rounded-2xl shadow-sm">
        <van-loading type="spinner" color="#f97316" size="36px" class="mb-4 text-orange-500"/>
        <p class="text-gray-500 font-medium animate-pulse">AI 正在飞速计算营养价值...</p>
    </div>

    <!-- 结果展示区 -->
    <div v-if="!analyzing && result" class="bg-white rounded-2xl p-5 shadow-sm border border-orange-50 mt-4 transition-all">
       <div v-if="result.error" class="text-red-500 bg-red-50 p-3 rounded-lg text-sm">
          {{ result.error }}
       </div>
       <div v-else>
           <div class="flex items-center justify-between border-b pb-4 mb-4">
              <h2 class="text-xl font-black text-gray-800 flex items-center">
                  <span class="mr-2">🍽️</span> {{ result.name || '未知食物' }}
              </h2>
           </div>
           
           <div class="flex justify-between items-center bg-orange-50 rounded-xl p-4 mb-4 border border-orange-100">
               <span class="text-gray-600 font-medium">总热量预估</span>
               <div><span class="text-3xl font-black text-orange-600 mr-1">{{ result.kcal }}</span><span class="text-xs text-orange-400">kcal</span></div>
           </div>
           
           <div class="grid grid-cols-3 gap-3 text-center">
               <div class="bg-gray-50 rounded-xl p-3">
                   <div class="text-xs text-gray-400 font-medium mb-1">蛋白质</div>
                   <div class="font-bold text-gray-800">{{ result.protein || 0 }}g</div>
               </div>
               <div class="bg-gray-50 rounded-xl p-3">
                   <div class="text-xs text-gray-400 font-medium mb-1">脂肪</div>
                   <div class="font-bold text-gray-800">{{ result.fat || 0 }}g</div>
               </div>
               <div class="bg-gray-50 rounded-xl p-3">
                   <div class="text-xs text-gray-400 font-medium mb-1">碳水</div>
                   <div class="font-bold text-gray-800">{{ result.carb || 0 }}g</div>
               </div>
           </div>
           
           <van-button block round class="mt-6" type="warning" @click="reset">记录并分析下一餐</van-button>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Compressor from 'compressorjs'

const fileList = ref([])
const foodText = ref('')
const analyzing = ref(false)
const result = ref(null)

// 压缩照片：极大地减少上传消耗和后端解码压力
const beforeRead = (file) => {
  return new Promise((resolve) => {
    new Compressor(file, {
      quality: 0.6,
      maxWidth: 800, // 调整图像宽度，AI 足以识别即可，无需几千万像素
      success(result) {
        // 构建出带有原始文件名的 File 格式以便于后续转 Base64 读取
        const compressedFile = new File([result], file.name, { type: result.type, lastModified: Date.now() });
        resolve(compressedFile);
      },
      error(err) {
        console.error('压缩失败:', err.message);
        resolve(file); // 失败时退回原文件，确保业务不中断
      },
    });
  });
}

const onAnalyzeText = async () => {
  if (!foodText.value.trim()) return

  analyzing.value = true
  result.value = null

  try {
    const response = await fetch('http://127.0.0.1:8080/api/intake/identify_text', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        description: foodText.value.trim()
      })
    })

    const data = await response.json()
    if (!response.ok) {
        throw new Error(data.detail || "请求失败")
    }
    result.value = data
  } catch (error) {
    console.error("AI 识别报错:", error)
    result.value = { error: error.message }
  } finally {
    analyzing.value = false
  }
}

const onRead = async (fileInfo) => {
  // 读取 Base64 内容
  const base64Data = fileInfo.content
  if (!base64Data) {
      alert("无法读取照片")
      return
  }

  analyzing.value = true
  result.value = null

  try {
    const response = await fetch('http://127.0.0.1:8080/api/intake/identify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        image_base64: base64Data
      })
    })

    const data = await response.json()
    if (!response.ok) {
        throw new Error(data.detail || "请求失败")
    }
    result.value = data
  } catch (error) {
    console.error("AI 识别报错:", error)
    result.value = { error: error.message }
  } finally {
    analyzing.value = false
  }
}

const reset = () => {
    fileList.value = []
    result.value = null
}
</script>
