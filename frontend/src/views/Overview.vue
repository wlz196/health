<template>
  <div class="p-4 bg-gray-50 min-h-screen">
    <div class="flex justify-between items-center mb-6 mt-2">
      <h1 class="text-3xl font-extrabold text-gray-800 tracking-tight">健康总览</h1>
      <div v-if="loading" class="text-sm text-gray-500 flex items-center">
        <van-loading size="16px" class="mr-1"/> 同步中
      </div>
      <div v-else class="flex items-center gap-2">
         <div @click="showSettings = true" class="bg-indigo-50/80 text-indigo-600 px-3 py-1.5 rounded-full flex items-center gap-1 cursor-pointer border border-indigo-100/50 hover:bg-indigo-100 transition-all text-[11px] font-medium shadow-sm">
            <van-icon name="setting-o" class="text-xs" />
            <span>设置基础代谢</span>
         </div>
      </div>
    </div>

    <div v-if="!loading" class="space-y-4">
      <!-- 核心热量环形卡片区 (利用 Tailwind 完成精美渐变) -->
      <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden">
        <div class="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-white opacity-10 rounded-full blur-xl"></div>
        <div class="flex justify-between items-start mb-3">
           <div>
              <h2 class="text-xs font-medium opacity-80 mb-1">今日建议摄入热量</h2>
              <div class="text-5xl font-black tracking-tighter">{{ targetKcal }}</div>
           </div>
           <div class="bg-white/10 backdrop-blur-md px-3 py-1.5 rounded-full text-[11px] font-bold self-start mt-1 flex items-center gap-1 border border-white/5">
              <span class="opacity-80">缺口</span>
              <span class="font-black" :class="currentDeficit >= 0 ? '!text-green-300' : '!text-rose-300'">
                 {{ Math.round((1 - currentConfig.qPct) * 100) }}% TDEE
              </span>
           </div>
        </div>
        
        <!-- 进度条可视化 -->
        <div class="mt-4 pt-4 border-t border-white/10">
           <div class="flex justify-between text-xs opacity-90 mb-1.5">
              <span>已吃: <strong class="text-white">{{ metrics.consumedKilocalories || 0 }}</strong> kcal</span>
              <span>目标: <strong class="text-white">{{ targetKcal }}</strong> kcal</span>
           </div>
           <div class="w-full h-2.5 bg-white/15 rounded-full overflow-hidden">
              <div class="h-full bg-gradient-to-r from-emerald-400 to-green-300 rounded-full transition-all duration-500" 
                   :style="{ width: Math.min(100, (((metrics.consumedKilocalories || 0) / targetKcal) * 100)) + '%' }"></div>
           </div>
        </div>

        <!-- BMR & TDEE 辅助小卡数据 -->
        <div class="flex justify-between text-[10px] mt-3 pt-3 border-t border-white/10 opacity-80">
           <div>
              <span>基础代谢 BMR: </span>
              <strong class="text-white font-black">{{ metrics.bmrKilocalories || '---' }}</strong> <span class="opacity-60">kcal</span>
           </div>
           <div>
              <span>预估总消耗 TDEE: </span>
              <strong class="text-white font-black">{{ Math.round(metrics.tdeeKilocalories || 0) }}</strong> <span class="opacity-60">kcal</span>
           </div>
        </div>
      </div>

      <!-- 今日模式点选 -->
      <div class="bg-white rounded-3xl p-5 shadow-sm space-y-4 mb-4">
         <h2 class="text-xs font-bold text-gray-400 tracking-wider">今日运动模式</h2>
         <div class="grid grid-cols-5 gap-2">
            <div v-for="(cfg, key) in dayTypes" :key="key" 
                 @click="dayType = key"
                 class="p-2 rounded-xl text-center cursor-pointer transition-all flex flex-col items-center justify-center border"
                 :class="dayType === key ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-gray-50 border-gray-100 text-gray-500'">
               <span class="text-xs font-bold">{{ cfg.name }}</span>
               <span class="text-[9px] mt-0.5 opacity-70">✖️{{ cfg.qPct }}</span>
            </div>
         </div>
         <div class="bg-indigo-50/50 p-3 rounded-xl border border-indigo-100/50">
            <p class="text-[11px] text-indigo-800 font-medium flex items-center gap-1">
               <span>🎯 目标摄入:</span> 
               <span class="font-bold text-indigo-600">{{ targetKcal }} kcal</span>
            </p>
            <p class="text-[10px] text-gray-400 mt-1 leading-relaxed">{{ currentConfig.tip }}</p>
         </div>
      </div>

      <!-- 营养素分配卡片 -->
      <div class="bg-white rounded-3xl p-5 shadow-sm space-y-3">
         <!-- 营养素分配进度 -->
         <div class="pt-2">
            <div class="flex justify-between items-center mb-3">
               <span class="text-xs text-gray-500 font-bold">建议三大营养素分配 (克)</span>
            </div>
            <div class="space-y-3 text-[11px]">
               <!-- 碳水 -->
               <div>
                  <div class="flex justify-between mb-1">
                     <span class="text-sky-700 font-medium">🌾 碳水 (Carb)</span>
                     <span class="text-gray-400">{{ metrics.consumedMacros?.carb || 0 }} / {{ macroAlloc.carb }} g</span>
                  </div>
                  <div class="w-full h-1.5 bg-sky-50 rounded-full overflow-hidden border border-sky-100/20">
                     <div class="h-full bg-gradient-to-r from-sky-400 to-sky-500 rounded-full transition-all" 
                          :style="{ width: Math.min(100, (((metrics.consumedMacros?.carb || 0) / (macroAlloc.carb || 1)) * 100)) + '%' }"></div>
                  </div>
               </div>

               <!-- 蛋白 -->
               <div>
                  <div class="flex justify-between mb-1">
                     <span class="text-rose-700 font-medium">🥩 蛋白质 (Prot)</span>
                     <span class="text-gray-400">{{ metrics.consumedMacros?.protein || 0 }} / {{ macroAlloc.protein }} g</span>
                  </div>
                  <div class="w-full h-1.5 bg-rose-50 rounded-full overflow-hidden border border-rose-100/20">
                     <div class="h-full bg-gradient-to-r from-rose-400 to-rose-500 rounded-full transition-all" 
                          :style="{ width: Math.min(100, (((metrics.consumedMacros?.protein || 0) / (macroAlloc.protein || 1)) * 100)) + '%' }"></div>
                  </div>
               </div>

               <!-- 脂肪 -->
               <div>
                  <div class="flex justify-between mb-1">
                     <span class="text-amber-700 font-medium">🥑 脂肪 (Fat)</span>
                     <span class="text-gray-400">{{ metrics.consumedMacros?.fat || 0 }} / {{ macroAlloc.fat }} g</span>
                  </div>
                  <div class="w-full h-1.5 bg-amber-50 rounded-full overflow-hidden border border-amber-100/20">
                     <div class="h-full bg-gradient-to-r from-amber-400 to-amber-500 rounded-full transition-all" 
                          :style="{ width: Math.min(100, (((metrics.consumedMacros?.fat || 0) / (macroAlloc.fat || 1)) * 100)) + '%' }"></div>
                  </div>
               </div>
            </div>
         </div>
      </div>

      
    </div>
    <!-- 设置弹窗 -->
    <van-dialog v-model:show="showSettings" title="设置基础数据" show-cancel-button @confirm="saveConfig">
      <div class="px-4 py-2 space-y-2">
         <van-field v-model="heightValue" type="number" label="身高 (cm)" placeholder="请输入身高" class="rounded-xl bg-gray-50 border-0" />
         <van-field v-model="weightValue" type="number" label="体重 (kg)" placeholder="请输入体重" class="rounded-xl bg-gray-50 border-0" />
         <van-field v-model="ageValue" type="digit" label="年龄" placeholder="请输入年龄" class="rounded-xl bg-gray-50 border-0" />
         
         <div class="van-cell van-field border-0 rounded-xl bg-gray-50 !p-3">
            <div class="van-cell__title !w-[80px]"><span>性别</span></div>
            <van-radio-group v-model="genderValue" direction="horizontal">
               <van-radio name="male" icon-size="16px">男</van-radio>
               <van-radio name="female" icon-size="16px">女</van-radio>
            </van-radio-group>
         </div>

         <div class="van-cell van-field border-0 rounded-xl bg-gray-50 flex-col !items-start !p-3">
            <div class="van-cell__title mb-2"><span>活动强度系数</span></div>
            <van-radio-group v-model="multiplierValue" class="space-y-1 w-full text-xs">
               <van-radio name="1.2" icon-size="14px" class="!flex">1.2 - 久坐（基本不运动）</van-radio>
               <van-radio name="1.375" icon-size="14px" class="!flex">1.375 - 轻度（每周1-3天运动）</van-radio>
               <van-radio name="1.55" icon-size="14px" class="!flex">1.55 - 中度（每周3-5天运动）</van-radio>
               <van-radio name="1.725" icon-size="14px" class="!flex">1.725 - 强度（每周6-7天运动）</van-radio>
            </van-radio-group>
         </div>
         <!-- 🔥 直接设定 BMR -->
         <p class="text-[10px] text-gray-400 px-1 mt-1 mb-1">或者：直接设定一个固定 BMR 数值</p>
         <van-field v-model="bmrValue" type="digit" label="固定 BMR" placeholder="基础代谢卡路里" class="rounded-xl bg-gray-50 border-0" />
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'

