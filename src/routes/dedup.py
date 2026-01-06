"""
题目去重相关路由
"""
from flask import request, jsonify
from src.models.question_dedup import DedupTask


def register_dedup_routes(app):
    """注册题目去重相关的路由"""
    
    @app.route('/api/dedup/tasks', methods=['GET'])
    def get_dedup_tasks():
        """
        获取去重任务列表（分页）
        
        请求参数:
            page (int, 可选): 页码，默认 1
            page_size (int, 可选): 每页数量，默认 10，最大 100
            status (str, 可选): 任务状态过滤（pending/running/completed/error/cancelled）
        """
        try:
            # 获取请求参数
            page = request.args.get('page', type=int, default=1)
            page_size = request.args.get('page_size', type=int, default=10)
            status = request.args.get('status', '').strip() or None
            
            # 验证参数
            page = max(1, page)
            page_size = min(max(1, page_size), 100)  # 限制最大100条
            
            # 构建查询
            query = DedupTask.query
            
            # 状态过滤
            if status:
                valid_statuses = ['pending', 'running', 'completed', 'error', 'cancelled']
                if status not in valid_statuses:
                    return jsonify({
                        'success': False,
                        'message': f'无效的状态值，支持的状态：{", ".join(valid_statuses)}',
                        'error_code': 'INVALID_PARAMETER'
                    }), 400
                query = query.filter(DedupTask.status == status)
            
            # 按创建时间倒序排列（最新的在前）
            query = query.order_by(DedupTask.created_at.desc())
            
            # 分页
            offset = (page - 1) * page_size
            total = query.count()
            tasks = query.offset(offset).limit(page_size).all()
            
            # 转换为字典
            task_list = [task.to_dict() for task in tasks]
            
            # 计算总页数
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': {
                    'list': task_list,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'total_pages': total_pages
                    }
                }
            }), 200
        
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e),
                'error_code': 'INVALID_PARAMETER'
            }), 400
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>', methods=['GET'])
    def get_dedup_task_detail(task_id):
        """
        获取单个去重任务详情
        
        路径参数:
            task_id (int): 任务 ID
        """
        try:
            task = DedupTask.query.get(task_id)
            
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': task.to_dict()
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500

