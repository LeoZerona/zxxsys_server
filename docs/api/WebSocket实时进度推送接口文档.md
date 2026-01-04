# WebSocket 实时进度推送接口文档

## 📋 概述

通过 WebSocket 连接，前端可以实时接收去重任务的进度更新，无需轮询查询。

## 🔌 连接信息

**WebSocket 地址**: `ws://localhost:5000/socket.io/`

**协议**: Socket.IO (支持 WebSocket 和长轮询降级)

## 📦 安装依赖

### 前端（JavaScript/TypeScript）

```bash
npm install socket.io-client
```

### 后端

已在 `requirements.txt` 中包含：
- `Flask-SocketIO==5.3.6`
- `python-socketio==5.11.0`
- `eventlet==0.36.1`

安装命令：
```bash
pip install -r requirements.txt
```

## 🚀 使用示例

### JavaScript/TypeScript 示例

```typescript
import { io, Socket } from 'socket.io-client';

// 1. 连接到 WebSocket 服务器
const socket: Socket = io('http://localhost:5000', {
  transports: ['websocket', 'polling'], // 优先使用 WebSocket，失败时降级到轮询
  reconnection: true, // 自动重连
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
});

// 2. 监听连接事件
socket.on('connect', () => {
  console.log('WebSocket 连接成功');
  
  // 3. 加入任务房间（监听任务ID为1的进度更新）
  socket.emit('join_task', { task_id: 1 });
});

socket.on('connected', (data) => {
  console.log('服务器确认连接:', data);
});

// 4. 监听任务进度更新
socket.on('task_progress', (data) => {
  console.log('任务进度更新:', data);
  /*
  data 格式:
  {
    task_id: 1,
    status: 'running',
    processed_groups: 5,
    total_groups: 10,
    progress_percentage: 50.0,
    current_group: {
      type_name: '单选题',
      subject_name: '数学',
      channel_code: 'default'
    },
    message: '已完成分组: 单选题 - 数学'
  }
  */
  
  // 更新UI
  updateProgressBar(data.progress_percentage);
  updateStatusText(data.message);
});

// 5. 监听任务完成事件
socket.on('task_completed', (data) => {
  console.log('任务完成:', data);
  /*
  data 格式:
  {
    task_id: 1,
    data: {
      id: 1,
      status: 'completed',
      total_groups: 10,
      processed_groups: 10,
      progress_percentage: 100.0,
      ...
    }
  }
  */
  
  // 显示完成提示
  showCompletionMessage();
});

// 6. 监听错误事件
socket.on('task_error', (data) => {
  console.error('任务错误:', data);
  /*
  data 格式:
  {
    task_id: 1,
    error: '错误消息'
  }
  */
  
  // 显示错误提示
  showErrorMessage(data.error);
});

// 7. 监听任务状态（加入房间时返回的当前状态）
socket.on('task_status', (data) => {
  console.log('任务当前状态:', data);
  // 初始化UI显示
  initializeUI(data.data);
});

// 8. 离开任务房间（可选）
function leaveTask(taskId: number) {
  socket.emit('leave_task', { task_id: taskId });
}

// 9. 断开连接
function disconnect() {
  socket.disconnect();
}
```

### Vue 3 Composition API 示例

```vue
<template>
  <div>
    <div v-if="connected">连接状态: 已连接</div>
    <div v-else>连接状态: 未连接</div>
    
    <div v-if="taskProgress">
      <h3>任务进度</h3>
      <div>状态: {{ taskProgress.status }}</div>
      <div>进度: {{ taskProgress.progress_percentage }}%</div>
      <div>已处理: {{ taskProgress.processed_groups }} / {{ taskProgress.total_groups }}</div>
      <div v-if="taskProgress.current_group">
        当前分组: {{ taskProgress.current_group.type_name }} - {{ taskProgress.current_group.subject_name }}
      </div>
      <div v-if="taskProgress.message">{{ taskProgress.message }}</div>
    </div>
    
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { io, Socket } from 'socket.io-client';

const socket = ref<Socket | null>(null);
const connected = ref(false);
const taskProgress = ref<any>(null);
const error = ref<string>('');

const taskId = 1; // 任务ID

onMounted(() => {
  // 连接 WebSocket
  socket.value = io('http://localhost:5000', {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5
  });

  // 监听连接事件
  socket.value.on('connect', () => {
    connected.value = true;
    console.log('WebSocket 连接成功');
    
    // 加入任务房间
    socket.value?.emit('join_task', { task_id: taskId });
  });

  socket.value.on('disconnect', () => {
    connected.value = false;
    console.log('WebSocket 断开连接');
  });

  // 监听任务进度
  socket.value.on('task_progress', (data: any) => {
    taskProgress.value = data;
    console.log('进度更新:', data);
  });

  // 监听任务完成
  socket.value.on('task_completed', (data: any) => {
    taskProgress.value = data.data;
    console.log('任务完成:', data);
    alert('任务已完成！');
  });

  // 监听错误
  socket.value.on('task_error', (data: any) => {
    error.value = data.error;
    console.error('任务错误:', data);
  });

  // 监听任务状态
  socket.value.on('task_status', (data: any) => {
    taskProgress.value = data.data;
    console.log('任务状态:', data);
  });
});

onUnmounted(() => {
  // 离开任务房间
  if (socket.value) {
    socket.value.emit('leave_task', { task_id: taskId });
    socket.value.disconnect();
  }
});
</script>
```