const loading = ref(true)
const metrics = ref({})
const activities = ref([])

const showSettings = ref(false)
const heightValue = ref('')
const weightValue = ref('')
const ageValue = ref('')
const bmrValue = ref('')
const genderValue = ref('male')
const multiplierValue = ref('1.2')

const fetchConfig = async () => {
  try {
    const res = await fetch('/api/config')
    const data = await res.json()
    heightValue.value = data.height || ''
    weightValue.value = data.weight || ''
    ageValue.value = data.age || ''
    bmrValue.value = data.bmr_kcal ? String(data.bmr_kcal) : ''
    genderValue.value = data.gender || 'male'
    multiplierValue.value = String(data.activity_multiplier || '1.2')
  } catch (e) {
    console.error("加载配置失败:", e)
  }
}

const saveConfig = async () => {
  try {
    const payload = {
        height: heightValue.value ? parseFloat(heightValue.value) : null,
        weight: weightValue.value ? parseFloat(weightValue.value) : null,
        age: ageValue.value ? parseInt(ageValue.value) : null,
        bmr_kcal: bmrValue.value ? parseInt(bmrValue.value) : null,
        gender: genderValue.value,
        activity_multiplier: parseFloat(multiplierValue.value)
    }
    await fetch('/api/config', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    })
    fetchData() 
  } catch (e) {
     console.error("保存配置失败:", e)
  }
}


