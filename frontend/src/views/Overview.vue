<template>
  <div class="p-4 bg-gray-50 min-h-screen">
    <div class="flex justify-between items-center mb-6 mt-2">
      <h1 class="text-3xl font-extrabold text-gray-800 tracking-tight">健康总览</h1>
      <div v-if="loading" class="text-sm text-gray-500 flex items-center">
        <van-loading size="16px" class="mr-1"/> 同步中
      </div>
      <div v-else class="text-sm text-gray-500">{{ metrics.date }}</div>
    </div>

    <div v-if="!loading" class="space-y-4">
      <!-- 核心热量环形卡片区 (利用 Tailwind 完成精美渐变) -->
      <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden">
        <div class="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-white opacity-10 rounded-full blur-xl"></div>
        <h2 class="text-lg font-medium opacity-90 mb-1">今日可摄入热量 (千卡)</h2>
        <div class="text-5xl font-black mb-4 tracking-tighter">
          {{ remainingKcal }}
        </div>
        
        <div class="flex justify-between text-sm mt-4 pt-4 border-t border-white/20">
          <div class="flex items-center">
             <span class="w-2 h-2 rounded-full bg-green-300 mr-2"></span>
             <span>基础: {{ Math.round(metrics.bmrKilocalories || 0) }}</span>
          </div>
          <div class="flex items-center">
             <span class="w-2 h-2 rounded-full bg-yellow-300 mr-2"></span>
             <span>活动: {{ Math.round(metrics.activeKilocalories || 0) }}</span>
          </div>
        </div>
      </div>

      <!-- 步数目标卡片 -->
      <div class="bg-white rounded-2xl p-5 shadow-[0_4px_20px_rgba(0,0,0,0.03)] flex items-center justify-between">
        <div>
          <h3 class="text-gray-500 font-medium text-sm mb-1">今日步数</h3>
          <div class="flex items-end">
             <span class="text-2xl font-bold text-gray-800 mr-1">{{ metrics.totalSteps || 0 }}</span>
             <span class="text-xs text-gray-400 mb-1">/ {{ metrics.stepGoal || 0 }} 步</span>
          </div>
        </div>
        <div class="w-16 h-16">
           <van-circle
            v-model:current-rate="stepRate"
            :rate="100"
            :speed="100"
            :color="gradientColor"
            :text="stepRateText"
            size="64px"
          />
        </div>
      </div>
      
      <!-- 睡眠数据卡片 -->
      <div v-if="metrics.sleepHrs > 0" class="bg-white rounded-2xl p-5 shadow-[0_4px_20px_rgba(0,0,0,0.03)] relative overflow-hidden">
        <div class="absolute right-0 top-0 mt-4 mr-4 w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center opacity-50">🌙</div>
        <div class="flex justify-between items-center mb-3">
            <h3 class="text-gray-500 font-medium text-sm">昨日睡眠</h3>
            <span v-if="metrics.sleepScore" class="bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded-full font-bold">分数: {{ metrics.sleepScore }}</span>
        </div>
        <div class="flex items-end mb-3">
           <span class="text-2xl font-bold text-gray-800 mr-1">{{ metrics.sleepHrs }}</span>
           <span class="text-sm text-gray-400 mb-1">小时</span>
        </div>
        <div class="flex gap-4 text-xs font-medium">
            <div class="flex items-center text-blue-600">
               <span class="w-2 h-2 rounded-full bg-blue-500 mr-1 opacity-80"></span>
               深睡 {{ Math.round(metrics.deepSleepMins / 60) }}h{{ metrics.deepSleepMins % 60 }}m
            </div>
            <div class="flex items-center text-teal-600">
               <span class="w-2 h-2 rounded-full bg-teal-400 mr-1 opacity-80"></span>
               浅睡 {{ Math.round(metrics.lightSleepMins / 60) }}h{{ metrics.lightSleepMins % 60 }}m
            </div>
        </div>
      </div>
      <div v-else class="bg-white rounded-2xl p-5 shadow-[0_4px_20px_rgba(0,0,0,0.03)] flex flex-col items-center justify-center text-gray-400 py-6">
          <p class="text-sm">暂无睡眠数据记录或未同步</p>
      </div>

      <!-- 网格数据统计区 (有氧、无氧与摄入) -->
      <div class="grid grid-cols-2 gap-4">
        <!-- 摄入 -->
        <div class="bg-orange-50 rounded-2xl p-4 shadow-sm border border-orange-100 flex flex-col justify-between">
          <div class="flex items-center text-orange-600 mb-2">
            <van-icon name="like" class="mr-1" />
            <span class="text-xs font-bold">今日摄入</span>
          </div>
          <div>
            <span class="text-2xl font-black text-orange-700">{{ metrics.consumedKilocalories || 0 }}</span>
            <span class="text-xs text-orange-500 ml-1">kcal</span>
          </div>
        </div>

        <!-- 有氧 -->
        <div class="bg-blue-50 rounded-2xl p-4 shadow-sm border border-blue-100 flex flex-col justify-between">
          <div class="flex items-center text-blue-600 mb-2">
            <van-icon name="hot" class="mr-1" />
            <span class="text-xs font-bold">今日有氧</span>
          </div>
          <div>
            <span class="text-2xl font-black text-blue-700">{{ todayAerobicCalories }}</span>
            <span class="text-xs text-blue-500 ml-1">kcal</span>
          </div>
        </div>

        <!-- 无氧 -->
        <div class="bg-purple-50 rounded-2xl p-4 shadow-sm border border-purple-100 flex flex-col justify-between col-span-2">
          <div class="flex items-center text-purple-600 mb-2">
            <van-icon name="fire" class="mr-1" />
            <span class="text-xs font-bold">今日无氧</span>
          </div>
          <div class="flex justify-between items-end">
             <div>
                <span class="text-2xl font-black text-purple-700">{{ todayAnaerobicCalories }}</span>
                <span class="text-xs text-purple-500 ml-1">kcal</span>
             </div>
             <div class="text-sm text-purple-600 opacity-80" v-if="todayAnaerobicCount > 0">
               {{ todayAnaerobicCount }} 次训练
             </div>
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const loading = ref(true)
const metrics = ref({})
const activities = ref([])

