/**
 * Vue3 + TypeScript 前端调用示例
 * 
 * 这个文件展示了如何在 Vue3 + TypeScript 项目中调用 Flask 后端 API
 * 你可以将这些代码复制到你的 Vue3 项目中使用
 */

// ============================================
// 方式 1: 使用 Fetch API（原生 JavaScript）
// ============================================

interface RegisterRequest {
  email: string;
  password: string;
}

interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

interface User {
  id: number;
  email: string;
  created_at: string;
  is_active: boolean;
}

// 注册用户
export async function registerWithFetch(email: string, password: string): Promise<ApiResponse<User>> {
  try {
    const response = await fetch('http://localhost:5000/api/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
      } as RegisterRequest),
    });

    const data: ApiResponse<User> = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '注册失败');
    }

    return data;
  } catch (error) {
    console.error('注册请求失败:', error);
    throw error;
  }
}

// ============================================
// 方式 2: 使用 Axios（推荐）
// ============================================

import axios, { AxiosInstance, AxiosResponse } from 'axios';

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 注册用户
export async function registerWithAxios(email: string, password: string): Promise<ApiResponse<User>> {
  try {
    const response: AxiosResponse<ApiResponse<User>> = await apiClient.post('/register', {
      email,
      password,
    });
    return response.data;
  } catch (error: any) {
    if (error.response) {
      // 服务器返回了错误响应
      throw new Error(error.response.data.message || '注册失败');
    } else if (error.request) {
      // 请求已发出但没有收到响应
      throw new Error('网络错误，请检查服务器是否运行');
    } else {
      throw new Error(error.message || '请求失败');
    }
  }
}

// ============================================
// 方式 3: Vue3 Composition API 使用示例
// ============================================

// 在 Vue 组件中使用示例:
/*
<script setup lang="ts">
import { ref } from 'vue';
import { registerWithAxios } from './api'; // 导入上面的函数

const email = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const handleRegister = async () => {
  if (!email.value || !password.value) {
    errorMessage.value = '请填写邮箱和密码';
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const result = await registerWithAxios(email.value, password.value);
    if (result.success) {
      successMessage.value = '注册成功！';
      // 可以跳转到登录页面或其他操作
      console.log('用户信息:', result.data);
    }
  } catch (error: any) {
    errorMessage.value = error.message || '注册失败，请重试';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div>
    <input v-model="email" type="email" placeholder="邮箱" />
    <input v-model="password" type="password" placeholder="密码" />
    <button @click="handleRegister" :disabled="loading">
      {{ loading ? '注册中...' : '注册' }}
    </button>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="success">{{ successMessage }}</p>
  </div>
</template>
*/

// ============================================
// 方式 4: 创建 API 服务类（推荐用于大型项目）
// ============================================

class ApiService {
  private baseURL: string;
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:5000/api') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        // 可以在这里添加 token 等
        // const token = localStorage.getItem('token');
        // if (token) {
        //   config.headers.Authorization = `Bearer ${token}`;
        // }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // 统一错误处理
        if (error.response) {
          const message = error.response.data?.message || '请求失败';
          console.error('API 错误:', message);
        }
        return Promise.reject(error);
      }
    );
  }

  // 注册
  async register(email: string, password: string): Promise<ApiResponse<User>> {
    const response = await this.client.post<ApiResponse<User>>('/register', {
      email,
      password,
    });
    return response.data;
  }

  // 健康检查
  async healthCheck(): Promise<any> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // 获取用户信息
  async getUser(userId: number): Promise<ApiResponse<User>> {
    const response = await this.client.get<ApiResponse<User>>(`/users/${userId}`);
    return response.data;
  }
}

// 导出单例
export const apiService = new ApiService();

// ============================================
// 方式 5: 使用 API Service 的 Vue 组件示例
// ============================================

/*
<script setup lang="ts">
import { ref } from 'vue';
import { apiService } from './api';

const email = ref('');
const password = ref('');
const loading = ref(false);

const handleRegister = async () => {
  loading.value = true;
  try {
    const result = await apiService.register(email.value, password.value);
    console.log('注册成功:', result);
  } catch (error) {
    console.error('注册失败:', error);
  } finally {
    loading.value = false;
  }
};
</script>
*/