const remainingKcal = computed(() => {
  const q = targetKcal.value
  const consumed = metrics.value.consumedKilocalories || 0
  return Math.round(q - consumed)
})

const currentDeficit = computed(() => {
  // 修改为按公式结算的 TDEE - 已吃
  const tdee = metrics.value.tdeeKilocalories || (metrics.value.bmrKilocalories || 0)
  const consumed = metrics.value.consumedKilocalories || 0
  return tdee - consumed
})

// === 营养日历与建议模式 ===
const d = new Date()
const todayIdx = new Date(d.getTime() - (d.getTimezoneOffset() * 60 * 1000)).toISOString().split('T')[0]

const dayType = ref(localStorage.getItem('dayType_' + todayIdx) || 'rest')

const dayTypes = {
  leg: { name: '练腿', qPct: 0.90, pFactor: 1.8, fFactor: 0.9, tip: '不设缺口。防止低血糖，保护神经系统。' },
  strength: { name: '胸背', qPct: 0.80, pFactor: 1.8, fFactor: 0.8, tip: '标准缺口。高蛋白维持肌肉量，碳水提供训练爆发力。' },
  cardio: { name: '有氧', qPct: 0.75, pFactor: 1.6, fFactor: 0.75, tip: '高效刷脂。有氧耗大，跑步后饥饿感可用低脂高碳补足。' },
  rest: { name: '休息', qPct: 0.80, pFactor: 1.5, fFactor: 0.8, tip: '低碳修复。压低碳水控血糖，提高蛋白比率修复肌肉。' },
  cheat: { name: '放纵', qPct: 1.05, pFactor: 1.5, fFactor: 0.75, tip: '热量盈余。重启瘦素，打破减慢平台期。' }
}

watch(dayType, (newVal) => {
    localStorage.setItem('dayType_' + todayIdx, newVal)
})

const currentConfig = computed(() => dayTypes[dayType.value])
const tdee = computed(() => metrics.value.tdeeKilocalories || (metrics.value.bmrKilocalories || 0))
const userWeight = computed(() => parseFloat(weightValue.value) || 60)

const targetKcal = computed(() => {
    return Math.round(tdee.value * currentConfig.value.qPct)
})

const macroAlloc = computed(() => {
    const c = currentConfig.value
    const q = targetKcal.value
    const w = userWeight.value
    
    const pGrams = Math.round(w * c.pFactor)
    const fGrams = Math.round(w * c.fFactor)
    const cGrams = Math.round((q - pGrams * 4 - fGrams * 9) / 4)
    
    return {
        protein: pGrams,
        fat: fGrams,
        carb: cGrams < 0 ? 0 : cGrams,
        q: q
    }
})



const fetchData = async () => {
  try {
    const resOverview = await fetch('/api/overview')
    metrics.value = await resOverview.json()
  } catch (e) {
    console.error("加载数据失败:", e)
  }
 finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchConfig()
})
</script>