const stepRate = computed(() => {
  if (!metrics.value.totalSteps || !metrics.value.stepGoal) return 0;
  return Math.min(100, Math.round((metrics.value.totalSteps / metrics.value.stepGoal) * 100))
})

const stepRateText = computed(() => {
  return `${stepRate.value}%`
})

const gradientColor = {
  '0%': '#3fecad',
  '100%': '#20e3b2',
}

const remainingKcal = computed(() => {
  const totalBurned = (metrics.value.bmrKilocalories || 0) + (metrics.value.activeKilocalories || 0)
  const consumed = metrics.value.consumedKilocalories || 0
  return Math.round(totalBurned - consumed)
})

// === 获取今日活动汇总 ===
// 这里筛选出与今天日期匹配的运动记录
const todayActivities = computed(() => {
  if (!metrics.value.date) return []
  return activities.value.filter(a => {
    // a.startTimeLocal 格式如 "2023-10-15T08:30:00"
    return a.startTimeLocal && a.startTimeLocal.startsWith(metrics.value.date)
  })
})

const todayAerobicCalories = computed(() => {
  const aerobicTypes = ['running', 'cycling', 'walking', 'swimming']
  return todayActivities.value
    .filter(a => aerobicTypes.includes(a.type))
    .reduce((sum, a) => sum + (a.calories || 0), 0)
})

const todayAnaerobicActivities = computed(() => {
  const anaerobicTypes = ['strength_training', 'fitness_equipment']
  return todayActivities.value.filter(a => anaerobicTypes.includes(a.type))
})

const todayAnaerobicCalories = computed(() => {
  return todayAnaerobicActivities.value.reduce((sum, a) => sum + (a.calories || 0), 0)
})

const todayAnaerobicCount = computed(() => {
  return todayAnaerobicActivities.value.length
})


const fetchData = async () => {
  try {
    // 并行请求 Overview与近期活动 
    const [resOverview, resActivities] = await Promise.all([
        fetch('http://127.0.0.1:8080/api/overview'),
        fetch('http://127.0.0.1:8080/api/activities')
    ])
    
    metrics.value = await resOverview.json()
    activities.value = await resActivities.json()
  } catch (e) {
    console.error("加载数据失败:", e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>


