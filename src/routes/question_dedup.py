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

# 任务线程管理器：跟踪运行中的任务线程
_task_threads = {}
_task_threads_lock = threading.Lock()


def _execute_dedup_task(task_id: int):
    """
    在后台线程中执行去重任务

    Args:
        task_id: 任务ID
    """
    from src.app import app as flask_app
    from src.services.question_dedup_service import QuestionDedupService

    with flask_app.app_context():
        try:
            task = DedupTask.query.get(task_id)
            if not task:
                print(f"任务 {task_id} 不存在")
                return

            # 获取任务配置
            config = task.get_config()
            similarity_threshold = config.get('similarity_threshold', 0.8)

            # 检查是否已有进度（支持断点续传）
            existing_progress = QuestionDedupService.get_progress()
            is_resume = (existing_progress.get('task_id') == task_id and 
                        existing_progress.get('total_groups', 0) > 0 and
                        existing_progress.get('processed_groups', 0) < existing_progress.get('total_groups', 0))
            
            if is_resume:
                # 恢复执行：使用现有进度
                print(f"恢复执行任务 {task_id}，从第 {existing_progress.get('processed_groups', 0) + 1} 个分组继续")
                groups = existing_progress.get('groups', [])
                if not groups:
                    # 如果进度中没有分组信息，重新获取
                    groups = QuestionService.get_question_groups()
                    existing_progress['groups'] = groups
                    existing_progress['total_groups'] = len(groups)
                    QuestionDedupService.save_progress(existing_progress)
            else:
                # 首次执行：初始化进度
                print(f"首次执行任务 {task_id}，初始化进度...")
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
                
                # 更新任务状态（仅在首次执行时设置）
                if not task.started_at:
                    task.started_at = datetime.now()
                task.total_groups = len(groups)
                task.total_questions = sum(group['count'] for group in groups)
                db.session.commit()
            
            # 更新任务状态为运行中（恢复时也需要更新）
            task.status = 'running'
            db.session.commit()
            
            print(f"开始处理任务 {task_id}，共 {len(groups)} 个分组，已处理 {task.processed_groups} 个")
            
            # 循环处理所有分组
            while True:
                # 检查任务状态（支持暂停功能）
                # 使用 expire_all() 确保获取最新状态
                db.session.expire_all()
                task = DedupTask.query.get(task_id)
                if not task:
                    print(f"任务 {task_id} 不存在，停止执行")
                    break
                
                # 如果任务被暂停，等待恢复
                if task.status == 'paused':
                    print(f"任务 {task_id} 已暂停，等待恢复...")

                    # 🔧 修复：同时更新进度文件状态为 'paused'
                    from src.services.question_dedup_service import QuestionDedupService
                    progress = QuestionDedupService.get_progress()
                    if progress.get('task_id') == task_id:
                        progress['status'] = 'paused'
                        QuestionDedupService.save_progress(progress)

                    # 发送暂停状态到WebSocket
                    from src.routes.websocket import emit_task_progress
                    progress_percentage = 0.0
                    if task.total_groups > 0:
                        progress_percentage = round(
                            (task.processed_groups / task.total_groups) * 100, 2
                        )
                    emit_task_progress(task_id, {
                        'status': 'paused',
                        'processed_groups': task.processed_groups,
                        'total_groups': task.total_groups,
                        'progress_percentage': progress_percentage,
                        'message': '任务已暂停'
                    })
                    
                    # 轮询检查状态，直到恢复或取消
                    import time
                    resumed = False
                    should_exit = False
                    while True:
                        time.sleep(0.5)  # 每0.5秒检查一次，提高响应速度
                        # 重新获取任务对象以确保状态最新
                        # 清除所有对象的缓存，强制重新加载
                        db.session.expire_all()
                        # 重新查询任务，确保获取最新状态（使用新的查询上下文）
                        task = db.session.query(DedupTask).filter_by(id=task_id).first()
                        if not task:
                            print(f"任务 {task_id} 不存在，停止执行")
                            should_exit = True
                            break
                        
                        # 检查状态变化
                        if task.status != 'paused':
                            if task.status == 'running':
                                print(f"任务 {task_id} 已恢复运行，继续处理...")

                                # 🔧 修复：同时更新进度文件状态为 'running'
                                progress = QuestionDedupService.get_progress()
                                if progress.get('task_id') == task_id:
                                    progress['status'] = 'running'
                                    QuestionDedupService.save_progress(progress)

                                # 发送恢复状态到WebSocket
                                progress_percentage = 0.0
                                if task.total_groups > 0:
                                    progress_percentage = round(
                                        (task.processed_groups / task.total_groups) * 100, 2
                                    )
                                emit_task_progress(task_id, {
                                    'status': 'running',
                                    'processed_groups': task.processed_groups,
                                    'total_groups': task.total_groups,
                                    'progress_percentage': progress_percentage,
                                    'message': '任务已恢复运行'
                                })
                                # 标记为已恢复，退出等待循环
                                resumed = True
                                break
                            elif task.status in ['cancelled', 'completed', 'error']:
                                print(f"任务 {task_id} 状态变为 {task.status}，停止执行")
                                # 标记需要退出主循环
                                should_exit = True
                                break
                    
                    # 如果任务不存在或被取消/完成，退出主循环
                    if should_exit or not task:
                        if not task:
                            print(f"任务 {task_id} 不存在，停止执行")
                        break
                    
                    if task and task.status in ['cancelled', 'completed', 'error']:
                        print(f"任务 {task_id} 状态为 {task.status}，停止执行")
                        break
                    
                    # 如果恢复运行，继续执行主循环（处理分组）
                    if resumed and task and task.status == 'running':
                        print(f"任务 {task_id} 已从暂停状态恢复，继续处理分组...")
                        # 重新获取任务对象以确保状态最新
                        db.session.expire_all()
                        task = DedupTask.query.get(task_id)
                        # 继续执行，不要 break，让循环继续处理分组
                        # 这里会继续到下面的代码，获取下一个分组并处理
                    elif not resumed:
                        # 如果等待循环因为其他原因退出（如任务被取消），退出主循环
                        print(f"任务 {task_id} 等待循环退出，但未恢复运行，停止执行")
                        break
                
                # 如果任务被取消或完成，退出循环
                if task and task.status in ['cancelled', 'completed', 'error']:
                    print(f"任务 {task_id} 状态为 {task.status}，停止执行")
                    break
                
                # 如果任务不存在，退出循环
                if not task:
                    print(f"任务 {task_id} 不存在，停止执行")
                    break
                
                # 再次检查状态（防止在处理分组期间状态被改变）
                db.session.expire_all()  # 确保获取最新状态
                task = DedupTask.query.get(task_id)
                if not task:
                    print(f"任务 {task_id} 不存在，停止执行")
                    break
                
                if task.status == 'paused':
                    # 如果状态在获取分组后变为暂停，跳过处理，回到循环开始
                    print(f"任务 {task_id} 已暂停，跳过当前分组")
                    continue
                
                if task.status in ['cancelled', 'completed', 'error']:
                    print(f"任务 {task_id} 状态为 {task.status}，停止执行")
                    break
                
                # 确保状态是 running 才继续处理
                if task.status != 'running':
                    print(f"任务 {task_id} 状态为 {task.status}，跳过处理")
                    continue
                
                # 获取下一个分组（传入task_id确保使用正确的进度）
                print(f"任务 {task_id} 准备获取下一个分组...")
                group = QuestionDedupService.get_next_group(task_id=task_id)
                if not group:
                    print(f"任务 {task_id} 所有分组处理完成")
                    break
                
                print(f"任务 {task_id} 获取到分组: {group.get('type_name', 'N/A')} - {group.get('subject_name', 'N/A')}")
                
                # 最后一次检查状态（在开始处理分组之前）
                task = DedupTask.query.get(task_id)
                if not task or task.status != 'running':
                    if task and task.status == 'paused':
                        print(f"任务 {task_id} 在处理分组前被暂停，跳过当前分组")
                        continue
                    elif task and task.status in ['cancelled', 'completed', 'error']:
                        print(f"任务 {task_id} 状态为 {task.status}，停止执行")
                        break
                    else:
                        print(f"任务 {task_id} 不存在或状态异常，停止执行")
                        break
                
                try:
                    # 处理该分组（传入 task_id 用于状态检查）
                    results = QuestionDedupService.process_single_group(group, task_id=task_id)
                    
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
                    
                except RuntimeError as e:
                    # 处理暂停或取消的情况
                    error_msg = str(e)
                    if '已暂停' in error_msg:
                        print(f"任务 {task_id} 在处理分组时被暂停")
                        # 不更新任务状态，保持 paused 状态
                        # 任务会在下次循环时进入暂停等待逻辑
                        continue
                    elif '状态为' in error_msg:
                        print(f"任务 {task_id} 在处理分组时状态改变: {error_msg}")
                        # 任务状态已被改变，退出循环
                        break
                    else:
                        # 其他运行时错误，当作普通异常处理
                        raise
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
            finally:
                # 从线程管理器中移除
                with _task_threads_lock:
                    _task_threads.pop(task_id, None)
        finally:
            # 确保任务完成后从线程管理器中移除
            with _task_threads_lock:
                _task_threads.pop(task_id, None)
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
                valid_statuses = ['pending', 'running', 'paused', 'completed', 'error', 'cancelled']
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
            
            if task.status == 'paused':
                return jsonify({
                    'success': False,
                    'message': '任务已暂停，请使用继续接口恢复运行',
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
            
            # 保存线程到管理器
            with _task_threads_lock:
                _task_threads[task_id] = thread
            
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
    
    @app.route('/api/dedup/tasks/<int:task_id>/pause', methods=['POST'])
    def pause_dedup_task(task_id):
        """
        暂停任务
        只能暂停运行中的任务
        """
        try:
            task = DedupTask.query.get(task_id)
            
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            if task.status != 'running':
                return jsonify({
                    'success': False,
                    'message': f'只能暂停运行中的任务，当前状态为: {task.status}',
                    'error_code': 'INVALID_STATUS'
                }), 400
            
            # 更新任务状态为暂停
            task.status = 'paused'
            db.session.commit()
            
            # 发送暂停通知到WebSocket
            from src.routes.websocket import emit_task_progress
            progress_percentage = 0.0
            if task.total_groups > 0:
                progress_percentage = round(
                    (task.processed_groups / task.total_groups) * 100, 2
                )
            emit_task_progress(task_id, {
                'status': 'paused',
                'processed_groups': task.processed_groups,
                'total_groups': task.total_groups,
                'progress_percentage': progress_percentage,
                'message': '任务已暂停'
            })
            
            task_dict = task.to_dict()
            task_dict['progress_percentage'] = progress_percentage
            
            return jsonify({
                'success': True,
                'message': '任务已暂停',
                'data': task_dict
            }), 200
        
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'暂停任务失败: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/dedup/tasks/<int:task_id>/resume', methods=['POST'])
    def resume_dedup_task(task_id):
        """
        继续运行任务
        只能继续已暂停的任务
        """
        try:
            task = DedupTask.query.get(task_id)
            
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            if task.status != 'paused':
                return jsonify({
                    'success': False,
                    'message': f'只能继续已暂停的任务，当前状态为: {task.status}',
                    'error_code': 'INVALID_STATUS'
                }), 400
            
            # 检查任务是否还有未完成的分组
            has_unfinished_groups = task.processed_groups < task.total_groups if task.total_groups > 0 else False
            
            # 检查执行线程是否还在运行
            thread_running = False
            with _task_threads_lock:
                thread = _task_threads.get(task_id)
                if thread and thread.is_alive():
                    thread_running = True
            
            # 更新任务状态为运行中（必须在检查线程之前更新，让等待循环能检测到）
            print(f"继续任务 {task_id}: 更新状态为 running...")
            task.status = 'running'
            db.session.commit()
            print(f"继续任务 {task_id}: 状态已更新为 running，线程运行状态: {thread_running}")
            
            # 如果线程不存在或已结束，且还有未完成的分组，重新启动线程
            if not thread_running:
                if has_unfinished_groups:
                    print(f"任务 {task_id} 的执行线程已结束，重新启动线程继续执行...")
                    thread = threading.Thread(
                        target=_execute_dedup_task,
                        args=(task_id,),
                        daemon=True
                    )
                    thread.start()
                    with _task_threads_lock:
                        _task_threads[task_id] = thread
                    print(f"任务 {task_id} 的新线程已启动")
                else:
                    print(f"任务 {task_id} 的执行线程已结束，但所有分组已完成，无需重新启动")
            else:
                print(f"任务 {task_id} 的执行线程仍在运行，状态已更新为 running，等待循环应该会检测到并继续执行")
                # 确保等待循环能检测到状态变化，强制刷新一次
                # 注意：这里不能直接操作线程，只能等待等待循环自己检测
            
            # 发送恢复通知到WebSocket
            from src.routes.websocket import emit_task_progress
            progress_percentage = 0.0
            if task.total_groups > 0:
                progress_percentage = round(
                    (task.processed_groups / task.total_groups) * 100, 2
                )
            emit_task_progress(task_id, {
                'status': 'running',
                'processed_groups': task.processed_groups,
                'total_groups': task.total_groups,
                'progress_percentage': progress_percentage,
                'message': '任务已恢复运行' if thread_running else '任务已重新启动并继续执行'
            })
            
            task_dict = task.to_dict()
            task_dict['progress_percentage'] = progress_percentage
            
            return jsonify({
                'success': True,
                'message': '任务已恢复运行' if thread_running else '任务已重新启动并继续执行',
                'data': task_dict
            }), 200
        
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'恢复任务失败: {str(e)}',
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
            
            # 如果任务正在运行，先暂停再取消（可选，也可以直接取消）
            # 这里选择直接取消，因为取消操作会立即停止任务执行
            
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
        获取相似重复对列表（按题目分组，每个题目只返回一次）
        
        请求参数:
            page (int, 可选): 页码，默认1
            page_size (int, 可选): 每页数量，默认20
            min_similarity (float, 可选): 最小相似度，默认0.8
            group_type (str, 可选): 题型筛选
            format (str, 可选): 返回格式，'grouped'=按题目分组（默认），'pairs'=原始对格式
        """
        try:
            page = request.args.get('page', type=int, default=1)
            page_size = request.args.get('page_size', type=int, default=20)
            min_similarity = request.args.get('min_similarity', type=float) or 0.8
            group_type = request.args.get('group_type', '').strip() or None
            format_type = request.args.get('format', 'grouped').strip() or 'grouped'
            
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
            
            # 构建查询（获取所有符合条件的相似对，不分页）
            query = QuestionDuplicatePair.query.filter_by(
                task_id=task_id,
                duplicate_type='similar'
            )
            
            if min_similarity:
                query = query.filter(QuestionDuplicatePair.similarity >= min_similarity)
            if group_type:
                query = query.filter(QuestionDuplicatePair.group_type == group_type)
            
            # 获取所有相似对
            all_pairs = query.order_by(desc(QuestionDuplicatePair.similarity)).all()
            
            if format_type == 'pairs':
                # 原始格式：返回所有对
                # 分页处理
                total = len(all_pairs)
                start = (page - 1) * page_size
                end = start + page_size
                paginated_pairs = all_pairs[start:end]
                
                pairs = []
                for pair in paginated_pairs:
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
                
                total_pages = (total + page_size - 1) // page_size
                
                return jsonify({
                    'success': True,
                    'message': '获取成功',
                    'data': {
                        'list': pairs,
                        'pagination': {
                            'page': page,
                            'page_size': page_size,
                            'total': total,
                            'total_pages': total_pages
                        }
                    }
                }), 200
            else:
                # 按题目分组格式：每个题目只返回一次，列出所有与它重复的题目
                # 构建题目到重复题目的映射
                question_duplicates = {}  # {question_id: [{'question_id': x, 'similarity': y, 'pair_id': z}, ...]}
                question_info = {}  # {question_id: {group_type, group_subject_id, group_channel_code, ...}}
                
                for pair in all_pairs:
                    q1 = pair.question_id_1
                    q2 = pair.question_id_2
                    similarity = float(pair.similarity) if pair.similarity else 0.0
                    
                    # 为每个题目记录重复信息
                    if q1 not in question_duplicates:
                        question_duplicates[q1] = []
                        question_info[q1] = {
                            'group_type': pair.group_type,
                            'group_subject_id': pair.group_subject_id,
                            'group_channel_code': pair.group_channel_code
                        }
                    
                    if q2 not in question_duplicates:
                        question_duplicates[q2] = []
                        question_info[q2] = {
                            'group_type': pair.group_type,
                            'group_subject_id': pair.group_subject_id,
                            'group_channel_code': pair.group_channel_code
                        }
                    
                    # 记录重复关系（双向）
                    question_duplicates[q1].append({
                        'question_id': q2,
                        'similarity': similarity,
                        'pair_id': pair.id
                    })
                    question_duplicates[q2].append({
                        'question_id': q1,
                        'similarity': similarity,
                        'pair_id': pair.id
                    })
                
                # 转换为列表格式，按题目ID排序
                grouped_list = []
                for question_id in sorted(question_duplicates.keys()):
                    duplicates = question_duplicates[question_id]
                    info = question_info[question_id]
                    
                    # 按相似度降序排序
                    duplicates.sort(key=lambda x: x['similarity'], reverse=True)
                    
                    # 获取题目基本信息
                    question = Question.query.filter_by(question_id=question_id).first()
                    subject_name = question.subject_name if question else None
                    
                    grouped_item = {
                        'question_id': question_id,
                        'duplicate_count': len(duplicates),
                        'duplicates': duplicates,
                        'max_similarity': duplicates[0]['similarity'] if duplicates else 0.0,
                        'min_similarity': duplicates[-1]['similarity'] if duplicates else 0.0,
                        'group': {
                            'type': info['group_type'],
                            'type_name': QuestionService.TYPE_NAMES.get(
                                info['group_type'], '未知题型'
                            ),
                            'subject_id': info['group_subject_id'],
                            'subject_name': subject_name,
                            'channel_code': info['group_channel_code']
                        }
                    }
                    grouped_list.append(grouped_item)
                
                # 按最大相似度降序排序
                grouped_list.sort(key=lambda x: x['max_similarity'], reverse=True)
                
                # 分页
                total = len(grouped_list)
                start = (page - 1) * page_size
                end = start + page_size
                paginated_list = grouped_list[start:end]
                total_pages = (total + page_size - 1) // page_size
                
                return jsonify({
                    'success': True,
                    'message': '获取成功',
                    'data': {
                        'list': paginated_list,
                        'pagination': {
                            'page': page,
                            'page_size': page_size,
                            'total': total,
                            'total_pages': total_pages
                        },
                        'format': 'grouped'
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