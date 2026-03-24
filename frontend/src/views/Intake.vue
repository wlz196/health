<template>
  <div class="p-4 bg-gray-50 min-h-screen pb-20">
    <h1 class="text-3xl font-extrabold text-gray-800 tracking-tight mb-2 mt-2">饮食记录</h1>
    <p class="text-gray-500 text-sm mb-4">记录您的每一餐热量与营养</p>
    
    <!-- 📊 今日营养汇总看板 -->
    <div class="bg-white rounded-3xl p-5 shadow-sm mb-4 border border-gray-100">
      <div class="flex justify-between items-center mb-3">
        <div>
          <span class="text-2xl font-black" :class="kcalPercentage >= 100 ? 'text-red-500' : 'text-gray-800'">{{ totalKcal }}</span>
          <span class="text-xs text-gray-400 ml-1">/ {{ targetKcal }} kcal</span>
        </div>
        <van-tag :type="kcalPercentage >= 100 ? 'danger' : 'warning'" size="medium" round class="font-bold">今日摄入</van-tag>
      </div>
      
      <van-progress :percentage="kcalPercentage" :color="kcalPercentage >= 100 ? '#ef4444' : '#f97316'" stroke-width="8px" :show-pivot="false" class="mb-4" />
      
      <div class="grid grid-cols-3 gap-2 text-center text-xs">
        <div class="bg-gray-50 rounded-lg p-2">
          <div class="text-gray-400 mb-0.5">蛋白质</div>
          <div class="font-bold text-gray-700">{{ totalProtein.toFixed(1) }}g</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-2">
          <div class="text-gray-400 mb-0.5">脂肪</div>
          <div class="font-bold text-gray-700">{{ totalFat.toFixed(1) }}g</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-2">
          <div class="text-gray-400 mb-0.5">碳水</div>
          <div class="font-bold text-gray-700">{{ totalCarb.toFixed(1) }}g</div>
        </div>
      </div>
    </div>

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
                       <div class="font-bold text-gray-800">{{ Number(result.protein || 0).toFixed(1) }}g</div>
                   </div>
                   <div class="bg-gray-50 rounded-xl p-3">
                       <div class="text-xs text-gray-400 font-medium mb-1">脂肪</div>
                       <div class="font-bold text-gray-800">{{ Number(result.fat || 0).toFixed(1) }}g</div>
                   </div>
                   <div class="bg-gray-50 rounded-xl p-3">
                       <div class="text-xs text-gray-400 font-medium mb-1">碳水</div>
                       <div class="font-bold text-gray-800">{{ Number(result.carb || 0).toFixed(1) }}g</div>
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
          <!-- 🔍 搜索过滤 -->
          <van-search v-model="searchQuery" placeholder="搜索已保存的模板或食物..." class="!p-0 mb-4 bg-transparent" />

         <!-- 快捷添加区域 -->
          <!-- 🌟 我的常用（普通食物） -->
          <div v-if="normalSavedFoods.length > 0" class="mb-3 mt-4">
             <h3 class="font-bold text-gray-700 mb-2 text-xs flex justify-between items-center">
               <span>🌟 我的常用</span>
               <span class="text-xs text-gray-400 font-normal">点击快速记录（划过可删）</span>
             </h3>
             <div class="flex flex-wrap gap-1.5">
                <div v-for="food in normalSavedFoods" :key="food.id" 
                     class="bg-white border border-orange-200 text-orange-600 px-3 py-1.5 rounded-full text-xs font-medium shadow-sm active:scale-95 transition-transform flex items-center group relative cursor-pointer">
                  <span @click="quickAdd(food)" class="flex items-center">
                    {{food.name}} <span class="text-xs ml-1 opacity-70">{{food.kcal}}k</span>
                  </span>
                  <van-icon name="clear" class="text-gray-300 hover:text-red-500 text-[14px] ml-1 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop="deleteSavedFood(food.id)" />
                </div>
             </div>
          </div>

          <!-- 📋 配料表模板（100g） -->
          <div v-if="templateSavedFoods.length > 0" class="mb-4">
             <h3 class="font-bold text-gray-700 mb-2 text-xs flex justify-between items-center">
               <span>📋 配料表模板</span>
               <span class="text-xs text-gray-400 font-normal">点击选克数记录</span>
             </h3>
             <div class="flex flex-wrap gap-1.5">
                <div v-for="food in templateSavedFoods" :key="food.id" 
                     class="bg-white border border-orange-200 text-orange-600 px-3 py-1.5 rounded-full text-xs font-medium shadow-sm active:scale-95 transition-transform flex items-center group relative cursor-pointer">
                  <span @click="onTemplateClick(food)" class="flex items-center">
                    {{food.name}} <span class="text-xs ml-1 opacity-70">{{food.kcal}}k</span>
                    <van-tag type="warning" class="ml-1 scale-90" plain round>100g</van-tag>
                  </span>
                  <van-icon name="clear" class="text-gray-300 hover:text-red-500 text-[14px] ml-1 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop="deleteSavedFood(food.id)" />
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
                <div v-for="food in recentFoods" :key="food.id" 
                     class="bg-gray-100 border border-gray-200 text-gray-600 px-3 py-1.5 rounded-full text-xs font-medium active:scale-95 transition-all flex items-center hover:bg-orange-50 hover:text-orange-600 cursor-pointer"
                     @click="fillForm(food)">
                  {{food.food_name}} <span class="text-[10px] ml-1 opacity-60">{{food.kcal}}k</span>
                </div>
             </div>
          </div>
         
         <!-- 手动表单区域 -->
         <div class="bg-white rounded-3xl p-5 shadow-sm mb-6" :class="savedFoods.length === 0 ? 'mt-4' : ''">
             <div class="flex justify-between items-center mb-4">
                <h3 class="font-bold text-gray-700 text-sm">自定义添加</h3>
                <van-radio-group v-model="addMode" direction="horizontal" class="!scale-85">
                  <van-radio name="food" checked-color="#ea580c" class="!text-xs">记录食物</van-radio>
                  <van-radio name="template" checked-color="#ea580c" class="!text-xs">保存模板</van-radio>
                </van-radio-group>
             </div>
             
             <van-form ref="manualFormRef">
               <van-cell-group inset class="!mx-0 border border-gray-100 mb-3">
                 <van-field v-model="manualForm.food_name" name="food_name" :label="addMode === 'template' ? '模板名称' : '食物名称'" placeholder="输入名称" :rules="[{ required: true, message: '请填写名称' }]" />
                 
                 <!-- 能量字段，支持单位切换 -->
                 <van-field v-model="manualForm.kcal" type="number" name="kcal" :label="addMode === 'template' ? '能量/100g' : '热量'" placeholder="必填" :rules="[{ required: true, message: '请填写数值' }]" class="items-center">
                   <template #button>
                     <div class="flex bg-gray-100 rounded-lg p-0.5 ml-1">
                       <button type="button" class="px-2 py-0.5 text-[10px] rounded-md transition-all font-bold" :class="manualForm.unit === 'kJ' ? 'bg-orange-500 text-white' : 'text-gray-500'" @click="manualForm.unit = 'kJ'">kJ</button>
                       <button type="button" class="px-2 py-0.5 text-[10px] rounded-md transition-all font-bold" :class="manualForm.unit === 'kcal' ? 'bg-orange-500 text-white' : 'text-gray-500'" @click="manualForm.unit = 'kcal'">kcal</button>
                     </div>
                   </template>
                 </van-field>

                 <van-field v-model="manualForm.protein" type="number" :label="addMode === 'template' ? '蛋白质/100g' : '蛋白质(g)'" placeholder="选填" />
                 <van-field v-model="manualForm.fat" type="number" :label="addMode === 'template' ? '脂肪/100g' : '脂肪(g)'" placeholder="选填" />
                 <van-field v-model="manualForm.carb" type="number" :label="addMode === 'template' ? '碳水/100g' : '碳水(g)'" placeholder="选填" />
                 
                 <!-- 🕰️ 补录时间 -->
                 <van-field v-model="logTime" is-link readonly label="摄入时间" placeholder="不填默认当前时间" @click="showTimePicker = true" />
               </van-cell-group>
               
               <!-- 仅在记录食物时显示保存常用 -->
               <div v-if="addMode === 'food'" class="py-2 mb-4">
                  <van-checkbox v-model="manualForm.save_quick" shape="square" checked-color="#f97316">
                    <span class="text-sm text-gray-600">保存到「我的常用」以便下次快捷记录</span>
                  </van-checkbox>
               </div>
               
               <van-button round block type="primary" color="linear-gradient(to right, #fb923c, #ef4444)" :loading="isSubmitting" @click="onSubmitManual">
                 {{ addMode === 'template' ? '确认保存模板' : '记录到今日摄入' }}
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
          今天还没有摄入记录，快去记录第一餐吧
       </div>
       <div v-else class="space-y-3">
          <div v-for="log in dailyLogs" :key="log.id" class="bg-white rounded-2xl p-4 shadow-sm flex flex-row items-center justify-between border-l-4 border-orange-400 relative">
             <!-- 删除按钮 -->
             <div class="absolute top-2 right-2 text-gray-300 hover:text-red-500 cursor-pointer p-1 active:scale-95 transition-all" @click.stop="deleteLog(log.id)">
                <van-icon name="delete-o" class="text-xs" />
             </div>
             
             <div class="flex-1">
                <div class="flex items-center gap-2 mb-1.5">
                   <span class="text-xs text-orange-500 font-black bg-orange-50 px-2 py-0.5 rounded mr-1 tracking-wider">{{log.time || '--:--'}}</span>
                   <span class="font-bold text-gray-800 text-md">{{log.food_name}}</span>
                </div>
                <div class="text-xs text-gray-500 flex gap-3">
                   <span v-if="log.macros?.protein !== undefined">蛋白: {{ Number(log.macros.protein).toFixed(1) }}g</span>
                   <span v-if="log.macros?.fat !== undefined">脂肪: {{ Number(log.macros.fat).toFixed(1) }}g</span>
                   <span v-if="log.macros?.carb !== undefined">碳水: {{ Number(log.macros.carb).toFixed(1) }}g</span>
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

    <!-- 配料表食物选量记录弹窗 -->
    <van-popup v-model:show="showPortionModal" round position="bottom" class="p-5 bg-gray-50 flex flex-col rounded-t-3xl">
      <div class="flex justify-between items-center mb-4">
        <span class="font-extrabold text-lg text-gray-800">秤 记录「{{ selectedTemplate?.name }}」</span>
        <van-icon name="cross" class="text-gray-400 text-lg cursor-pointer" @click="showPortionModal = false" />
      </div>
      
      <div class="bg-white rounded-2xl p-4 shadow-sm mb-4 border border-gray-100">
        <div class="text-center text-xs text-gray-400 mb-3">💡 该食物按每100g计，请输入本次食用克数</div>
        <van-cell-group inset class="!mx-0 border-0">
          <van-field v-model="currentPortion" type="number" label="食用重量(g)" placeholder="请输入本次摄入的重量（克）" class="!bg-gray-50 rounded-lg" />
        </van-cell-group>
        
        <!-- 弹口也加一个补录时间 -->
        <div class="mt-3 px-1">
          <van-field v-model="logTime" is-link readonly label="摄入时间" placeholder="不填默认当前时间" @click="showTimePicker = true" class="!bg-gray-50 rounded-lg" />
        </div>
      </div>

      <div>
        <van-button round block type="primary" color="linear-gradient(to right, #fb923c, #ef4444)" @click="addTemplateLog">
          确认记录
        </van-button>
      </div>
    </van-popup>

    <!-- 🕰️ 时间选择器弹窗 -->
    <van-popup v-model:show="showTimePicker" round position="bottom">
      <van-time-picker v-model="currentTimeArray" title="选择摄入时间" @confirm="onConfirmTime" @cancel="showTimePicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
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

