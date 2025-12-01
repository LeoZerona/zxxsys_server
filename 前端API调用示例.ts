/**
 * 前端 API 调用示例
 * 适用于 Vue3 + TypeScript 项目
 */

// ============================================================================
// 方式一：使用 Fetch API
// ============================================================================

const API_BASE_URL = 'http://localhost:5000/api'

// 类型定义
interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  code?: string  // 仅测试模式
  cooldown_seconds?: number
}

interface SendCodeResponse extends ApiResponse {
  code?: string
  cooldown_seconds?: number
}

interface RegisterResponse extends ApiResponse {
  data?: {
    id: number
    email: string
    role: string
    created_at: string
    is_active: boolean
  }
}

/**
 * 发送验证码
 */
export async function sendVerificationCode(email: string): Promise<SendCodeResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/send-verification-code`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    })

    const data: SendCodeResponse = await response.json()

    if (!response.ok) {
      throw new Error(data.message || '请求失败')
    }

    return data
  } catch (error) {
    console.error('发送验证码失败:', error)
    throw error
  }
}

/**
 * 用户注册
 */
export async function register(
  email: string,
  password: string,
  verificationCode: string
): Promise<RegisterResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        verification_code: verificationCode,
      }),
    })

    const data: RegisterResponse = await response.json()

    if (!response.ok) {
      throw new Error(data.message || '注册失败')
    }

    return data
  } catch (error) {
    console.error('注册失败:', error)
    throw error
  }
}

// ============================================================================
// 方式二：使用 Axios（需要先安装: npm install axios）
// ============================================================================

/*
import axios, { AxiosResponse } from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

export async function sendVerificationCode(email: string): Promise<SendCodeResponse> {
  try {
    const response: AxiosResponse<SendCodeResponse> = await api.post('/send-verification-code', {
      email,
    })
    return response.data
  } catch (error: any) {
    if (error.response) {
      throw new Error(error.response.data?.message || '发送验证码失败')
    } else {
      throw new Error('网络错误，请检查后端服务是否启动')
    }
  }
}

export async function register(
  email: string,
  password: string,
  verificationCode: string
): Promise<RegisterResponse> {
  try {
    const response: AxiosResponse<RegisterResponse> = await api.post('/register', {
      email,
      password,
      verification_code: verificationCode,
    })
    return response.data
  } catch (error: any) {
    if (error.response) {
      throw new Error(error.response.data?.message || '注册失败')
    } else {
      throw new Error('网络错误，请检查后端服务是否启动')
    }
  }
}
*/

// ============================================================================
// 使用示例（在 Vue 组件中）
// ============================================================================

/*
<script setup lang="ts">
import { ref } from 'vue'
import { sendVerificationCode, register } from '@/api/auth'

const email = ref('')
const password = ref('')
const code = ref('')
const loading = ref(false)

// 发送验证码
async function handleSendCode() {
  try {
    const response = await sendVerificationCode(email.value)
    console.log('验证码发送成功:', response)
    
    // 测试模式下，验证码会返回在 response.code 中
    if (response.code) {
      console.log('测试模式验证码:', response.code)
    }
  } catch (error: any) {
    console.error('发送失败:', error.message)
  }
}

// 注册
async function handleRegister() {
  loading.value = true
  try {
    const response = await register(email.value, password.value, code.value)
    console.log('注册成功:', response.data)
  } catch (error: any) {
    console.error('注册失败:', error.message)
  } finally {
    loading.value = false
  }
}
</script>
*/

