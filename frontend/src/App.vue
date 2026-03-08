<template>
  <div class="h-screen flex flex-col bg-gray-50">
    <div class="flex-grow overflow-auto pb-16">
      <router-view></router-view>
    </div>
    <van-tabbar route>
      <van-tabbar-item replace to="/overview" icon="home-o">总览</van-tabbar-item>
      <van-tabbar-item replace to="/anaerobic" icon="fire-o">无氧</van-tabbar-item>
      <van-tabbar-item replace to="/aerobic" icon="location-o">有氧</van-tabbar-item>
      <van-tabbar-item replace to="/intake" icon="photograph">摄入</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
</script>
