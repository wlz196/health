<template>
  <div class="p-4 bg-gray-50 min-h-screen pb-20">
    <h1 class="text-3xl font-extrabold text-gray-800 tracking-tight mb-2 mt-2">体重管理</h1>
    <p class="text-gray-500 text-sm mb-6">了解您的体脂与体型趋势</p>
    
    <!-- 录入卡片 -->
    <div class="bg-white rounded-3xl p-5 shadow-sm mb-6">
       <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800 text-sm">打卡今日体重</h2>
          <span class="text-xs text-gray-400">{{ todayStr }}</span>
       </div>
       <div class="flex gap-3">
          <van-field v-model="currentWeight" type="number" placeholder="输入体重 (kg)" class="bg-gray-50 rounded-xl" />
          <van-button type="primary" color="linear-gradient(to right, #10b981, #059669)" class="rounded-xl font-bold px-6" :loading="submitting" @click="submitWeight">记录</van-button>
       </div>
    </div>

    <!-- 趋势图卡片 -->
    <div class="bg-white rounded-3xl p-5 shadow-sm mb-6" v-if="logs.length > 1">
       <h2 class="text-sm font-bold text-gray-700 mb-4">趋势分析 (近10天)</h2>
       <div class="relative w-full h-48 mt-2">
          <!-- SVG Line Chart -->
          <svg viewBox="0 0 500 200" width="100%" height="100%">
             <!-- Area Background Gradient -->
             <defs>
                <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                   <stop offset="0%" stop-color="#10b981" stop-opacity="0.15" />
                   <stop offset="100%" stop-color="#10b981" stop-opacity="0" />
                </linearGradient>
             </defs>
             
             <!-- Grid Lines -->
             <line x1="30" y1="20" x2="470" y2="20" stroke="#f3f4f6" stroke-width="1" />
             <line x1="30" y1="90" x2="470" y2="90" stroke="#f3f4f6" stroke-width="1" />
             <line x1="30" y1="160" x2="470" y2="160" stroke="#f3f4f6" stroke-width="1" stroke-dasharray="2,2"/>

             <!-- Graph Path Area -->
             <path :d="areaPath" fill="url(#grad)" />
             <!-- Graph Line -->
             <path :d="linePath" fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
             
             <!-- Dots and Labels -->
             <g v-for="(p, i) in points" :key="i">
                <circle :cx="p.x" :cy="p.y" r="4" fill="#fff" stroke="#10b981" stroke-width="2.5" />
                <text :x="p.x" :y="p.y - 12" text-anchor="middle" font-size="10" fill="#374151" font-weight="800">{{ p.weight }}</text>
                <!-- Date Label -->
                <text :x="p.x" y="178" text-anchor="middle" font-size="8" fill="#9ca3af">{{ p.label }}</text>
             </g>
          </svg>
       </div>
    </div>
    <div v-else-if="logs.length === 1" class="bg-white rounded-3xl p-5 shadow-sm mb-6 text-center text-gray-400 text-sm py-10">
       尚需一条以上记录开启曲线统计视图 📈
    </div>

    <!-- 列表卡片 -->
    <div class="bg-white rounded-3xl p-5 shadow-sm">
       <h2 class="text-sm font-bold text-gray-700 mb-4">历史记录</h2>
       <div v-if="logs.length === 0" class="text-center py-6 text-gray-400 text-sm">暂无体重记录</div>
       <div v-else class="space-y-2">
          <div v-for="log in reversedLogs" :key="log.id" class="flex justify-between items-center bg-gray-50 px-4 py-3 rounded-xl relative">
             <!-- 删除按钮 -->
             <div class="absolute top-1 right-1 text-gray-300 hover:text-red-500 cursor-pointer p-0.5 active:scale-95" @click.stop="deleteWeight(log.id)">
                <van-icon name="delete-o" class="text-[10px]" />
             </div>
             
             <span class="text-xs text-gray-500 font-medium">{{ log.date }}</span>
             <span class="text-lg font-black text-gray-800 mr-2">{{ log.weight }} <span class="text-xs font-normal text-gray-400">kg</span></span>
          </div>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { showDialog } from 'vant'

const currentWeight = ref('')
const submitting = ref(false)
const logs = ref([])

const todayStr = computed(() => new Date().toISOString().split('T')[0])
const reversedLogs = computed(() => [...logs.value].reverse())

const fetchLogs = async () => {
    try {
        const res = await fetch('/api/weight')
        logs.value = await res.json()
    } catch (e) {
        console.error(e)
    }
}

const deleteWeight = async (id) => {
    // eslint-disable-next-line no-alert
    if (!window.confirm('确定要删除这条体重记录吗？')) return
    try {
        const res = await fetch(`/api/weight/${id}`, { method: 'DELETE' })
        if (res.ok) {
            fetchLogs() // 刷新列表
        } else {
            alert('删除失败')
        }
    } catch (e) {
        console.error(e)
    }
}

const submitWeight = async () => {
    if (!currentWeight.value) return
    
    // 校验今日是否选择了运动模式
    const d = new Date()
    const todayIdx = new Date(d.getTime() - (d.getTimezoneOffset() * 60 * 1000)).toISOString().split('T')[0]
    const dt = localStorage.getItem('dayType_' + todayIdx)
    
    if (!dt) {
        showDialog({
            title: '模式未选择',
            message: '请先前往“健康总览”点选今天的运动模式，以便于精准记录！',
            theme: 'round-button'
        })
        return
    }

    submitting.value = true
    try {
       await fetch('/api/weight', {
           method: 'POST',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify({ 
               weight: parseFloat(currentWeight.value),
               day_type: dt
           })
       })
       currentWeight.value = ''
       await fetchLogs()
    } catch (e) {
       console.error(e)
    } finally {
       submitting.value = false
    }
}

// === SVG Chart Logic ===
const points = computed(() => {
    if (logs.value.length === 0) return []
    const filterLogs = logs.value
    const weights = filterLogs.map(l => l.weight)
    
    // 动态边界
    let minW = Math.min(...weights)
    let maxW = Math.max(...weights)
    if (minW === maxW) {
        minW -= 2; maxW += 2;
    } else {
        minW -= (maxW - minW) * 0.1;
        maxW += (maxW - minW) * 0.1;
    }
    
    return filterLogs.map((l,index) => {
        // X coord: 30 to 470
        const x = filterLogs.length > 1 ? (index / (filterLogs.length - 1)) * 440 + 30 : 250;
        // Y coord: 20 to 160
        const y = 160 - ((l.weight - minW) / (maxW - minW)) * 140;
        const dateParts = l.date.split('-')
        const label = dateParts.length > 2 ? `${dateParts[1]}-${dateParts[2]}` : l.date;
        return { x, y, weight: l.weight, label }
    })
})

const linePath = computed(() => {
    if (points.value.length < 2) return ''
    return 'M ' + points.value.map(p => `${p.x} ${p.y}`).join(' L ')
})

const areaPath = computed(() => {
    if (points.value.length < 2) return ''
    const p = points.value
    const first = p[0]
    const last = p[p.length - 1]
    return `M ${first.x} 160 L ${linePath.value.substring(2)} L ${last.x} 160 Z`
})

onMounted(() => {
    fetchLogs()
})
</script>
