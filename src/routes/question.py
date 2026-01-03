"""
题目查询相关路由
"""
from flask import request, jsonify
from src.services.question_service import QuestionService


def register_question_routes(app):
    """注册题目相关的路由"""
    
    @app.route('/api/questions', methods=['GET'])
    def get_question_list():
        """
        获取题目列表（分页）
        
        请求参数:
            type (str, 必填): 题型（1=单选, 2=多选, 3=判断, 4=填空, 8=计算分析）
            channel_code (str, 可选): 渠道代码
            subject_id (int, 可选): 科目 ID
            subject_name (str, 可选): 科目名称
            chapter_id (int, 可选): 章节 ID
            attr (str, 可选): 题目属性
            keyword (str, 可选): 关键字，用于搜索题目内容
            page (int, 可选): 页码，默认 1
            page_size (int, 可选): 每页数量，默认 20，最大 100
            include_answer (bool, 可选): 是否包含答案，默认 true
            include_analysis (bool, 可选): 是否包含解析，默认 true
        """
        try:
            # 获取请求参数
            question_type = request.args.get('type', '').strip()
            channel_code = request.args.get('channel_code', '').strip() or None
            subject_id = request.args.get('subject_id', type=int) or None
            subject_name = request.args.get('subject_name', '').strip() or None
            chapter_id = request.args.get('chapter_id', type=int) or None
            attr = request.args.get('attr', '').strip() or None
            # 支持 keyword 和 search 两种参数名
            keyword = request.args.get('keyword', '').strip() or request.args.get('search', '').strip() or None
            page = request.args.get('page', type=int, default=1)
            page_size = request.args.get('page_size', type=int, default=20)
            
            # 布尔参数处理
            include_answer_str = request.args.get('include_answer', 'true').strip().lower()
            include_answer = include_answer_str in ('true', '1', 'yes', 'on')
            
            include_analysis_str = request.args.get('include_analysis', 'true').strip().lower()
            include_analysis = include_analysis_str in ('true', '1', 'yes', 'on')
            
            # 验证必填参数
            if not question_type:
                return jsonify({
                    'success': False,
                    'message': '题型参数不能为空',
                    'error_code': 'INVALID_PARAMETER',
                    'details': {
                        'field': 'type',
                        'reason': '题型参数是必填的'
                    }
                }), 400
            
            # 调用服务层
            result = QuestionService.get_question_list(
                question_type=question_type,
                channel_code=channel_code,
                subject_id=subject_id,
                subject_name=subject_name,
                chapter_id=chapter_id,
                attr=attr,
                keyword=keyword,
                page=page,
                page_size=page_size,
                include_answer=include_answer,
                include_analysis=include_analysis
            )
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': result
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
    
    @app.route('/api/questions/<int:question_id>', methods=['GET'])
    def get_question_detail(question_id):
        """
        获取单个题目详情
        
        路径参数:
            question_id (int): 题目 ID
            
        请求参数:
            include_answer (bool, 可选): 是否包含答案，默认 true
            include_analysis (bool, 可选): 是否包含解析，默认 true
        """
        try:
            # 获取请求参数
            include_answer_str = request.args.get('include_answer', 'true').strip().lower()
            include_answer = include_answer_str in ('true', '1', 'yes', 'on')
            
            include_analysis_str = request.args.get('include_analysis', 'true').strip().lower()
            include_analysis = include_analysis_str in ('true', '1', 'yes', 'on')
            
            # 调用服务层
            result = QuestionService.get_question_detail(
                question_id=question_id,
                include_answer=include_answer,
                include_analysis=include_analysis
            )
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': '题目不存在或已被删除',
                    'error_code': 'NOT_FOUND'
                }), 404
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': result
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @app.route('/api/questions/batch', methods=['POST'])
    def batch_get_questions():
        """
        批量获取题目详情
        
        请求体:
            question_ids (array[int], 必填): 题目 ID 数组，最多 100 个
            include_answer (bool, 可选): 是否包含答案，默认 true
            include_analysis (bool, 可选): 是否包含解析，默认 true
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': '请求数据不能为空',
                    'error_code': 'INVALID_PARAMETER'
                }), 400
            
            question_ids = data.get('question_ids', [])
            
            if not question_ids:
                return jsonify({
                    'success': False,
                    'message': '题目ID列表不能为空',
                    'error_code': 'INVALID_PARAMETER',
                    'details': {
                        'field': 'question_ids',
                        'reason': '题目ID列表不能为空，且最多100个'
                    }
                }), 400
            
            if not isinstance(question_ids, list):
                return jsonify({
                    'success': False,
                    'message': '题目ID列表必须是数组',
                    'error_code': 'INVALID_PARAMETER'
                }), 400
            
            # 验证ID类型
            try:
                question_ids = [int(qid) for qid in question_ids]
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': '题目ID必须是整数',
                    'error_code': 'INVALID_PARAMETER'
                }), 400
            
            # 布尔参数处理
            include_answer = data.get('include_answer', True)
            if isinstance(include_answer, str):
                include_answer = include_answer.lower() in ('true', '1', 'yes', 'on')
            
            include_analysis = data.get('include_analysis', True)
            if isinstance(include_analysis, str):
                include_analysis = include_analysis.lower() in ('true', '1', 'yes', 'on')
            
            # 调用服务层
            result = QuestionService.batch_get_questions(
                question_ids=question_ids,
                include_answer=include_answer,
                include_analysis=include_analysis
            )
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': result
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
    
    @app.route('/api/questions/statistics', methods=['GET'])
    def get_question_statistics():
        """
        获取题目统计信息
        
        请求参数:
            channel_code (str, 可选): 渠道代码
            group_by (str, 可选): 分组方式（type/subject/channel）
        """
        try:
            channel_code = request.args.get('channel_code', '').strip() or None
            group_by = request.args.get('group_by', '').strip() or None
            
            # 调用服务层
            result = QuestionService.get_statistics(
                channel_code=channel_code,
                group_by=group_by
            )
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': result
            }), 200
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }), 500

