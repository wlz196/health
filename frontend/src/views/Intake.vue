<template>
  <div class="p-4 bg-gray-50 min-h-screen pb-20">
    <h1 class="text-3xl font-extrabold text-gray-800 tracking-tight mb-2 mt-2">饮食记录</h1>
    <p class="text-gray-500 text-sm mb-6">记录您的每一餐热量与营养</p>
    
    <van-tabs v-model:active="activeTab" class="mb-6" color="#f97316" title-active-color="#f97316" sticky>
      <van-tab title="智能识别" name="ai">
        <!-- 顶部的视觉区块 -->
        <div class="bg-gradient-to-r from-orange-400 to-red-500 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden mb-6 flex flex-col justify-center items-center py-6 mt-4">
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
               
               <div class="py-2 mt-4 px-1">
                  <van-checkbox v-model="saveAiQuick" shape="square" checked-color="#ea580c">
                    <span class="text-sm text-gray-600">保存到「我的常用」以便下次快捷记录</span>
                  </van-checkbox>
               </div>
               
               <van-button block round class="mt-4" type="warning" color="linear-gradient(to right, #f59e0b, #ea580c)" @click="saveAiLogAndReset">记录并继续</van-button>
            </div>
         </div>
      </van-tab>

      <van-tab title="手动录入" name="manual">
         <!-- 快捷添加区域 -->
          <div v-if="savedFoods.length > 0" class="mb-4 mt-4">
             <h3 class="font-bold text-gray-700 mb-2 text-sm flex justify-between items-center">
               <span>🌟 我的常用</span>
               <span class="text-xs text-gray-400 font-normal">点击快速记录</span>
             </h3>
             <div class="flex flex-wrap gap-1.5">
                <div v-for="food in savedFoods" :key="food.id" 
                     class="bg-white border border-orange-200 text-orange-600 px-3 py-1.5 rounded-full text-xs font-medium shadow-sm active:scale-95 transition-transform flex items-center"
                     @click="quickAdd(food)">
                  {{food.name}} <span class="text-xs ml-1 opacity-70">{{food.kcal}}k</span>
                  <van-icon name="plus" class="ml-1" />
                </div>
             </div>
          </div>

          <!-- 🔥 历史记录快速填表区 -->
          <div v-if="recentFoods.length > 0" class="mb-6 mt-4">
             <h3 class="font-semibold text-gray-600 mb-2 text-xs flex items-center gap-1">
               <van-icon name="underway-o" class="text-orange-500" />
               <span>🕰️ 最近记录 (点击自动填表)</span>
             </h3>
             <div class="flex flex-wrap gap-1.5">
                <div v-for="food in recentFoods" :key="food.food_name" 
                     class="bg-gray-100 border border-gray-200 text-gray-600 px-3 py-1.5 rounded-full text-xs font-medium active:scale-95 transition-all flex items-center hover:bg-orange-50 hover:text-orange-600 cursor-pointer"
                     @click="fillForm(food)">
                  {{food.food_name}} <span class="text-[10px] ml-1 opacity-60">{{food.kcal}}k</span>
                </div>
             </div>
          </div>
         
         <!-- 手动表单区域 -->
         <div class="bg-white rounded-3xl p-5 shadow-sm mb-6" :class="savedFoods.length === 0 ? 'mt-4' : ''">
            <h3 class="font-bold text-gray-700 mb-3 text-sm">自定义添加</h3>
            <van-form ref="manualFormRef">
              <van-cell-group inset class="!mx-0 border border-gray-100 mb-3">
                <van-field v-model="manualForm.food_name" name="food_name" label="食物名称" placeholder="输入食物名称" :rules="[{ required: true, message: '请填写食物名称' }]" />
                <van-field v-model="manualForm.kcal" type="digit" name="kcal" label="热量(kcal)" placeholder="输入总热量" :rules="[{ required: true, message: '请填写热量' }]" />
                <van-field v-model="manualForm.protein" type="digit" name="protein" label="蛋白质(g)" placeholder="选填" />
                <van-field v-model="manualForm.fat" type="digit" name="fat" label="脂肪(g)" placeholder="选填" />
                <van-field v-model="manualForm.carb" type="digit" name="carb" label="碳水(g)" placeholder="选填" />
              </van-cell-group>
              
              <div class="py-2 mb-4">
                 <van-checkbox v-model="manualForm.save_quick" shape="square" checked-color="#f97316">
                   <span class="text-sm text-gray-600">保存到「我的常用」以便下次快捷记录</span>
                 </van-checkbox>
              </div>
              
              <van-button round block type="primary" color="linear-gradient(to right, #fb923c, #ef4444)" :loading="isSubmitting" @click="onSubmitManual">
                记录到今日摄入
              </van-button>
            </van-form>
         </div>
      </van-tab>
    </van-tabs>

    <!-- 每日记录列表 -->
    <div class="mt-8 px-1">
       <h2 class="text-lg font-bold text-gray-800 mb-4 flex items-center">
          <van-icon name="underway-o" class="mr-2 text-orange-500" />今日摄入时间线
       </h2>
       <div v-if="dailyLogs.length === 0" class="text-gray-400 text-sm text-center py-6 bg-white rounded-2xl border-dashed border border-gray-200">
          今还没有摄入记录，快去记录第一餐吧
       </div>
       <div v-else class="space-y-3">
          <div v-for="log in dailyLogs" :key="log.id" class="bg-white rounded-2xl p-4 shadow-sm flex flex-row items-center justify-between border-l-4 border-orange-400 relative">
             <div class="flex-1">
                <div class="flex items-center gap-2 mb-1.5">
                   <span class="text-xs text-orange-500 font-black bg-orange-50 px-2 py-0.5 rounded mr-1 tracking-wider">{{log.time || '--:--'}}</span>
                   <span class="font-bold text-gray-800 text-md">{{log.food_name}}</span>
                </div>
                <div class="text-xs text-gray-500 flex gap-3">
                   <span v-if="log.macros?.protein !== undefined">蛋白: {{log.macros.protein}}g</span>
                   <span v-if="log.macros?.fat !== undefined">脂肪: {{log.macros.fat}}g</span>
                   <span v-if="log.macros?.carb !== undefined">碳水: {{log.macros.carb}}g</span>
                </div>
             </div>
             <div class="text-right flex flex-col items-end justify-center min-w-[70px]">
                <div class="flex items-baseline">
                   <span class="text-2xl font-black text-orange-500">{{log.kcal}}</span>
                   <span class="text-[10px] text-gray-400 ml-0.5 font-bold uppercase tracking-tighter">kcal</span>
                </div>
             </div>
          </div>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Compressor from 'compressorjs'

