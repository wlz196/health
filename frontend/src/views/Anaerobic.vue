<template>
  <div class="p-4 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-extrabold text-gray-800 tracking-tight mb-6 mt-2">无氧消耗</h1>
    <div v-if="loading" class="text-center py-10"><van-loading /></div>
    <div v-else class="space-y-4">
      <div v-for="act in anaerobicActivities" :key="act.id" class="bg-white rounded-2xl p-5 shadow-sm flex justify-between items-center">
        <div>
          <h3 class="font-bold text-gray-800">{{ act.name }}</h3>
          <p class="text-xs text-gray-400 mt-1">{{ new Date(act.startTimeLocal).toLocaleString() }}</p>
        </div>
        <div class="text-right">
          <div class="text-lg font-black text-indigo-600">{{ act.calories || 0 }} <span class="text-sm font-normal text-gray-500">kcal</span></div>
          <div class="text-sm text-gray-500">{{ act.durationMinutes }} min</div>
        </div>
      </div>
      <div v-if="!anaerobicActivities.length" class="text-center text-gray-400 py-10">近 10 次运动中无此类记录</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const activities = ref([])
const loading = ref(true)

const anaerobicActivities = computed(() => {
  return activities.value.filter(a => a.type === 'strength_training' || a.type === 'fitness_equipment')
})

onMounted(async () => {
  try {
    const res = await fetch('http://127.0.0.1:8080/api/activities')
    activities.value = await res.json()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>
