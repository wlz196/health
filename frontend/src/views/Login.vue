<template>
  <div class="p-6 bg-gradient-to-br from-indigo-50 via-white to-indigo-50 min-h-screen flex flex-col justify-center items-center pb-20">
    <div class="w-full max-w-sm bg-white rounded-3xl p-6 shadow-xl border border-gray-100/50">
       <div class="text-center mb-6">
          <div class="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg shadow-indigo-200">
             <van-icon name="fire-o" class="text-white text-2xl" />
          </div>
          <h1 class="text-2xl font-black text-gray-800">{{ isLogin ? '欢迎回来' : '创建账号' }}</h1>
          <p class="text-xs text-gray-400 mt-1">{{ isLogin ? '登录后查看您的健康看板' : '加入我们，开启健康生活' }}</p>
       </div>

       <van-form @submit="onSubmit" class="space-y-4">
          <van-field v-model="form.username" name="username" label="用户名" placeholder="请输入用户名" 
                     :rules="[{ required: true, message: '请填写用户名' }]" class="bg-gray-50 rounded-xl" />
          <van-field v-model="form.password" type="password" name="password" label="密码" placeholder="请输入密码" 
                     :rules="[{ required: true, message: '请填写密码' }]" class="bg-gray-50 rounded-xl" />

          <div class="pt-4">
             <van-button round block type="primary" native-type="submit" :loading="loading" color="linear-gradient(to right, #6366f1, #4f46e5)" class="font-bold shadow-lg shadow-indigo-100">
                {{ isLogin ? '登录' : '注册' }}
             </van-button>
          </div>
       </van-form>

       <div class="text-center mt-6">
          <span class="text-xs text-gray-400">{{ isLogin ? '没有账号？' : '已有账号？' }}</span>
          <span @click="isLogin = !isLogin" class="text-xs font-bold text-indigo-600 cursor-pointer hover:underline ml-1">
             {{ isLogin ? '立即注册' : '立即登录' }}
          </span>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'

const router = useRouter()
const isLogin = ref(true)
const loading = ref(false)

const form = ref({
    username: '',
    password: ''
})

const onSubmit = async () => {
    loading.value = true
    const url = isLogin.value ? '/api/login' : '/api/register'
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form.value)
        })
        const data = await res.json()
        
        if (res.status === 200) {
            if (isLogin.value) {
                // 保存 Token 
                localStorage.setItem('token', data.access_token)
                localStorage.setItem('username', data.username)
                showSuccessToast('登录成功')
                router.push('/overview')
            } else {
                showSuccessToast('注册成功，请登录')
                isLogin.value = true
            }
        } else {
            showFailToast(data.detail || '发生错误')
        }
    } catch (e) {
        showFailToast('网络错误')
    } finally {
        loading.value = false
    }
}
</script>
