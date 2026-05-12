<template>
  <div class="login-container">
    <!-- 左侧布局 - 展示网站 LOGO 和主题 -->
    <div class="login-left">
      <div class="login-brand">
        <t-icon name="article" size="80px" class="brand-icon" />
        <h1 class="brand-title">ELEVEN Blog Tuner</h1>
        <p class="brand-subtitle">AI 博客生成助手</p>
        <p class="brand-desc">智能化内容创作，让写作更高效</p>
      </div>
    </div>

    <!-- 右侧布局 - 登录表单 -->
    <div class="login-right">
      <div class="login-form-wrapper">
        <transition name="form-fade" mode="out-in">
          <div :key="isRegister ? 'register' : 'login'" class="form-container">
            <div class="login-header">
              <h2>{{ isRegister ? '注册账号' : '欢迎回来' }}</h2>
              <p>{{ isRegister ? '创建您的新账号' : '请登录您的账号' }}</p>
            </div>

            <t-form ref="formRef" :data="formData" :rules="rules" @submit="handleSubmit" class="login-form">
              <t-form-item label="邮箱" name="email">
                <t-input v-model="formData.email" placeholder="请输入邮箱" size="large">
                  <template #prefix-icon>
                    <t-icon name="mail" />
                  </template>
                </t-input>
              </t-form-item>

              <t-form-item label="密码" name="password">
                <t-input v-model="formData.password" type="password" placeholder="请输入密码" size="large" show-password>
                  <template #prefix-icon>
                    <t-icon name="lock-on" />
                  </template>
                </t-input>
              </t-form-item>

              <t-form-item v-if="isRegister">
                <t-checkbox v-model="agreed">我已阅读并同意相关条款</t-checkbox>
              </t-form-item>

              <t-form-item>
                <t-button type="submit" theme="primary" size="large" block :loading="loading">
                  {{ isRegister ? '注册' : '登录' }}
                </t-button>
              </t-form-item>
            </t-form>

            <div class="login-footer">
              <t-link @click="toggleMode" theme="primary">
                {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
              </t-link>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)
const isRegister = ref(false)
const agreed = ref(false)

const formData = reactive({
  email: '',
  password: '',
  username: ''
})

const rules = {
  email: [{ required: true, message: '请输入邮箱', type: 'error' }],
  password: [{ required: true, message: '请输入密码', type: 'error' }]
}

const toggleMode = () => {
  isRegister.value = !isRegister.value
}

// 自动登录函数
const autoLogin = async (email: string, password: string) => {
  loading.value = true
  const result = await authStore.login({ email, password })
  loading.value = false

  if (result.success) {
    MessagePlugin.success('登录成功')
    router.push('/dashboard')
  } else {
    MessagePlugin.error(result.message)
  }
}

const handleSubmit = async () => {
  loading.value = true

  if (isRegister.value) {
    // 注册流程
    const result = await authStore.register({
      username: formData.email.split('@')[0] || '',
      email: formData.email,
      password: formData.password
    })

    if (result.success) {
      MessagePlugin.success('注册成功，正在自动登录...')

      // 延迟一下让用户看到提示，然后平滑过渡到登录表单
      setTimeout(() => {
        isRegister.value = false
        // 表单已经保留了邮箱和密码，直接调用登录
        autoLogin(formData.email, formData.password)
      }, 800)
    } else {
      loading.value = false
      MessagePlugin.error(result.message)
    }
  } else {
    // 直接登录流程
    const result = await authStore.login({
      email: formData.email,
      password: formData.password
    })

    loading.value = false

    if (result.success) {
      MessagePlugin.success('登录成功')
      router.push('/dashboard')
    } else {
      MessagePlugin.error(result.message)
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  background: #ffffff;
  padding: 4%;
}

/* 左侧布局 - 占 70% */
.login-left {
  width: 70%;
  display: flex;
  align-items: center;
  justify-content: center;
  /* background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%); */
  position: relative;
}

.login-left::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 30% 70%, rgba(102, 126, 234, 0.08) 0%, transparent 50%),
              radial-gradient(circle at 70% 30%, rgba(118, 75, 162, 0.06) 0%, transparent 50%);
  pointer-events: none;
}

.login-brand {
  text-align: center;
  z-index: 1;
}

.brand-icon {
  color: #667eea;
  margin-bottom: 24px;
}

.brand-title {
  font-size: 36px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 12px 0;
  letter-spacing: -0.5px;
}

.brand-subtitle {
  font-size: 20px;
  color: #667eea;
  margin: 0 0 16px 0;
  font-weight: 500;
}

.brand-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}

/* 右侧布局 - 占 30% */
.login-right {
  width: 30%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.05);
}

.login-form-wrapper {
  width: 80%;
  max-width: 360px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h2 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #1a1a2e;
  font-weight: 600;
}

.login-header p {
  color: #888;
  font-size: 14px;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.login-footer {
  text-align: center;
  margin-top: 16px;
}

/* 表单过渡动画 */
.form-fade-enter-active,
.form-fade-leave-active {
  transition: all 0.4s ease;
}

.form-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.form-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.form-container {
  width: 100%;
}

/* 响应式适配 */
@media (max-width: 1024px) {
  .login-left {
    width: 60%;
  }

  .login-right {
    width: 40%;
  }

  .login-form-wrapper {
    width: 85%;
  }
}

@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }

  .login-left {
    width: 100%;
    min-height: 200px;
    padding: 40px 20px;
  }

  .login-right {
    width: 100%;
    flex: 1;
    padding: 40px 20px;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.05);
  }

  .login-form-wrapper {
    width: 100%;
    max-width: 400px;
  }

  .brand-title {
    font-size: 28px;
  }

  .brand-subtitle {
    font-size: 16px;
  }
}
</style>