### React Hooks 示例

```tsx
import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface TaskProgress {
  task_id: number;
  status: string;
  processed_groups: number;
  total_groups: number;
  progress_percentage: number;
  current_group?: {
    type_name: string;
    subject_name: string;
    channel_code: string;
  };
  message?: string;
}

function TaskProgressComponent({ taskId }: { taskId: number }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    // 连接 WebSocket
    const newSocket = io('http://localhost:5000', {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    newSocket.on('connect', () => {
      setConnected(true);
      console.log('WebSocket 连接成功');
      
      // 加入任务房间
      newSocket.emit('join_task', { task_id: taskId });
    });

    newSocket.on('disconnect', () => {
      setConnected(false);
      console.log('WebSocket 断开连接');
    });

    newSocket.on('task_progress', (data: TaskProgress) => {
      setProgress(data);
      console.log('进度更新:', data);
    });

    newSocket.on('task_completed', (data: any) => {
      setProgress(data.data);
      console.log('任务完成:', data);
      alert('任务已完成！');
    });

    newSocket.on('task_error', (data: any) => {
      setError(data.error);
      console.error('任务错误:', data);
    });

    newSocket.on('task_status', (data: any) => {
      setProgress(data.data);
      console.log('任务状态:', data);
    });

    setSocket(newSocket);

    // 清理函数
    return () => {
      newSocket.emit('leave_task', { task_id: taskId });
      newSocket.disconnect();
    };
  }, [taskId]);

  return (
    <div>
      <div>连接状态: {connected ? '已连接' : '未连接'}</div>
      
      {progress && (
        <div>
          <h3>任务进度</h3>
          <div>状态: {progress.status}</div>
          <div>进度: {progress.progress_percentage}%</div>
          <div>已处理: {progress.processed_groups} / {progress.total_groups}</div>
          {progress.current_group && (
            <div>
              当前分组: {progress.current_group.type_name} - {progress.current_group.subject_name}
            </div>
          )}
          {progress.message && <div>{progress.message}</div>}
        </div>
      )}
      
      {error && <div className="error">{error}</div>}
    </div>
  );
}

export default TaskProgressComponent;
```

## 📡 WebSocket 事件说明

### 客户端发送的事件

| 事件名 | 说明 | 数据格式 |
|--------|------|----------|
| `join_task` | 加入任务房间，开始接收该任务的进度更新 | `{ task_id: number }` |
| `leave_task` | 离开任务房间，停止接收进度更新 | `{ task_id: number }` |

### 服务器发送的事件

| 事件名 | 说明 | 数据格式 |
|--------|------|----------|
| `connected` | 连接成功确认 | `{ message: string }` |
| `task_status` | 加入房间时返回的当前任务状态 | `{ task_id: number, status: string, data: object }` |
| `task_progress` | 任务进度更新 | `{ task_id: number, status: string, processed_groups: number, total_groups: number, progress_percentage: number, current_group: object, message: string }` |
| `task_completed` | 任务完成通知 | `{ task_id: number, data: object }` |
| `task_error` | 任务错误通知 | `{ task_id: number, error: string }` |
| `error` | 通用错误 | `{ message: string }` |
| `left` | 离开房间确认 | `{ message: string }` |

## 🔄 完整流程示例

```typescript
// 1. 创建任务
const response = await fetch('http://localhost:5000/api/dedup/tasks', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ task_name: '我的去重任务' })
});
const { data } = await response.json();
const taskId = data.id;

// 2. 连接 WebSocket
const socket = io('http://localhost:5000');

socket.on('connect', () => {
  // 3. 加入任务房间
  socket.emit('join_task', { task_id: taskId });
  
  // 4. 启动任务
  fetch(`http://localhost:5000/api/dedup/tasks/${taskId}/start`, {
    method: 'POST'
  });
});

// 5. 监听进度更新
socket.on('task_progress', (data) => {
  console.log(`进度: ${data.progress_percentage}%`);
  updateUI(data);
});

// 6. 监听完成
socket.on('task_completed', (data) => {
  console.log('任务完成！');
  showCompletionMessage();
});
```

## ⚠️ 注意事项

1. **自动重连**: Socket.IO 客户端默认支持自动重连，连接断开时会自动尝试重连
2. **降级支持**: 如果 WebSocket 不可用，会自动降级到长轮询（polling）
3. **房间机制**: 使用房间（room）机制，多个客户端可以同时监听同一个任务
4. **连接管理**: 页面卸载时记得断开连接，避免资源浪费
5. **错误处理**: 建议监听 `error` 事件处理连接错误

## 🐛 调试技巧

1. **查看连接状态**: 
   ```typescript
   socket.on('connect', () => console.log('已连接'));
   socket.on('disconnect', () => console.log('已断开'));
   ```

2. **启用调试日志**:
   ```typescript
   const socket = io('http://localhost:5000', {
     debug: true  // 启用调试日志
   });
   ```

3. **检查服务器日志**: Flask 应用会输出 WebSocket 连接和事件日志

## 📚 相关文档

- [Socket.IO 官方文档](https://socket.io/docs/v4/)
- [Socket.IO 客户端文档](https://socket.io/docs/v4/client-api/)
- [题目去重接口文档](./题目去重接口前端对接.md)

