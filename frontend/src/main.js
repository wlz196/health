import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

// 引入 Vant 组件
import { Tabbar, TabbarItem, Button, Loading, Circle, Icon, Uploader, Field, CellGroup, Checkbox, Form, Tab, Tabs, Radio, RadioGroup, Dialog, Popup, Tag, Progress, Search, TimePicker } from 'vant'
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
app.use(Checkbox)
app.use(Form)
app.use(Tab)
app.use(Tabs)
app.use(Radio)
app.use(RadioGroup)
app.use(Dialog)
app.use(Popup)
app.use(Tag)
app.use(Progress)
app.use(Search)
app.use(TimePicker)

// === 全局 Fetch 拦截器：自动注入 JWT Token ===
const originalFetch = window.fetch;
window.fetch = async function (...args) {
  let [resource, config] = args;
  
  if (!config) config = {};
  if (!config.headers) {
      config.headers = {};
  } else if (config.headers instanceof Headers) {
      // 如果已经是 Headers 对象，做一下转换或直接 append
      config.headers.append('Authorization', `Bearer ${localStorage.getItem('token')}`);
  }

  const token = localStorage.getItem('token');
  if (token && !(config.headers instanceof Headers)) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  // 保证 JSON 类型安全
  if (!(config.headers instanceof Headers) && !config.headers['Content-Type'] && config.body) {
      config.headers['Content-Type'] = 'application/json';
  }

  const response = await originalFetch(resource, config);

  if (response.status === 401 && typeof resource === 'string' && !resource.includes('/api/login') && !resource.includes('/api/register')) {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      window.location.href = '/login';
  }

  return response;
};

app.mount('#app')