const targetKcal = ref(2000) // 🌟 每日目标热量
const searchQuery = ref('') // 🌟 过滤搜索框

const addMode = ref('food') // 'food' 记录食物, 'template' 保存模板

const manualForm = ref({
  food_name: '',
  kcal: '',
  protein: '',
  fat: '',
  carb: '',
  unit: 'kJ',
  save_quick: false
})

const logTime = ref('') // 🌟 自定义补录时间
const showTimePicker = ref(false)
const currentTimeArray = ref([]) // ['11', '40']

const onConfirmTime = ({ selectedValues }) => {
    logTime.value = selectedValues.join(':')
    showTimePicker.value = false
}

const fetchConfig = async () => {
    try {
        const res = await fetch('/api/config')
        if (res.ok) {
            const data = await res.json()
            targetKcal.value = data.target_kcal || 2000
        }
    } catch (e) { }
}

const totalKcal = computed(() => {
    return dailyLogs.value.reduce((acc, log) => acc + log.kcal, 0)
})

const totalProtein = computed(() => {
    return dailyLogs.value.reduce((acc, log) => acc + (log.macros?.protein || 0), 0)
})

const totalFat = computed(() => {
    return dailyLogs.value.reduce((acc, log) => acc + (log.macros?.fat || 0), 0)
})

