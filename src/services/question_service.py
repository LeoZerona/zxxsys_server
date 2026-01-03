"""
题目查询服务
负责题目列表查询、详情查询、批量查询等业务逻辑
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, or_
from src.models import db
from src.models.question import Question
from src.services.question_aggregation_service import QuestionAggregationService


class QuestionService:
    """题目查询服务"""
    
    # 支持的题型
    SUPPORTED_TYPES = ['1', '2', '3', '4', '8']
    
    # 题型名称映射
    TYPE_NAMES = {
        '1': '单选题',
        '2': '多选题',
        '3': '判断题',
        '4': '填空题',
        '8': '计算分析题'
    }
    
    @staticmethod
    def get_question_list(
        question_type: str,
        channel_code: Optional[str] = None,
        subject_id: Optional[int] = None,
        subject_name: Optional[str] = None,
        chapter_id: Optional[int] = None,
        attr: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        include_answer: bool = True,
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        获取题目列表（分页）
        
        Args:
            question_type: 题型（必填）
            channel_code: 渠道代码
            subject_id: 科目 ID
            subject_name: 科目名称
            chapter_id: 章节 ID
            attr: 题目属性
            keyword: 关键字，用于搜索题目内容
            page: 页码
            page_size: 每页数量
            include_answer: 是否包含答案
            include_analysis: 是否包含解析
            
        Returns:
            包含题目列表和分页信息的字典
        """
        # 验证题型
        if question_type not in QuestionService.SUPPORTED_TYPES:
            raise ValueError(f"题型参数无效，支持的类型：{','.join(QuestionService.SUPPORTED_TYPES)}")
        
        # 构建查询条件
        query = Question.query.filter(
            Question.type == question_type,
            Question.is_del == 0
        )
        
        # 渠道过滤
        if channel_code:
            query = query.filter(Question.channel_code == channel_code)
        
        # 科目过滤
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        
        if subject_name:
            query = query.filter(Question.subject_name == subject_name)
        
        # 章节过滤
        if chapter_id:
            query = query.filter(Question.chapter_id == chapter_id)
        
        # 属性过滤
        if attr:
            query = query.filter(Question.attr == attr)
        
        # 关键字搜索（在题目内容中搜索）
        if keyword:
            query = query.filter(Question.content.like(f'%{keyword}%'))
        
        # 获取总数
        total = query.count()
        
        # 分页
        page = max(1, page)
        page_size = min(max(1, page_size), 100)  # 限制最大100条
        offset = (page - 1) * page_size
        
        # 排序：按 sort 字段和 question_id
        questions = query.order_by(Question.sort, Question.question_id).offset(offset).limit(page_size).all()
        
        # 聚合数据
        channel_code_for_agg = channel_code or (questions[0].channel_code if questions else 'default')
        aggregated_questions = QuestionAggregationService.batch_aggregate_questions(
            questions, channel_code_for_agg, include_answer, include_analysis
        )
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        return {
            'list': aggregated_questions,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': total_pages
            }
        }
    
    @staticmethod
    def get_question_detail(
        question_id: int,
        include_answer: bool = True,
        include_analysis: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        获取单个题目详情
        
        Args:
            question_id: 题目 ID
            include_answer: 是否包含答案
            include_analysis: 是否包含解析
            
        Returns:
            题目详情字典，如果不存在返回 None
        """
        question = Question.query.filter_by(
            question_id=question_id,
            is_del=0
        ).first()
        
        if not question:
            return None
        
        # 聚合数据
        result = QuestionAggregationService.aggregate_question(
            question, question.channel_code, include_answer, include_analysis
        )
        
        return result
    
    @staticmethod
    def batch_get_questions(
        question_ids: List[int],
        include_answer: bool = True,
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        批量获取题目详情
        
        Args:
            question_ids: 题目 ID 列表（最多100个）
            include_answer: 是否包含答案
            include_analysis: 是否包含解析
            
        Returns:
            包含题目列表和未找到ID的字典
        """
        # 限制数量
        if len(question_ids) > 100:
            raise ValueError("题目ID列表最多100个")
        
        if not question_ids:
            return {
                'questions': [],
                'not_found_ids': []
            }
        
        # 查询题目
        questions = Question.query.filter(
            Question.question_id.in_(question_ids),
            Question.is_del == 0
        ).all()
        
        # 找到的ID集合
        found_ids = {q.question_id for q in questions}
        not_found_ids = [qid for qid in question_ids if qid not in found_ids]
        
        # 聚合数据
        if questions:
            # 按渠道分组聚合（不同渠道可能有不同的数据结构）
            questions_by_channel = {}
            for q in questions:
                channel = q.channel_code
                if channel not in questions_by_channel:
                    questions_by_channel[channel] = []
                questions_by_channel[channel].append(q)
            
            aggregated_questions = []
            for channel, q_list in questions_by_channel.items():
                channel_results = QuestionAggregationService.batch_aggregate_questions(
                    q_list, channel, include_answer, include_analysis
                )
                aggregated_questions.extend(channel_results)
            
            # 保持原始ID顺序
            id_to_question = {q['question_id']: q for q in aggregated_questions}
            aggregated_questions = [id_to_question[qid] for qid in question_ids if qid in found_ids]
        else:
            aggregated_questions = []
        
        return {
            'questions': aggregated_questions,
            'not_found_ids': not_found_ids
        }
    
    @staticmethod
    def get_statistics(
        channel_code: Optional[str] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取题目统计信息
        
        Args:
            channel_code: 渠道代码
            group_by: 分组方式（type/subject/channel）
            
        Returns:
            统计信息字典
        """
        # 构建基础查询
        query = Question.query.filter(Question.is_del == 0)
        
        if channel_code:
            query = query.filter(Question.channel_code == channel_code)
        
        # 总数
        total = query.count()
        
        result = {'total': total}
        
        if group_by == 'type':
            # 按题型统计
            statistics = []
            for q_type in QuestionService.SUPPORTED_TYPES:
                count_query = Question.query.filter(
                    Question.type == q_type,
                    Question.is_del == 0
                )
                if channel_code:
                    count_query = count_query.filter(Question.channel_code == channel_code)
                
                count = count_query.count()
                if count > 0:
                    statistics.append({
                        'type': q_type,
                        'type_name': QuestionService.TYPE_NAMES.get(q_type, '未知题型'),
                        'count': count
                    })
            
            result['statistics'] = statistics
        
        elif group_by == 'subject':
            # 按科目统计
            from sqlalchemy import func
            stats_query = db.session.query(
                Question.subject_id,
                Question.subject_name,
                func.count(Question.question_id).label('count')
            ).filter(Question.is_del == 0)
            
            if channel_code:
                stats_query = stats_query.filter(Question.channel_code == channel_code)
            
            stats_query = stats_query.group_by(
                Question.subject_id,
                Question.subject_name
            ).order_by(func.count(Question.question_id).desc())
            
            statistics = []
            for row in stats_query.all():
                statistics.append({
                    'subject_id': row.subject_id,
                    'subject_name': row.subject_name,
                    'count': row.count
                })
            
            result['statistics'] = statistics
        
        elif group_by == 'channel':
            # 按渠道统计
            from sqlalchemy import func
            stats_query = db.session.query(
                Question.channel_code,
                func.count(Question.question_id).label('count')
            ).filter(Question.is_del == 0).group_by(
                Question.channel_code
            ).order_by(func.count(Question.question_id).desc())
            
            statistics = []
            for row in stats_query.all():
                statistics.append({
                    'channel_code': row.channel_code,
                    'count': row.count
                })
            
            result['statistics'] = statistics
        
        return result
    
    @staticmethod
    def get_question_groups() -> List[Dict[str, Any]]:
        """
        预处理阶段：数据分组
        查询所有分组（按 type, subject_id, channel_code），统计每组数量
        
        这是题目去重功能的预处理步骤，将题目按业务逻辑分组，每组分别处理
        
        Returns:
            分组列表，每个分组包含 type, subject_id, channel_code, count 等信息
            格式：
            [
                {
                    'type': '1',
                    'type_name': '单选题',
                    'subject_id': 100,
                    'subject_name': '数学',
                    'channel_code': 'default',
                    'count': 2000
                },
                ...
            ]
        """
        from sqlalchemy import func
        
        # 查询所有分组，统计每组数量
        # SQL等价于：
        # SELECT type, subject_id, channel_code, COUNT(*) as count
        # FROM teach_question
        # WHERE is_del = 0
        # GROUP BY type, subject_id, channel_code
        # 注意：只按 (type, subject_id, channel_code) 分组，不包含 subject_name
        # 使用 MAX(subject_name) 获取一个代表性的 subject_name（如果存在）
        groups_query = db.session.query(
            Question.type,
            Question.subject_id,
            func.max(Question.subject_name).label('subject_name'),  # 使用 MAX 获取一个代表性值
            Question.channel_code,
            func.count(Question.question_id).label('count')
        ).filter(
            Question.is_del == 0
        ).group_by(
            Question.type,
            Question.subject_id,
            Question.channel_code
        ).order_by(
            func.count(Question.question_id).desc()  # 按数量降序排列，大组在前
        )
        
        # 转换为字典列表
        groups = []
        for row in groups_query.all():
            groups.append({
                'type': row.type,
                'type_name': QuestionService.TYPE_NAMES.get(row.type, '未知题型'),
                'subject_id': row.subject_id,
                'subject_name': row.subject_name,
                'channel_code': row.channel_code,
                'count': row.count
            })
        
        return groups
    
    @staticmethod
    def get_questions_by_group(
        question_type: str,
        subject_id: int,
        channel_code: str
    ) -> List[Question]:
        """
        根据分组条件查询题目列表
        
        Args:
            question_type: 题型
            subject_id: 科目ID
            channel_code: 渠道代码
            
        Returns:
            题目列表
        """
        questions = Question.query.filter(
            Question.type == question_type,
            Question.subject_id == subject_id,
            Question.channel_code == channel_code,
            Question.is_del == 0
        ).all()
        
        return questions