const activeTab = ref('ai')
const fileList = ref([])
const foodText = ref('')
const analyzing = ref(false)
const result = ref(null)
const saveAiQuick = ref(false)

const savedFoods = ref([])
const recentFoods = ref([])
const dailyLogs = ref([])
const isSubmitting = ref(false)

const manualForm = ref({
  food_name: '',
  kcal: '',
  protein: '',
  fat: '',
  carb: '',
  save_quick: false
})

const fetchLogs = async () => {
    try {
        const res = await fetch('/api/intake/logs')
        if (res.ok) {
            const data = await res.json()
            if (Array.isArray(data)) {
                dailyLogs.value = data.reverse()
            } else {
                dailyLogs.value = []
            }
        }
    } catch (e) {
        console.error('Failed to fetch logs', e)
    }
}

const fetchSavedFoods = async () => {
    try {
        const res = await fetch('/api/intake/saved_foods')
        if (res.ok) {
            savedFoods.value = await res.json()
        }
    } catch (e) {
        console.error('Failed to fetch saved foods', e)
    }
}

const fetchHistory = async () => {
    try {
        const res = await fetch('/api/intake/history')
        if (res.ok) {
            recentFoods.value = await res.json()
        }
    } catch (e) {
        console.error('Failed to fetch history', e)
    }
}