const totalCarb = computed(() => {
    return dailyLogs.value.reduce((acc, log) => acc + (log.macros?.carb || 0), 0)
})

const kcalPercentage = computed(() => {
    if (targetKcal.value === 0) return 0
    return Math.min(100, Math.round((totalKcal.value / targetKcal.value) * 100))
})

const normalSavedFoods = computed(() => {
    return savedFoods.value.filter(f => !f.is_per_100g && (f.name.toLowerCase().includes(searchQuery.value.toLowerCase())))
})

const templateSavedFoods = computed(() => {
    return savedFoods.value.filter(f => f.is_per_100g && (f.name.toLowerCase().includes(searchQuery.value.toLowerCase())))
})

const fillForm = (food) => {
    manualForm.value.food_name = food.food_name || food.name
    manualForm.value.kcal = String(food.kcal)
    manualForm.value.protein = food.macros?.protein !== undefined ? String(food.macros.protein) : (food.protein !== undefined ? String(food.protein) : '')
    manualForm.value.fat = food.macros?.fat !== undefined ? String(food.macros.fat) : (food.fat !== undefined ? String(food.fat) : '')
    manualForm.value.carb = food.macros?.carb !== undefined ? String(food.macros.carb) : (food.carb !== undefined ? String(food.carb) : '')
}

