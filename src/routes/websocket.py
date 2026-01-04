"""
WebSocket 路由
用于实时推送去重任务进度
"""
from flask import request
from flask_socketio import emit, join_room, leave_room
from src.models.question_dedup import DedupTask


def register_websocket_routes(socketio):
    """注册 WebSocket 路由"""
    
    @socketio.on('connect')
    def handle_connect():
        """客户端连接时触发"""
        print(f"WebSocket 客户端已连接: {request.sid}")
        emit('connected', {'message': '连接成功'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开连接时触发"""
        print(f"WebSocket 客户端已断开: {request.sid}")
    
    @socketio.on('join_task')
    def handle_join_task(data):
        """
        加入任务房间，接收该任务的进度更新
        
        事件: 'join_task'
        数据: {'task_id': 1}
        """
        task_id = data.get('task_id')
        if not task_id:
            emit('error', {'message': '缺少 task_id'})
            return
        
        # 验证任务是否存在
        task = DedupTask.query.get(task_id)
        if not task:
            emit('error', {'message': f'任务 {task_id} 不存在'})
            return
        
        # 加入任务房间（room名称格式：task_{task_id}）
        room = f'task_{task_id}'
        join_room(room)
        print(f"客户端 {request.sid} 加入任务房间: {room}")
        
        # 发送当前任务状态
        task_dict = task.to_dict()
        if task.total_groups > 0:
            task_dict['progress_percentage'] = round(
                (task.processed_groups / task.total_groups) * 100, 2
            )
        else:
            task_dict['progress_percentage'] = 0.0
        
        emit('task_status', {
            'task_id': task_id,
            'status': task.status,
            'data': task_dict
        })
    
    @socketio.on('leave_task')
    def handle_leave_task(data):
        """
        离开任务房间
        
        事件: 'leave_task'
        数据: {'task_id': 1}
        """
        task_id = data.get('task_id')
        if task_id:
            room = f'task_{task_id}'
            leave_room(room)
            print(f"客户端 {request.sid} 离开任务房间: {room}")
            emit('left', {'message': f'已离开任务 {task_id} 的房间'})


def emit_task_progress(task_id: int, progress_data: dict):
    """
    向任务房间的所有客户端发送进度更新
    
    Args:
        task_id: 任务ID
        progress_data: 进度数据字典，包含：
            - status: 任务状态
            - processed_groups: 已处理分组数
            - total_groups: 总分组数
            - progress_percentage: 进度百分比
            - current_group: 当前处理的分组信息
            - message: 消息（可选）
    """
    from src.app import socketio
    
    room = f'task_{task_id}'
    try:
        socketio.emit('task_progress', {
            'task_id': task_id,
            **progress_data
        }, room=room)
    except Exception as e:
        print(f"发送进度更新失败: {e}")


def emit_task_completed(task_id: int, task_data: dict):
    """
    向任务房间的所有客户端发送任务完成通知
    
    Args:
        task_id: 任务ID
        task_data: 任务数据字典
    """
    from src.app import socketio
    
    room = f'task_{task_id}'
    try:
        socketio.emit('task_completed', {
            'task_id': task_id,
            'data': task_data
        }, room=room)
    except Exception as e:
        print(f"发送完成通知失败: {e}")


def emit_task_error(task_id: int, error_message: str):
    """
    向任务房间的所有客户端发送错误通知
    
    Args:
        task_id: 任务ID
        error_message: 错误消息
    """
    from src.app import socketio
    
    room = f'task_{task_id}'
    try:
        socketio.emit('task_error', {
            'task_id': task_id,
            'error': error_message
        }, room=room)
    except Exception as e:
        print(f"发送错误通知失败: {e}")

