<template>
  <div class="p-4 bg-gray-50 min-h-screen pb-20">
    <div class="flex justify-between items-center mb-2 mt-2">
       <h1 class="text-3xl font-extrabold text-gray-800 tracking-tight">训练记录</h1>
       <!-- 二分化切换 -->
       <div class="flex bg-gray-100 p-0.5 rounded-full border border-gray-200/50">
          <div v-for="cat in ['上半身', '下半身']" :key="cat" 
               @click="currentCategory = cat"
               class="px-4 py-1.5 rounded-full text-xs font-bold cursor-pointer transition-all"
               :class="currentCategory === cat ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-400'">
             {{ cat }}
          </div>
       </div>
    </div>
    <p class="text-gray-500 text-sm mb-6">记录您的力量、负重与训练进度 🏋️‍♂️</p>

    <!-- 录入卡片 -->
    <div class="bg-white rounded-3xl p-5 shadow-sm mb-6">
       <h2 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-1">
          <van-icon name="edit" />打卡今日 {{ currentCategory }}
       </h2>
       <div class="space-y-3">
          <!-- 快捷历史动作 -->
          <div v-if="recentExercises.length > 0" class="flex flex-wrap gap-1.5 pb-1">
             <div v-for="ex in recentExercises" :key="ex.id" 
                  @click="quickFill(ex)"
                  class="bg-indigo-50/50 hover:bg-indigo-50 text-indigo-600 text-[10px] px-2.5 py-1 rounded-full border border-indigo-100/30 cursor-pointer transition-all flex items-center gap-0.5 shadow-sm">
                <span class="opacity-70">#</span> {{ ex.exercise_name }}
             </div>
          </div>

          <van-field v-model="form.exercise_name" label="动作" placeholder="例如：卧推、深蹲" class="bg-gray-50 rounded-xl" />
          <div class="grid grid-cols-3 gap-2">
             <van-field v-model="form.weight" type="number" label="负重" placeholder="kg" class="bg-gray-50 rounded-xl flex-col !items-start" />
             <van-field v-model="form.sets" type="digit" label="组数" placeholder="组" class="bg-gray-50 rounded-xl flex-col !items-start" />
             <van-field v-model="form.reps" type="digit" label="次数" placeholder="次" class="bg-gray-50 rounded-xl flex-col !items-start" />
          </div>
          <van-button type="primary" block color="linear-gradient(to right, #6366f1, #4f46e5)" class="rounded-xl font-bold mt-2" :loading="submitting" @click="submitLog">记录</van-button>
       </div>
    </div>

    <!-- 负重趋势图 -->
    <div class="bg-white rounded-3xl p-5 shadow-sm mb-6" v-if="uniqueExercises.length > 0">
       <div class="flex justify-between items-center mb-4">
          <h2 class="text-sm font-bold text-gray-700">负重随日期变化 📈</h2>
          <!-- 动作选择器 -->
          <select v-model="chartExercise" class="text-xs bg-gray-50 border-gray-100 rounded-lg p-1 text-gray-600 outline-none">
             <option v-for="ex in filteredExercises" :key="ex" :value="ex">{{ ex }}</option>
          </select>
       </div>
       <div class="relative w-full h-40 mt-2" v-if="chartPoints.length > 1">
          <svg viewBox="0 0 500 200" width="100%" height="100%">
             <!-- Grid Lines -->
             <line x1="30" y1="20" x2="470" y2="20" stroke="#f3f4f6" stroke-width="1" />
             <line x1="30" y1="90" x2="470" y2="90" stroke="#f3f4f6" stroke-width="1" />
             <line x1="30" y1="160" x2="470" y2="160" stroke="#f3f4f6" stroke-width="1" stroke-dasharray="2,2"/>
             
             <!-- Graph Path -->
             <path :d="linePath" fill="none" stroke="#6366f1" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
             <g v-for="(p, i) in chartPoints" :key="i">
                <circle :cx="p.x" :cy="p.y" r="4" fill="#fff" stroke="#6366f1" stroke-width="2.5" />
                <text :x="p.x" :y="p.y - 10" text-anchor="middle" font-size="9" fill="#374151" font-weight="bold">{{ p.weight }}</text>
                <!-- Date Label -->
                <text :x="p.x" y="178" text-anchor="middle" font-size="8" fill="#9ca3af">{{ p.label }}</text>
             </g>
          </svg>
       </div>
       <div v-else class="text-center py-10 text-gray-400 text-xs">尚需两条同一动作打卡数据绘制曲线 📊</div>
    </div>

    <!-- 列表卡片 -->
    <div class="bg-white rounded-3xl p-5 shadow-sm">
       <div class="flex justify-between items-center mb-4">
          <h2 class="text-sm font-bold text-gray-700 flex items-center gap-1">
             <van-icon name="todo-list-o" /> {{ currentCategory }}训练历程
          </h2>
       </div>
       <div v-if="loading" class="text-center py-6"><van-loading /></div>
       <div v-else-if="filteredLogs.length === 0" class="text-center py-6 text-gray-400 text-sm">暂无本拆分记录，去撸铁吧！</div>
       <div v-else class="space-y-3">
          <div v-for="lg in filteredLogs" :key="lg.id" class="flex justify-between items-center bg-gray-50 px-4 py-3 rounded-xl border border-gray-100/50 relative">
             <!-- 删除按钮 -->
             <div class="absolute top-1 right-1 text-gray-300 hover:text-red-500 cursor-pointer p-0.5 active:scale-95" @click.stop="deleteExercise(lg.id)">
                <van-icon name="delete-o" class="text-[10px]" />
             </div>
             
             <div>
                <span class="text-sm font-black text-gray-800">{{ lg.exercise_name }}</span>
                <p class="text-[10px] text-gray-400 mt-0.5">{{ lg.date }}</p>
             </div>
             <div class="text-right mr-3">
                <span class="text-lg font-black text-indigo-600">{{ lg.weight }} <span class="text-xs font-normal text-gray-400">kg</span></span>
                <p class="text-[10px] text-gray-500 mt-0.5">{{ lg.sets }}组 x {{ lg.reps }}次</p>
             </div>
          </div>
       </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'