const onSubmitManual = async () => {
    if (!manualForm.value.food_name || !manualForm.value.kcal) {
        alert("请填写名称和热量")
        return
    }
    
    isSubmitting.value = true
    const isKj = manualForm.value.unit === 'kJ'
    const energyValue = parseFloat(manualForm.value.kcal)
    const finalKcal = Math.round(isKj ? (energyValue / 4.184) : energyValue)
    
    const proteinVal = manualForm.value.protein ? parseFloat(manualForm.value.protein) : ''
    const fatVal = manualForm.value.fat ? parseFloat(manualForm.value.fat) : ''
    const carbVal = manualForm.value.carb ? parseFloat(manualForm.value.carb) : ''

    const logData = {
        food_name: manualForm.value.food_name,
        kcal: finalKcal,
        macros: { 
            protein: proteinVal !== '' ? proteinVal : 0, 
            fat: fatVal !== '' ? fatVal : 0, 
            carb: carbVal !== '' ? carbVal : 0 
        },
        time: logTime.value || null // 🌟 传自定义时间
    }

    if (addMode.value === 'food') {
        try {
            const res = await fetch('/api/intake/logs', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(logData)
            })
            if (res.ok) { await fetchLogs(); await fetchHistory(); }
        } catch (e) { }

        if (manualForm.value.save_quick) {
            try {
                await fetch('/api/intake/saved_foods', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: manualForm.value.food_name,
                        kcal: finalKcal,
                        protein: proteinVal !== '' ? proteinVal : 0,
                        fat: fatVal !== '' ? fatVal : 0,
                        carb: carbVal !== '' ? carbVal : 0,
                        is_per_100g: false
                    })
                })
                fetchSavedFoods()
            } catch(e) {}
        }
    } else {
         try {
             const res = await fetch('/api/intake/saved_foods', {
                 method: 'POST',
                 headers: {'Content-Type': 'application/json'},
                 body: JSON.stringify({
                     name: manualForm.value.food_name,
                     kcal: finalKcal,
                     protein: proteinVal !== '' ? proteinVal : 0,
                     fat: fatVal !== '' ? fatVal : 0,
                     carb: carbVal !== '' ? carbVal : 0,
                     is_per_100g: true
                 })
             })
             if (res.ok) {
                 await fetchSavedFoods()
                 alert("保存配料表模板成功！已添加到上方配料表。")
                 addMode.value = 'food'
             }
         } catch(e) {}
    }

    manualForm.value = { food_name: '', kcal: '', protein: '', fat: '', carb: '', unit: 'kJ', save_quick: false }
    logTime.value = '' // 清空
    isSubmitting.value = false
}

const showPortionModal = ref(false)
const selectedTemplate = ref(null)
const currentPortion = ref('')

const onTemplateClick = (food) => {
    if (food.is_per_100g) {
        selectedTemplate.value = food
        currentPortion.value = ''
        logTime.value = '' // 重置时间
        showPortionModal.value = true
    } else {
        quickAdd(food)
    }
}

