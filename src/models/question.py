"""
题目相关数据模型
"""
from datetime import datetime
from src.models import db


class Question(db.Model):
    """题目主表模型"""
    __tablename__ = 'teach_question'
    
    question_id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer)
    subject_name = db.Column(db.String(50))
    chapter_id = db.Column(db.Integer)
    subject_type = db.Column(db.String(50))
    subject_type_name = db.Column(db.String(50), index=True)
    content = db.Column(db.Text)
    content_detail = db.Column(db.String(100))
    type = db.Column(db.String(2), index=True)  # 题型：1=单选, 2=多选, 3=判断, 4=填空, 8=计算分析
    analysis = db.Column(db.Text)
    attr = db.Column(db.String(2), index=True)
    sort = db.Column(db.Integer, default=0)
    remark = db.Column(db.String(100))
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    create_time = db.Column(db.DateTime)
    is_del = db.Column(db.Integer, default=0)  # 0=正常, 1=删除
    
    def to_dict(self, include_answer=True, include_analysis=True):
        """转换为字典"""
        result = {
            'question_id': self.question_id,
            'type': self.type,
            'type_name': self._get_type_name(),
            'subject_id': self.subject_id,
            'subject_name': self.subject_name,
            'chapter_id': self.chapter_id,
            'subject_type': self.subject_type,
            'subject_type_name': self.subject_type_name,
            'content': self.content,
            'content_detail': self.content_detail,
            'attr': self.attr,
            'sort': self.sort,
            'channel_code': self.channel_code,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }
        
        if include_analysis and self.analysis:
            result['analysis'] = self.analysis
        
        return result
    
    def _get_type_name(self):
        """获取题型名称"""
        type_map = {
            '1': '单选题',
            '2': '多选题',
            '3': '判断题',
            '4': '填空题',
            '8': '计算分析题'
        }
        return type_map.get(self.type, '未知题型')
    
    def __repr__(self):
        return f'<Question {self.question_id}: {self.type}>'


class SingleChoiceAnswer(db.Model):
    """单选题答案表"""
    __tablename__ = 'teach_ans_single_choice'
    
    singlechoice_id = db.Column(db.Integer, primary_key=True)
    option_true = db.Column(db.String(200))
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    
    def to_dict(self):
        return {
            'correct_answer': self.option_true,
            'option_true': self.option_true
        }


class SingleChoiceOption(db.Model):
    """单选题选项表"""
    __tablename__ = 'teach_ans_single_choice_child'
    
    singlechoice_child_id = db.Column(db.Integer, primary_key=True)
    singlechoice_id = db.Column(db.Integer, index=True)
    option_content = db.Column(db.String(512))
    label = db.Column(db.String(2))
    seq = db.Column(db.Integer)
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    
    def to_dict(self):
        return {
            'label': self.label,
            'content': self.option_content,
            'seq': self.seq
        }


class MultChoiceAnswer(db.Model):
    """多选题答案表"""
    __tablename__ = 'teach_ans_mult_choice'
    
    multchoice_id = db.Column(db.Integer, primary_key=True)
    option_true = db.Column(db.String(200))
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    
    def to_dict(self):
        # 多选题答案可能是逗号分隔的字符串，如 "A,B"
        correct_answer = self.option_true
        if correct_answer:
            # 尝试解析为数组
            if ',' in correct_answer:
                correct_answer = [opt.strip() for opt in correct_answer.split(',')]
            else:
                correct_answer = [correct_answer]
        else:
            correct_answer = []
        
        return {
            'correct_answer': correct_answer,
            'option_true': self.option_true
        }


class MultChoiceOption(db.Model):
    """多选题选项表"""
    __tablename__ = 'teach_ans_mult_choice_child'
    
    multchoice_child_id = db.Column(db.Integer, primary_key=True)
    multchoice_id = db.Column(db.Integer, index=True)
    option_content = db.Column(db.String(512))
    label = db.Column(db.String(2))
    seq = db.Column(db.Integer)
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    
    def to_dict(self):
        return {
            'label': self.label,
            'content': self.option_content,
            'seq': self.seq
        }


class JudgmentAnswer(db.Model):
    """判断题答案表"""
    __tablename__ = 'teach_ans_judgment'
    
    judgment_id = db.Column(db.Integer, primary_key=True)
    option_true = db.Column(db.String(1))  # 1=正确, 2=错误
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    
    def to_dict(self):
        return {
            'correct_answer': self.option_true,
            'option_true': self.option_true
        }


class BlankAnswer(db.Model):
    """填空题答案表"""
    __tablename__ = 'teach_ans_blank'
    
    blank_id = db.Column(db.Integer, primary_key=True)
    answer_content = db.Column(db.Text)
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    create_time = db.Column(db.DateTime)
    is_del = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'correct_answer': self.answer_content,
            'answer_content': self.answer_content
        }


class CalcParentAnswer(db.Model):
    """计算分析题答案表（大题）"""
    __tablename__ = 'teach_ans_calcparent'
    
    calcparent_id = db.Column(db.Integer, primary_key=True)
    type2 = db.Column(db.String(2), default='0')  # 1=分录题, 2=填空题
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    
    def to_dict(self):
        return {
            'type2': self.type2
        }


class CalcChildAnswer(db.Model):
    """计算分析题子题答案表"""
    __tablename__ = 'teach_ans_calcchild'
    
    calcchild_id = db.Column(db.Integer, primary_key=True)
    calcparent_id = db.Column(db.Integer, index=True)
    type = db.Column(db.String(2))  # 1=分录题, 2=填空题, 3=不定项选择
    content = db.Column(db.String(1000))
    answer_content = db.Column(db.String(8000))
    analysis = db.Column(db.String(5000))
    option_true = db.Column(db.String(200))
    sort = db.Column(db.Integer, default=0)
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    create_time = db.Column(db.DateTime)
    is_del = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        result = {
            'calcchild_id': self.calcchild_id,
            'type': self.type,
            'content': self.content,
            'answer_content': self.answer_content,
            'analysis': self.analysis,
            'option_true': self.option_true,
            'sort': self.sort
        }
        return result


class CalcChildItem(db.Model):
    """计算分析题子题选项表"""
    __tablename__ = 'teach_ans_calcchild_item'
    
    calcchild_item_id = db.Column(db.Integer, primary_key=True)
    calcchild_id = db.Column(db.Integer, index=True)
    option_content = db.Column(db.String(512))
    label = db.Column(db.String(2))
    seq = db.Column(db.Integer)
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    
    def to_dict(self):
        return {
            'label': self.label,
            'content': self.option_content,
            'seq': self.seq
        }


class BlankChildAnswer(db.Model):
    """填空题答案子表（关联计算分析大题）"""
    __tablename__ = 'teach_ans_blankchild'
    
    blankchild_id = db.Column(db.Integer, primary_key=True)
    calcparent_id = db.Column(db.Integer, index=True)
    type = db.Column(db.String(2))  # 4=填空题
    content = db.Column(db.String(1000))
    answer_content = db.Column(db.String(8000))
    analysis = db.Column(db.String(8000))
    sort = db.Column(db.Integer, default=0)
    channel_code = db.Column(db.String(20), nullable=False, index=True)
    create_time = db.Column(db.DateTime)
    is_del = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'blankchild_id': self.blankchild_id,
            'type': self.type,
            'content': self.content,
            'answer_content': self.answer_content,
            'analysis': self.analysis,
            'sort': self.sort
        }