const loading = ref(true)
const submitting = ref(false)
const logs = ref([])
const currentCategory = ref('上半身')
const chartExercise = ref('')

const form = ref({
    exercise_name: '',
    weight: '',
    sets: '',
    reps: ''
})

// === 快捷复用历史记录 ===
const recentExercises = computed(() => {
    const list = []
    const seen = new Set()
    for (const l of logs.value) {
        if (l.category === currentCategory.value && !seen.has(l.exercise_name)) {
            seen.add(l.exercise_name)
            list.push(l)
        }
    }
    return list.slice(0, 6) // 展示最近 6 个常用动作
})

const quickFill = (lg) => {
    form.value.exercise_name = lg.exercise_name
    form.value.weight = lg.weight.toString()
    form.value.sets = lg.sets.toString()
    form.value.reps = lg.reps.toString()
}

// === 分组过滤列表 ===
const filteredLogs = computed(() => {
    return logs.value.filter(l => l.category === currentCategory.value)
})

const uniqueExercises = computed(() => {
    return [...new Set(filteredLogs.value.map(l => l.exercise_name))]
})

const filteredExercises = computed(() => uniqueExercises.value)

// 自动随切换修正默认趋势动作
watch(filteredExercises, (newVal) => {
    if (newVal.length > 0 && !newVal.includes(chartExercise.value)) {
        chartExercise.value = newVal[0]
    }
}, { immediate: true })

const fetchLogs = async () => {
    try {
        const res = await fetch('/api/anaerobic')
        logs.value = await res.json()
    } catch (e) { console.error(e) }
    finally { loading.value = false }
}

const deleteExercise = async (id) => {
    // eslint-disable-next-line no-alert
    if (!window.confirm('确定要删除这条训练记录吗？')) return
    try {
        const res = await fetch(`/api/anaerobic/${id}`, { method: 'DELETE' })
        if (res.ok) {
            fetchLogs() // 刷新列表
        } else {
            alert('删除失败')
        }
    } catch (e) { console.error(e) }
}

const submitLog = async () => {
    const f = form.value
    if (!f.exercise_name || !f.weight || !f.sets || !f.reps) return
    submitting.value = true
    try {
        await fetch('/api/anaerobic', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                exercise_name: f.exercise_name,
                weight: parseFloat(f.weight),
                sets: parseInt(f.sets),
                reps: parseInt(f.reps),
                category: currentCategory.value
            })
        })
        f.exercise_name = ''; f.weight = ''; f.sets = ''; f.reps = ''
        await fetchLogs()
    } catch (e) {
        console.error(e)
    } finally {
        submitting.value = false
    }
}

// === SVG Chart Logic ===
const currentExerciseLogs = computed(() => {
    if (!chartExercise.value) return []
    // 从全量 logs 中拉取（不限当前 category，为了更好的历程曲线）
    return logs.value
       .filter(l => l.exercise_name === chartExercise.value)
       .sort((a,b) => new Date(a.date) - new Date(b.date))
})

const chartPoints = computed(() => {
    const el = currentExerciseLogs.value
    if (el.length === 0) return []
    const weights = el.map(l => l.weight)
    
    let minW = Math.min(...weights)
    let maxW = Math.max(...weights)
    if (minW === maxW) { minW -= 2; maxW += 2; } 
    else { minW -= (maxW - minW) * 0.1; maxW += (maxW - minW) * 0.1; }

    return el.map((l, index) => {
        const x = el.length > 1 ? (index / (el.length - 1)) * 440 + 30 : 250;
        const y = 160 - ((l.weight - minW) / (maxW - minW)) * 140;
        const pts = l.date.split('-')
        const label = pts.length > 2 ? `${pts[1]}-${pts[2]}` : l.date;
        return { x, y, weight: l.weight, label }
    })
})

const linePath = computed(() => {
    if (chartPoints.value.length < 2) return ''
    return 'M ' + chartPoints.value.map(p => `${p.x} ${p.y}`).join(' L ')
})

onMounted(() => {
    fetchLogs()
})
</script>