const addTemplateLog = async () => {
    if (!currentPortion.value) {
        alert('请输入本次摄入的克数')
        return
    }
    const ratio = parseFloat(currentPortion.value) / 100
    const food = selectedTemplate.value
    
    const logData = {
        food_name: food.name,
        kcal: Math.round(food.kcal * ratio),
        macros: {
            protein: food.protein ? Math.round(food.protein * ratio * 10)/10 : 0,
            fat: food.fat ? Math.round(food.fat * ratio * 10)/10 : 0,
            carb: food.carb ? Math.round(food.carb * ratio * 10)/10 : 0
        },
        time: logTime.value || null // 🌟 传自定义时间
    }
    try {
        const res = await fetch('/api/intake/logs', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(logData)
        })
        if (res.ok) {
            await fetchLogs()
            showPortionModal.value = false
            logTime.value = ''
        } else {
            alert('记录失败')
        }
    } catch(e) { }
}

const quickAdd = async (food) => {
    const logData = {
        food_name: food.name,
        kcal: food.kcal,
        macros: {
            protein: food.protein || 0,
            fat: food.fat || 0,
            carb: food.carb || 0
        },
        time: null // 🌟 快捷记录默认为当前
    }
    try {
        const res = await fetch('/api/intake/logs', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(logData)
        })
        if (res.ok) { await fetchLogs() }
    } catch (e) { }
}

const deleteSavedFood = async (id) => {
    if (!window.confirm('确定要删除这个常备模板吗？')) return
    try {
        const res = await fetch(`/api/intake/saved_foods/${id}`, { method: 'DELETE' })
        if (res.ok) fetchSavedFoods()
    } catch (e) { }
}

const fetchLogs = async () => {
    try {
        const res = await fetch('/api/intake/logs')
        if (res.ok) {
            const data = await res.json()
            dailyLogs.value = Array.isArray(data) ? data.reverse() : []
        }
    } catch (e) { }
}

const deleteLog = async (logId) => {
    if (!window.confirm('确定要删除这条饮食记录吗？')) return
    try {
        const res = await fetch(`/api/intake/logs/${logId}`, { method: 'DELETE' })
        if (res.ok) fetchLogs()
    } catch (e) { }
}

const fetchSavedFoods = async () => {
    try {
        const res = await fetch('/api/intake/saved_foods')
        if (res.ok) savedFoods.value = await res.json()
    } catch (e) { }
}

const fetchHistory = async () => {
    try {
        const res = await fetch('/api/intake/history')
        if (res.ok) recentFoods.value = await res.json()
    } catch (e) { }
}

const saveAiLogAndReset = async () => {
    if (!result.value || result.value.error) { reset(); return; }
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
        if (res.ok) { await fetchLogs(); await fetchHistory(); }
    } catch (e) { }

    if (saveAiQuick.value) {
        try {
            await fetch('/api/intake/saved_foods', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: result.value.name || '未知食物',
                    kcal: result.value.kcal || 0,
                    protein: result.value.protein || 0,
                    fat: result.value.fat || 0,
                    carb: result.value.carb || 0,
                    is_per_100g: false
                })
            })
            await fetchSavedFoods()
        } catch(e) {}
    }
    saveAiQuick.value = false
    reset()
}

const beforeRead = (file) => {
  return new Promise((resolve) => {
    new Compressor(file, {
      quality: 0.6,
      maxWidth: 800,
      success(result) { resolve(new File([result], file.name, { type: result.type })); },
      error(err) { resolve(file); },
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: foodText.value.trim() })
    })
    const data = await response.json()
    if (!response.ok) throw new Error()
    result.value = data
  } catch (error) { result.value = { error: '识别失败' } } 
  finally { analyzing.value = false }
}

const onRead = async (fileInfo) => {
  const base64Data = fileInfo.content
  if (!base64Data) return
  analyzing.value = true; result.value = null;
  try {
    const response = await fetch('/api/intake/identify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: base64Data })
    })
    const data = await response.json()
    result.value = data
  } catch (error) { } 
  finally { analyzing.value = false }
}

const reset = () => { fileList.value = []; result.value = null; }

onMounted(() => {
    fetchLogs()
    fetchSavedFoods()
    fetchHistory()
    fetchConfig() // 🌟
})
</script>
