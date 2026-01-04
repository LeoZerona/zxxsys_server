"""
题目去重相关路由
提供任务管理、重复题目查询等API接口
"""
from flask import request, jsonify
from sqlalchemy import func, desc, and_
from typing import Dict, Any, Optional
from datetime import datetime
import threading
from src.models import db
from src.models.question import Question
from src.models.question_dedup import (
    DedupTask, QuestionDuplicatePair, QuestionDuplicateGroup,
    QuestionDuplicateGroupItem, QuestionDedupFeature
)
from src.services.question_service import QuestionService
from src.services.question_dedup_service import QuestionDedupService
from src.services.question_aggregation_service import QuestionAggregationService


def _execute_dedup_task(task_id: int):
    """
    在后台线程中执行去重任务
    
    Args:
        task_id: 任务ID
    """
    from src.app import app as flask_app
    
    with flask_app.app_context():
        try:
            task = DedupTask.query.get(task_id)
            if not task:
                print(f"任务 {task_id} 不存在")
                return
            
            # 获取任务配置
            config = task.get_config()
            similarity_threshold = config.get('similarity_threshold', 0.8)
            
            # 初始化去重会话（使用现有的task_id）
            groups = QuestionService.get_question_groups()
            
            # 初始化进度（关联到现有的task_id）
            progress = {
                'task_id': task_id,
                'current_group_index': 0,
                'total_groups': len(groups),
                'processed_groups': 0,
                'current_group': None,
                'status': 'running',
                'last_update': datetime.now().isoformat(),
                'groups': groups
            }
            QuestionDedupService.save_progress(progress)
            
            # 更新任务状态
            task.status = 'running'
            task.started_at = datetime.now()
            task.total_groups = len(groups)
            task.total_questions = sum(group['count'] for group in groups)
            db.session.commit()
            
            print(f"开始处理任务 {task_id}，共 {len(groups)} 个分组")
            
            # 循环处理所有分组
            while True:
                # 获取下一个分组（传入task_id确保使用正确的进度）
                group = QuestionDedupService.get_next_group(task_id=task_id)
                if not group:
                    print(f"任务 {task_id} 所有分组处理完成")
                    break
                
                try:
                    # 处理该分组
                    results = QuestionDedupService.process_single_group(group)
                    
                    # 标记完成（会自动保存到数据库）
                    QuestionDedupService.mark_group_completed(results)
                    
                    # 发送进度更新到WebSocket
                    from src.routes.websocket import emit_task_progress
                    progress = QuestionDedupService.get_progress()
                    task = DedupTask.query.get(task_id)
                    
                    if task:
                        progress_percentage = 0.0
                        if task.total_groups > 0:
                            progress_percentage = round(
                                (task.processed_groups / task.total_groups) * 100, 2
                            )
                        
                        emit_task_progress(task_id, {
                            'status': task.status,
                            'processed_groups': task.processed_groups,
                            'total_groups': task.total_groups,
                            'progress_percentage': progress_percentage,
                            'current_group': {
                                'type_name': group['type_name'],
                                'subject_name': group['subject_name'],
                                'channel_code': group['channel_code']
                            },
                            'message': f"已完成分组: {group['type_name']} - {group['subject_name']}"
                        })
                    
                    print(f"分组处理完成: {group['type_name']} - {group['subject_name']} ({group['channel_code']})")
                    
                except Exception as e:
                    print(f"处理分组失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    # 更新任务状态为错误
                    task = DedupTask.query.get(task_id)
                    if task:
                        task.status = 'error'
                        task.error_message = str(e)
                        db.session.commit()
                        
                        # 发送错误通知到WebSocket
                        from src.routes.websocket import emit_task_error
                        emit_task_error(task_id, str(e))
                    break
            
            # 检查是否完成
            progress = QuestionDedupService.get_progress()
            if progress.get('status') == 'completed':
                task = DedupTask.query.get(task_id)
                if task:
                    task.status = 'completed'
                    task.completed_at = datetime.now()
                    db.session.commit()
                    
                    # 发送任务完成通知到WebSocket
                    from src.routes.websocket import emit_task_completed
                    task_dict = task.to_dict()
                    task_dict['progress_percentage'] = 100.0
                    emit_task_completed(task_id, task_dict)
                    
                    print(f"任务 {task_id} 完成")
            
        except Exception as e:
            print(f"执行任务 {task_id} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 更新任务状态为错误
            try:
                task = DedupTask.query.get(task_id)
                if task:
                    task.status = 'error'
                    task.error_message = str(e)
                    db.session.commit()
                    
                    # 发送错误通知到WebSocket
                    from src.routes.websocket import emit_task_error
                    emit_task_error(task_id, str(e))
            except:
                pass


def register_question_dedup_routes(app):
    """注册题目去重相关的路由"""
    
    @app.route('/api/dedup/tasks', methods=['GET'])
    def get_dedup_tasks():
        """
        获取去重任务列表
        
        请求参数:
            page (int, 可选): 页码，默认1
            page_size (int, 可选): 每页数量，默认20
            status (str, 可选): 状态筛选 (pending/running/completed/error/cancelled)
        """
        try:
            page = request.args.get('page', type=int, default=1)
            page_size = request.args.get('page_size', type=int, default=20)
            status = request.args.get('status', '').strip() or None
            
            # 验证参数
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 20
            
            # 构建查询
            query = DedupTask.query
            
            if status:
                valid_statuses = ['pending', 'running', 'completed', 'error', 'cancelled']
                if status in valid_statuses:
                    query = query.filter(DedupTask.status == status)
            
            # 按创建时间倒序排列
            query = query.order_by(desc(DedupTask.created_at))
            
            # 分页
            pagination = query.paginate(
                page=page,
                per_page=page_size,
                error_out=False
            )
            
            # 转换为字典并添加进度百分比
            tasks = []
            for task in pagination.items:
                task_dict = task.to_dict()
                # 计算进度百分比
                if task.total_groups > 0:
                    task_dict['progress_percentage'] = round(
                        (task.processed_groups / task.total_groups) * 100, 2
                    )
                else:
                    task_dict['progress_percentage'] = 0.0
                tasks.append(task_dict)
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': {
                    'list': tasks,
                    'pagination': {
                        'page': pagination.page,
                        'page_size': page_size,
                        'total': pagination.total,
                        'total_pages': pagination.pages
                    }
                }
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks', methods=['POST'])
    def create_dedup_task():
        """
        创建新的去重任务
        
        请求体:
            task_name (str, 可选): 任务名称
            config (dict, 可选): 任务配置，如 {"similarity_threshold": 0.8}
            analysis_type (str, 可选): 分析类型，full=全量分析, incremental=增量分析, custom=自定义分析，默认full
        """
        try:
            data = request.get_json() or {}
            task_name = data.get('task_name', '').strip() or None
            config = data.get('config')
            analysis_type = data.get('analysis_type', 'full').strip() or 'full'
            
            # 验证分析类型
            valid_analysis_types = ['full', 'incremental', 'custom']
            if analysis_type not in valid_analysis_types:
                return jsonify({
                    'success': False,
                    'message': f'分析类型无效，支持的类型：{", ".join(valid_analysis_types)}',
                    'error_code': 'INVALID_PARAMETER'
                }), 400
            
            # 获取所有分组信息，用于计算统计信息
            groups = QuestionService.get_question_groups()
            total_groups = len(groups)
            total_questions = sum(group['count'] for group in groups)
            
            # 估算处理时长（秒）
            # 估算规则：
            # - 每个题目平均处理时间：0.1秒（包括清洗、特征提取、相似度计算等）
            # - 每个分组额外开销：5秒（分组初始化、数据加载等）
            # - 基础开销：30秒（任务初始化、数据库连接等）
            estimated_duration = int(
                30 +  # 基础开销
                (total_questions * 0.1) +  # 题目处理时间
                (total_groups * 5)  # 分组处理时间
            )
            
            # 创建任务
            task = DedupTask(
                task_name=task_name or f"查找重复题目-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                status='pending',
                total_groups=total_groups,
                processed_groups=0,
                total_questions=total_questions,
                exact_duplicate_groups=0,
                exact_duplicate_pairs=0,
                similar_duplicate_pairs=0,
                analysis_type=analysis_type,
                estimated_duration=estimated_duration
            )
            
            if config:
                task.set_config(config)
            
            db.session.add(task)
            db.session.commit()
            
            task_dict = task.to_dict()
            task_dict['progress_percentage'] = 0.0
            
            return jsonify({
                'success': True,
                'message': '任务创建成功',
                'data': task_dict
            }), 201
        
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'创建任务失败: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>', methods=['GET'])
    def get_dedup_task_detail(task_id):
        """
        获取任务详情
        """
        try:
            task = DedupTask.query.get(task_id)
            
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            task_dict = task.to_dict()
            # 计算进度百分比
            if task.total_groups > 0:
                task_dict['progress_percentage'] = round(
                    (task.processed_groups / task.total_groups) * 100, 2
                )
            else:
                task_dict['progress_percentage'] = 0.0
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': task_dict
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>', methods=['DELETE'])
    def delete_dedup_task(task_id):
        """
        删除任务（级联删除相关数据）
        """
        try:
            task = DedupTask.query.get(task_id)
            
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            db.session.delete(task)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '任务删除成功'
            }), 200
        
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'删除任务失败: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>/start', methods=['POST'])
    def start_dedup_task(task_id):
        """
        启动任务（后台异步执行）
        会在后台线程中执行去重分析
        """
        try:
            task = DedupTask.query.get(task_id)
            
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            if task.status == 'running':
                return jsonify({
                    'success': False,
                    'message': '任务已在运行中',
                    'error_code': 'INVALID_STATUS'
                }), 400
            
            if task.status == 'completed':
                return jsonify({
                    'success': False,
                    'message': '任务已完成，无法重新启动',
                    'error_code': 'INVALID_STATUS'
                }), 400
            
            # 在后台线程中执行任务
            thread = threading.Thread(
                target=_execute_dedup_task,
                args=(task_id,),
                daemon=True
            )
            thread.start()
            
            return jsonify({
                'success': True,
                'message': '任务已启动，正在后台执行',
                'data': task.to_dict()
            }), 200
        
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'启动任务失败: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>/cancel', methods=['POST'])
    def cancel_dedup_task(task_id):
        """
        取消任务
        """
        try:
            task = DedupTask.query.get(task_id)
            
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            if task.status in ['completed', 'cancelled']:
                return jsonify({
                    'success': False,
                    'message': f'任务状态为{task.status}，无法取消',
                    'error_code': 'INVALID_STATUS'
                }), 400
            
            task.status = 'cancelled'
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '任务已取消',
                'data': task.to_dict()
            }), 200
        
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'取消任务失败: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>/exact-groups', methods=['GET'])
    def get_exact_groups(task_id):
        """
        获取完全重复组列表
        
        请求参数:
            page (int, 可选): 页码，默认1
            page_size (int, 可选): 每页数量，默认20
            group_type (str, 可选): 题型筛选
            subject_id (int, 可选): 科目ID筛选
        """
        try:
            page = request.args.get('page', type=int, default=1)
            page_size = request.args.get('page_size', type=int, default=20)
            group_type = request.args.get('group_type', '').strip() or None
            subject_id = request.args.get('subject_id', type=int) or None
            
            # 验证任务是否存在
            task = DedupTask.query.get(task_id)
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            # 验证参数
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 20
            
            # 构建查询
            query = QuestionDuplicateGroup.query.filter_by(task_id=task_id)
            
            if group_type:
                query = query.filter(QuestionDuplicateGroup.group_type == group_type)
            if subject_id:
                query = query.filter(QuestionDuplicateGroup.group_subject_id == subject_id)
            
            query = query.order_by(desc(QuestionDuplicateGroup.detected_at))
            
            # 分页
            pagination = query.paginate(
                page=page,
                per_page=page_size,
                error_out=False
            )
            
            # 转换为字典
            groups = []
            for group in pagination.items:
                group_dict = group.to_dict(include_items=True)
                
                # 添加题型名称和科目名称
                group_dict['group']['type_name'] = QuestionService.TYPE_NAMES.get(
                    group.group_type, '未知题型'
                )
                
                # 查询科目名称（从第一个题目获取）
                if group_dict['question_ids']:
                    first_question = Question.query.filter_by(
                        question_id=group_dict['question_ids'][0]
                    ).first()
                    if first_question and first_question.subject_name:
                        group_dict['group']['subject_name'] = first_question.subject_name
                
                groups.append(group_dict)
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': {
                    'list': groups,
                    'pagination': {
                        'page': pagination.page,
                        'page_size': page_size,
                        'total': pagination.total,
                        'total_pages': pagination.pages
                    }
                }
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>/exact-groups/<int:group_id>', methods=['GET'])
    def get_exact_group_detail(task_id, group_id):
        """
        获取完全重复组详情（包含题目内容）
        """
        try:
            # 验证任务
            task = DedupTask.query.get(task_id)
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            # 查询组
            group = QuestionDuplicateGroup.query.filter_by(
                task_id=task_id,
                id=group_id
            ).first()
            
            if not group:
                return jsonify({
                    'success': False,
                    'message': '重复组不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            group_dict = group.to_dict(include_items=True)
            
            # 添加题型名称
            group_dict['group']['type_name'] = QuestionService.TYPE_NAMES.get(
                group.group_type, '未知题型'
            )
            
            # 获取题目详情
            questions = []
            for qid in group_dict['question_ids']:
                question_detail = QuestionService.get_question_detail(
                    question_id=qid,
                    include_answer=True,
                    include_analysis=True
                )
                if question_detail:
                    # 同时获取清洗后的内容
                    feature = QuestionDedupFeature.query.filter_by(
                        task_id=task_id,
                        question_id=qid
                    ).first()
                    if feature:
                        question_detail['cleaned_content'] = feature.cleaned_content
                    questions.append(question_detail)
            
            group_dict['questions'] = questions
            
            # 添加科目名称
            if questions:
                group_dict['group']['subject_name'] = questions[0].get('subject_name')
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': group_dict
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>/similar-pairs', methods=['GET'])
    def get_similar_pairs(task_id):
        """
        获取相似重复对列表
        
        请求参数:
            page (int, 可选): 页码，默认1
            page_size (int, 可选): 每页数量，默认20
            min_similarity (float, 可选): 最小相似度，默认0.8
            group_type (str, 可选): 题型筛选
        """
        try:
            page = request.args.get('page', type=int, default=1)
            page_size = request.args.get('page_size', type=int, default=20)
            min_similarity = request.args.get('min_similarity', type=float) or 0.8
            group_type = request.args.get('group_type', '').strip() or None
            
            # 验证任务是否存在
            task = DedupTask.query.get(task_id)
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            # 验证参数
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 20
            
            # 构建查询
            query = QuestionDuplicatePair.query.filter_by(
                task_id=task_id,
                duplicate_type='similar'
            )
            
            if min_similarity:
                query = query.filter(QuestionDuplicatePair.similarity >= min_similarity)
            if group_type:
                query = query.filter(QuestionDuplicatePair.group_type == group_type)
            
            query = query.order_by(desc(QuestionDuplicatePair.similarity))
            
            # 分页
            pagination = query.paginate(
                page=page,
                per_page=page_size,
                error_out=False
            )
            
            # 转换为字典
            pairs = []
            for pair in pagination.items:
                pair_dict = pair.to_dict()
                
                # 添加题型名称和科目名称
                pair_dict['group']['type_name'] = QuestionService.TYPE_NAMES.get(
                    pair.group_type, '未知题型'
                )
                
                # 查询科目名称（从第一个题目获取）
                first_question = Question.query.filter_by(
                    question_id=pair.question_id_1
                ).first()
                if first_question and first_question.subject_name:
                    pair_dict['group']['subject_name'] = first_question.subject_name
                
                pairs.append(pair_dict)
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': {
                    'list': pairs,
                    'pagination': {
                        'page': pagination.page,
                        'page_size': page_size,
                        'total': pagination.total,
                        'total_pages': pagination.pages
                    }
                }
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>/similar-pairs/<int:pair_id>', methods=['GET'])
    def get_similar_pair_detail(task_id, pair_id):
        """
        获取相似重复对详情（包含两个题目的内容）
        """
        try:
            # 验证任务
            task = DedupTask.query.get(task_id)
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            # 查询重复对
            pair = QuestionDuplicatePair.query.filter_by(
                task_id=task_id,
                id=pair_id,
                duplicate_type='similar'
            ).first()
            
            if not pair:
                return jsonify({
                    'success': False,
                    'message': '重复对不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            pair_dict = pair.to_dict()
            
            # 添加题型名称
            pair_dict['group']['type_name'] = QuestionService.TYPE_NAMES.get(
                pair.group_type, '未知题型'
            )
            
            # 获取两个题目的详情
            question_1 = QuestionService.get_question_detail(
                question_id=pair.question_id_1,
                include_answer=True,
                include_analysis=True
            )
            question_2 = QuestionService.get_question_detail(
                question_id=pair.question_id_2,
                include_answer=True,
                include_analysis=True
            )
            
            # 获取清洗后的内容
            feature_1 = QuestionDedupFeature.query.filter_by(
                task_id=task_id,
                question_id=pair.question_id_1
            ).first()
            if feature_1 and question_1:
                question_1['cleaned_content'] = feature_1.cleaned_content
            
            feature_2 = QuestionDedupFeature.query.filter_by(
                task_id=task_id,
                question_id=pair.question_id_2
            ).first()
            if feature_2 and question_2:
                question_2['cleaned_content'] = feature_2.cleaned_content
            
            pair_dict['question_1'] = question_1
            pair_dict['question_2'] = question_2
            
            # 添加科目名称
            if question_1:
                pair_dict['group']['subject_name'] = question_1.get('subject_name')
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': pair_dict
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>/statistics', methods=['GET'])
    def get_task_statistics(task_id):
        """
        获取任务统计信息
        """
        try:
            task = DedupTask.query.get(task_id)
            
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            task_dict = task.to_dict()
            if task.total_groups > 0:
                task_dict['progress_percentage'] = round(
                    (task.processed_groups / task.total_groups) * 100, 2
                )
            else:
                task_dict['progress_percentage'] = 0.0
            
            # 统计信息
            summary = {
                'total_duplicates': task.exact_duplicate_groups + task.similar_duplicate_pairs,
                'exact_duplicate_groups': task.exact_duplicate_groups,
                'exact_duplicate_pairs': task.exact_duplicate_pairs,
                'similar_duplicate_pairs': task.similar_duplicate_pairs,
                'unique_question_count': max(0, task.total_questions - task.exact_duplicate_pairs - task.similar_duplicate_pairs)
            }
            
            # 按题型统计
            by_type_query = db.session.query(
                QuestionDuplicateGroup.group_type,
                func.count(QuestionDuplicateGroup.id).label('exact_groups'),
                func.sum(QuestionDuplicateGroup.question_count).label('total_questions')
            ).filter_by(
                task_id=task_id
            ).group_by(
                QuestionDuplicateGroup.group_type
            )
            
            by_type = []
            for row in by_type_query.all():
                # 统计相似重复对
                similar_count = QuestionDuplicatePair.query.filter_by(
                    task_id=task_id,
                    duplicate_type='similar',
                    group_type=row.group_type
                ).count()
                
                by_type.append({
                    'type': row.group_type,
                    'type_name': QuestionService.TYPE_NAMES.get(row.group_type, '未知题型'),
                    'exact_groups': row.exact_groups or 0,
                    'similar_pairs': similar_count
                })
            
            # 按科目统计
            by_subject_query = db.session.query(
                QuestionDuplicateGroup.group_subject_id,
                func.count(QuestionDuplicateGroup.id).label('exact_groups')
            ).filter_by(
                task_id=task_id
            ).group_by(
                QuestionDuplicateGroup.group_subject_id
            )
            
            by_subject = []
            for row in by_subject_query.all():
                # 统计相似重复对
                similar_count = QuestionDuplicatePair.query.filter_by(
                    task_id=task_id,
                    duplicate_type='similar',
                    group_subject_id=row.group_subject_id
                ).count()
                
                # 获取科目名称
                subject_name = None
                first_group = QuestionDuplicateGroup.query.filter_by(
                    task_id=task_id,
                    group_subject_id=row.group_subject_id
                ).first()
                if first_group and first_group.items.first():
                    first_question = Question.query.filter_by(
                        question_id=first_group.items.first().question_id
                    ).first()
                    if first_question:
                        subject_name = first_question.subject_name
                
                by_subject.append({
                    'subject_id': row.group_subject_id,
                    'subject_name': subject_name,
                    'exact_groups': row.exact_groups or 0,
                    'similar_pairs': similar_count
                })
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': {
                    'task': task_dict,
                    'summary': summary,
                    'by_type': by_type,
                    'by_subject': by_subject
                }
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500