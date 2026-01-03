"""
题目数据聚合服务
负责将题目主表、答案表、选项表的数据聚合组装成统一的 JSON 结构
"""
from typing import List, Dict, Any, Optional
from src.models import db
from src.models.question import (
    Question, SingleChoiceAnswer, SingleChoiceOption,
    MultChoiceAnswer, MultChoiceOption, JudgmentAnswer,
    BlankAnswer, CalcParentAnswer, CalcChildAnswer,
    CalcChildItem, BlankChildAnswer
)


class QuestionAggregationService:
    """题目聚合服务"""
    
    @staticmethod
    def aggregate_question(question: Question, channel_code: str, 
                          include_answer: bool = True, 
                          include_analysis: bool = True) -> Dict[str, Any]:
        """
        聚合单个题目的完整数据
        
        Args:
            question: 题目对象
            channel_code: 渠道代码
            include_answer: 是否包含答案
            include_analysis: 是否包含解析
            
        Returns:
            聚合后的题目数据字典
        """
        # 基础题目信息
        result = question.to_dict(include_answer=include_answer, include_analysis=include_analysis)
        
        # 根据题型聚合答案和选项
        question_type = question.type
        
        if question_type == '1':
            # 单选题
            result.update(QuestionAggregationService._aggregate_single_choice(
                question.question_id, channel_code, include_answer
            ))
        elif question_type == '2':
            # 多选题
            result.update(QuestionAggregationService._aggregate_mult_choice(
                question.question_id, channel_code, include_answer
            ))
        elif question_type == '3':
            # 判断题
            result.update(QuestionAggregationService._aggregate_judgment(
                question.question_id, channel_code, include_answer
            ))
        elif question_type == '4':
            # 填空题
            result.update(QuestionAggregationService._aggregate_blank(
                question.question_id, channel_code, include_answer
            ))
        elif question_type == '8':
            # 计算分析题
            result.update(QuestionAggregationService._aggregate_calc_analysis(
                question.question_id, channel_code, include_answer, include_analysis
            ))
        
        return result
    
    @staticmethod
    def _aggregate_single_choice(question_id: int, channel_code: str, 
                                 include_answer: bool) -> Dict[str, Any]:
        """聚合单选题数据"""
        result = {}
        
        if include_answer:
            # 查询答案
            answer = SingleChoiceAnswer.query.filter_by(
                singlechoice_id=question_id,
                channel_code=channel_code
            ).first()
            
            if answer:
                result['answer'] = answer.to_dict()
            else:
                result['answer'] = {'correct_answer': None, 'option_true': None}
        
        # 查询选项
        options = SingleChoiceOption.query.filter_by(
            singlechoice_id=question_id,
            channel_code=channel_code
        ).order_by(SingleChoiceOption.seq).all()
        
        result['options'] = [opt.to_dict() for opt in options]
        
        return result
    
    @staticmethod
    def _aggregate_mult_choice(question_id: int, channel_code: str, 
                               include_answer: bool) -> Dict[str, Any]:
        """聚合多选题数据"""
        result = {}
        
        if include_answer:
            # 查询答案
            answer = MultChoiceAnswer.query.filter_by(
                multchoice_id=question_id,
                channel_code=channel_code
            ).first()
            
            if answer:
                result['answer'] = answer.to_dict()
            else:
                result['answer'] = {'correct_answer': [], 'option_true': None}
        
        # 查询选项
        options = MultChoiceOption.query.filter_by(
            multchoice_id=question_id,
            channel_code=channel_code
        ).order_by(MultChoiceOption.seq).all()
        
        result['options'] = [opt.to_dict() for opt in options]
        
        return result
    
    @staticmethod
    def _aggregate_judgment(question_id: int, channel_code: str, 
                           include_answer: bool) -> Dict[str, Any]:
        """聚合判断题数据"""
        result = {'options': []}  # 判断题无选项
        
        if include_answer:
            # 查询答案
            answer = JudgmentAnswer.query.filter_by(
                judgment_id=question_id,
                channel_code=channel_code
            ).first()
            
            if answer:
                result['answer'] = answer.to_dict()
            else:
                result['answer'] = {'correct_answer': None, 'option_true': None}
        
        return result
    
    @staticmethod
    def _aggregate_blank(question_id: int, channel_code: str, 
                        include_answer: bool) -> Dict[str, Any]:
        """聚合填空题数据"""
        result = {'options': []}  # 填空题无选项
        
        if include_answer:
            # 查询答案
            answer = BlankAnswer.query.filter_by(
                blank_id=question_id,
                channel_code=channel_code,
                is_del=0
            ).first()
            
            if answer:
                result['answer'] = answer.to_dict()
            else:
                result['answer'] = {'correct_answer': None, 'answer_content': None}
        
        return result
    
    @staticmethod
    def _aggregate_calc_analysis(question_id: int, channel_code: str, 
                                include_answer: bool, 
                                include_analysis: bool) -> Dict[str, Any]:
        """聚合计算分析题数据"""
        result = {}
        
        # 查询大题答案
        calc_parent = CalcParentAnswer.query.filter_by(
            calcparent_id=question_id,
            channel_code=channel_code
        ).first()
        
        # 初始化 answer 对象，无论是否包含答案都要有 answer 结构
        if calc_parent and include_answer:
            result['answer'] = calc_parent.to_dict()
        else:
            result['answer'] = {}
        
        # 查询子题（calcchild）
        sub_questions = []
        calc_children = CalcChildAnswer.query.filter_by(
            calcparent_id=question_id,
            channel_code=channel_code,
            is_del=0
        ).order_by(CalcChildAnswer.sort).all()
        
        for calc_child in calc_children:
            sub_question = {
                'calcchild_id': calc_child.calcchild_id,
                'type': calc_child.type,
                'content': calc_child.content,
                'sort': calc_child.sort
            }
            
            if include_answer:
                sub_question['answer'] = {
                    'answer_content': calc_child.answer_content,
                    'option_true': calc_child.option_true
                }
            
            if include_analysis and calc_child.analysis:
                sub_question['analysis'] = calc_child.analysis
            
            # 如果子题是不定项选择题（type=3），查询选项
            if calc_child.type == '3':
                items = CalcChildItem.query.filter_by(
                    calcchild_id=calc_child.calcchild_id,
                    channel_code=channel_code
                ).order_by(CalcChildItem.seq).all()
                sub_question['options'] = [item.to_dict() for item in items]
            else:
                sub_question['options'] = []
            
            sub_questions.append(sub_question)
        
        # 查询填空子题（blankchild）
        blank_children = BlankChildAnswer.query.filter_by(
            calcparent_id=question_id,
            channel_code=channel_code,
            is_del=0
        ).order_by(BlankChildAnswer.sort).all()
        
        for blank_child in blank_children:
            sub_question = {
                'blankchild_id': blank_child.blankchild_id,
                'type': blank_child.type,
                'content': blank_child.content,
                'sort': blank_child.sort
            }
            
            if include_answer:
                sub_question['answer'] = {
                    'answer_content': blank_child.answer_content
                }
            
            if include_analysis and blank_child.analysis:
                sub_question['analysis'] = blank_child.analysis
            
            sub_question['options'] = []
            sub_questions.append(sub_question)
        
        # 按 sort 排序
        sub_questions.sort(key=lambda x: x.get('sort', 0))
        
        # 子题始终放在 answer.sub_questions 中，符合 API 文档规范
        result['answer']['sub_questions'] = sub_questions
        
        return result
    
    @staticmethod
    def batch_aggregate_questions(questions: List[Question], channel_code: str,
                                  include_answer: bool = True,
                                  include_analysis: bool = True) -> List[Dict[str, Any]]:
        """
        批量聚合题目数据
        
        Args:
            questions: 题目对象列表
            channel_code: 渠道代码
            include_answer: 是否包含答案
            include_analysis: 是否包含解析
            
        Returns:
            聚合后的题目数据列表
        """
        results = []
        
        # 按题型分组，以便批量查询
        questions_by_type = {}
        for q in questions:
            q_type = q.type
            if q_type not in questions_by_type:
                questions_by_type[q_type] = []
            questions_by_type[q_type].append(q)
        
        # 批量查询并聚合
        for q_type, q_list in questions_by_type.items():
            question_ids = [q.question_id for q in q_list]
            
            if q_type == '1':
                # 批量查询单选题答案和选项
                answers = {a.singlechoice_id: a for a in 
                          SingleChoiceAnswer.query.filter(
                              SingleChoiceAnswer.singlechoice_id.in_(question_ids),
                              SingleChoiceAnswer.channel_code == channel_code
                          ).all()}
                
                options_dict = {}
                options_list = SingleChoiceOption.query.filter(
                    SingleChoiceOption.singlechoice_id.in_(question_ids),
                    SingleChoiceOption.channel_code == channel_code
                ).order_by(SingleChoiceOption.singlechoice_id, SingleChoiceOption.seq).all()
                
                for opt in options_list:
                    if opt.singlechoice_id not in options_dict:
                        options_dict[opt.singlechoice_id] = []
                    options_dict[opt.singlechoice_id].append(opt.to_dict())
                
                # 组装数据
                for q in q_list:
                    result = q.to_dict(include_answer=include_answer, include_analysis=include_analysis)
                    if include_answer:
                        answer = answers.get(q.question_id)
                        result['answer'] = answer.to_dict() if answer else {'correct_answer': None, 'option_true': None}
                    result['options'] = options_dict.get(q.question_id, [])
                    results.append(result)
            
            elif q_type == '2':
                # 批量查询多选题答案和选项
                answers = {a.multchoice_id: a for a in 
                          MultChoiceAnswer.query.filter(
                              MultChoiceAnswer.multchoice_id.in_(question_ids),
                              MultChoiceAnswer.channel_code == channel_code
                          ).all()}
                
                options_dict = {}
                options_list = MultChoiceOption.query.filter(
                    MultChoiceOption.multchoice_id.in_(question_ids),
                    MultChoiceOption.channel_code == channel_code
                ).order_by(MultChoiceOption.multchoice_id, MultChoiceOption.seq).all()
                
                for opt in options_list:
                    if opt.multchoice_id not in options_dict:
                        options_dict[opt.multchoice_id] = []
                    options_dict[opt.multchoice_id].append(opt.to_dict())
                
                for q in q_list:
                    result = q.to_dict(include_answer=include_answer, include_analysis=include_analysis)
                    if include_answer:
                        answer = answers.get(q.question_id)
                        result['answer'] = answer.to_dict() if answer else {'correct_answer': [], 'option_true': None}
                    result['options'] = options_dict.get(q.question_id, [])
                    results.append(result)
            
            elif q_type == '3':
                # 批量查询判断题答案
                answers = {a.judgment_id: a for a in 
                          JudgmentAnswer.query.filter(
                              JudgmentAnswer.judgment_id.in_(question_ids),
                              JudgmentAnswer.channel_code == channel_code
                          ).all()}
                
                for q in q_list:
                    result = q.to_dict(include_answer=include_answer, include_analysis=include_analysis)
                    result['options'] = []
                    if include_answer:
                        answer = answers.get(q.question_id)
                        result['answer'] = answer.to_dict() if answer else {'correct_answer': None, 'option_true': None}
                    results.append(result)
            
            elif q_type == '4':
                # 批量查询填空题答案
                answers = {a.blank_id: a for a in 
                          BlankAnswer.query.filter(
                              BlankAnswer.blank_id.in_(question_ids),
                              BlankAnswer.channel_code == channel_code,
                              BlankAnswer.is_del == 0
                          ).all()}
                
                for q in q_list:
                    result = q.to_dict(include_answer=include_answer, include_analysis=include_analysis)
                    result['options'] = []
                    if include_answer:
                        answer = answers.get(q.question_id)
                        result['answer'] = answer.to_dict() if answer else {'correct_answer': None, 'answer_content': None}
                    results.append(result)
            
            elif q_type == '8':
                # 计算分析题需要单独处理（因为结构复杂）
                for q in q_list:
                    result = QuestionAggregationService.aggregate_question(
                        q, channel_code, include_answer, include_analysis
                    )
                    results.append(result)
        
        # 保持原始顺序
        question_id_map = {q.question_id: i for i, q in enumerate(questions)}
        results.sort(key=lambda x: question_id_map.get(x['question_id'], 999999))
        
        return results

