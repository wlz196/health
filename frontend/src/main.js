import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

// 引入 Vant 组件
import { Tabbar, TabbarItem, Button, Loading, Circle, Icon, Uploader, Field, CellGroup } from 'vant'
import 'vant/lib/index.css'

const app = createApp(App)

app.use(router)
app.use(Tabbar)
app.use(TabbarItem)
app.use(Button)
app.use(Loading)
app.use(Circle)
app.use(Icon)
app.use(Uploader)
app.use(Field)
app.use(CellGroup)

app.mount('#app')