const onSubmitManual = async () => {
    console.log("Submit button clicked! manualForm data:", manualForm.value)
    isSubmitting.value = true
    
    // 1. Save log
    const logData = {
        food_name: manualForm.value.food_name,
        kcal: parseInt(manualForm.value.kcal),
        macros: {
            protein: manualForm.value.protein ? parseInt(manualForm.value.protein) : 0,
            fat: manualForm.value.fat ? parseInt(manualForm.value.fat) : 0,
            carb: manualForm.value.carb ? parseInt(manualForm.value.carb) : 0
        }
    }
    
    console.log("Prepared logData for backend:", logData)
    
    try {
        const res = await fetch('/api/intake/logs', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(logData)
        })
        if (res.ok) {
            await fetchLogs()
            await fetchHistory()
        } else {
            const errData = await res.json()
            console.error("API返回错误:", errData)
            alert("记录失败: " + JSON.stringify(errData))
        }
    } catch (e) {
        console.error("网络请求失败:", e)
        alert("网络请求失败")
    }
    
    // 2. If checked save quick
    if (manualForm.value.save_quick) {
        try {
            const res2 = await fetch('/api/intake/saved_foods', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: manualForm.value.food_name,
                    kcal: parseInt(manualForm.value.kcal),
                    protein: logData.macros.protein,
                    fat: logData.macros.fat,
                    carb: logData.macros.carb
                })
            })
            if (res2.ok) {
                await fetchSavedFoods()
            }
        } catch(e) {
            console.error("保存常用失败:", e)
        }
    }
    
    // Reset form
    manualForm.value = { food_name: '', kcal: '', protein: '', fat: '', carb: '', save_quick: false }
    isSubmitting.value = false
}

const quickAdd = async (food) => {
    const logData = {
        food_name: food.name,
        kcal: food.kcal,
        macros: {
            protein: food.protein || 0,
            fat: food.fat || 0,
            carb: food.carb || 0
        }
    }
    try {
        const res = await fetch('/api/intake/logs', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(logData)
        })
        if (res.ok) {
            await fetchLogs()
        } else {
            const errData = await res.json()
            console.error("快捷记录API返回错误:", errData)
            alert("快捷记录失败: " + JSON.stringify(errData))
        }
    } catch (e) {
        console.error("快捷记录网络失败:", e)
        alert("快捷记录网络请求失败")
    }
}

const saveAiLogAndReset = async () => {
    if (!result.value || result.value.error) {
        reset()
        return
    }
    
    const logData = {
        food_name: result.value.name || '未知食物',
        kcal: result.value.kcal || 0,
        macros: {
            protein: result.value.protein || 0,
            fat: result.value.fat || 0,
            carb: result.value.carb || 0
        }
    }
    try {
        const res = await fetch('/api/intake/logs', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(logData)
        })
        if (res.ok) {
            await fetchLogs()
            await fetchHistory()
        }
    } catch (e) {
        console.error("记录失败:", e)
    }

    if (saveAiQuick.value) {
        try {
            const res2 = await fetch('/api/intake/saved_foods', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: result.value.name || '未知食物',
                    kcal: result.value.kcal || 0,
                    protein: result.value.protein || 0,
                    fat: result.value.fat || 0,
                    carb: result.value.carb || 0
                })
            })
            if (res2.ok) {
                await fetchSavedFoods()
            }
        } catch(e) {
            console.error("保存常用失败:", e)
        }
    }

    saveAiQuick.value = false
    reset()
}

const beforeRead = (file) => {
  return new Promise((resolve) => {
    new Compressor(file, {
      quality: 0.6,
      maxWidth: 800,
      success(result) {
        const compressedFile = new File([result], file.name, { type: result.type, lastModified: Date.now() });
        resolve(compressedFile);
      },
      error(err) {
        console.error('压缩失败:', err.message);
        resolve(file);
      },
    });
  });
}

const onAnalyzeText = async () => {
  if (!foodText.value.trim()) return

  analyzing.value = true
  result.value = null

  try {
    const response = await fetch('/api/intake/identify_text', {
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
  const base64Data = fileInfo.content
  if (!base64Data) {
      alert("无法读取照片")
      return
  }

  analyzing.value = true
  result.value = null

  try {
    const response = await fetch('/api/intake/identify', {
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

const fillForm = (food) => {
    manualForm.value.food_name = food.food_name
    manualForm.value.kcal = String(food.kcal)
    manualForm.value.protein = food.macros?.protein !== undefined ? String(food.macros.protein) : ''
    manualForm.value.fat = food.macros?.fat !== undefined ? String(food.macros.fat) : ''
    manualForm.value.carb = food.macros?.carb !== undefined ? String(food.macros.carb) : ''
}

onMounted(() => {
    fetchLogs()
    fetchSavedFoods()
    fetchHistory()
})
</script>
