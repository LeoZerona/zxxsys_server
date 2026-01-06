"""
题目去重相关数据模型
用于存储去重任务记录、重复结果和特征数据
"""
import json
from datetime import datetime
from src.models import db


class DedupTask(db.Model):
    """去重任务表"""
    __tablename__ = 'dedup_tasks'
    
    id = db.Column(db.Integer, primary_key=True, comment='任务ID')
    task_name = db.Column(db.String(200), comment='任务名称（可选）')
    status = db.Column(db.Enum('pending', 'running', 'paused', 'completed', 'error', 'cancelled'), 
                       nullable=False, default='pending', comment='任务状态')
    total_groups = db.Column(db.Integer, default=0, comment='总分组数')
    processed_groups = db.Column(db.Integer, default=0, comment='已处理分组数')
    total_questions = db.Column(db.Integer, default=0, comment='总题目数')
    exact_duplicate_groups = db.Column(db.Integer, default=0, comment='完全重复组数')
    exact_duplicate_pairs = db.Column(db.Integer, default=0, comment='完全重复对数')
    similar_duplicate_pairs = db.Column(db.Integer, default=0, comment='相似重复对数')
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    error_message = db.Column(db.Text, comment='错误信息')
    config_json = db.Column(db.Text, comment='任务配置（JSON格式）')
    analysis_type = db.Column(db.String(50), default='full', comment='分析类型：full=全量分析, incremental=增量分析, custom=自定义分析')
    estimated_duration = db.Column(db.Integer, comment='预估时长（秒）')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    duplicate_pairs = db.relationship('QuestionDuplicatePair', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    duplicate_groups = db.relationship('QuestionDuplicateGroup', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    features = db.relationship('QuestionDedupFeature', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_name': self.task_name,
            'status': self.status,
            'total_groups': self.total_groups,
            'processed_groups': self.processed_groups,
            'total_questions': self.total_questions,
            'exact_duplicate_groups': self.exact_duplicate_groups,
            'exact_duplicate_pairs': self.exact_duplicate_pairs,
            'similar_duplicate_pairs': self.similar_duplicate_pairs,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'config': json.loads(self.config_json) if self.config_json else None,
            'analysis_type': self.analysis_type or 'full',
            'estimated_duration': self.estimated_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def set_config(self, config_dict):
        """设置配置（字典转JSON）"""
        self.config_json = json.dumps(config_dict, ensure_ascii=False) if config_dict else None
    
    def get_config(self):
        """获取配置（JSON转字典）"""
        return json.loads(self.config_json) if self.config_json else {}


class QuestionDuplicatePair(db.Model):
    """重复题目对表"""
    __tablename__ = 'question_duplicate_pairs'
    
    id = db.Column(db.Integer, primary_key=True, comment='记录ID')
    task_id = db.Column(db.Integer, db.ForeignKey('dedup_tasks.id', ondelete='CASCADE'), 
                        nullable=False, comment='任务ID')
    question_id_1 = db.Column(db.Integer, nullable=False, comment='题目ID 1')
    question_id_2 = db.Column(db.Integer, nullable=False, comment='题目ID 2')
    similarity = db.Column(db.Numeric(5, 4), nullable=False, comment='相似度 (0-1)')
    duplicate_type = db.Column(db.Enum('exact', 'similar'), nullable=False, comment='重复类型')
    group_type = db.Column(db.String(2), comment='题型')
    group_subject_id = db.Column(db.Integer, comment='科目ID')
    group_channel_code = db.Column(db.String(20), comment='渠道代码')
    detected_at = db.Column(db.DateTime, default=datetime.now, comment='检测时间')
    
    __table_args__ = (
        db.UniqueConstraint('task_id', 'question_id_1', 'question_id_2', name='uk_task_pair'),
        db.Index('idx_question_1', 'question_id_1'),
        db.Index('idx_question_2', 'question_id_2'),
        db.Index('idx_similarity', 'similarity'),
        db.Index('idx_type', 'duplicate_type'),
        db.Index('idx_group', 'group_type', 'group_subject_id', 'group_channel_code'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'question_id_1': self.question_id_1,
            'question_id_2': self.question_id_2,
            'similarity': float(self.similarity) if self.similarity else 0.0,
            'duplicate_type': self.duplicate_type,
            'group': {
                'type': self.group_type,
                'subject_id': self.group_subject_id,
                'channel_code': self.group_channel_code
            },
            'detected_at': self.detected_at.isoformat() if self.detected_at else None
        }


class QuestionDuplicateGroup(db.Model):
    """完全重复题目组表"""
    __tablename__ = 'question_duplicate_groups'
    
    id = db.Column(db.Integer, primary_key=True, comment='组ID')
    task_id = db.Column(db.Integer, db.ForeignKey('dedup_tasks.id', ondelete='CASCADE'), 
                        nullable=False, comment='任务ID')
    content_hash = db.Column(db.String(32), nullable=False, comment='内容哈希值（MD5）')
    question_count = db.Column(db.Integer, nullable=False, comment='题目数量')
    group_type = db.Column(db.String(2), comment='题型')
    group_subject_id = db.Column(db.Integer, comment='科目ID')
    group_channel_code = db.Column(db.String(20), comment='渠道代码')
    detected_at = db.Column(db.DateTime, default=datetime.now, comment='检测时间')
    
    # 关系
    items = db.relationship('QuestionDuplicateGroupItem', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_content_hash', 'content_hash'),
        db.Index('idx_group', 'group_type', 'group_subject_id', 'group_channel_code'),
    )
    
    def to_dict(self, include_items=True):
        """转换为字典"""
        result = {
            'id': self.id,
            'task_id': self.task_id,
            'content_hash': self.content_hash,
            'question_count': self.question_count,
            'group': {
                'type': self.group_type,
                'subject_id': self.group_subject_id,
                'channel_code': self.group_channel_code
            },
            'detected_at': self.detected_at.isoformat() if self.detected_at else None
        }
        
        if include_items:
            result['question_ids'] = [item.question_id for item in self.items.all()]
        
        return result


class QuestionDuplicateGroupItem(db.Model):
    """完全重复组明细表"""
    __tablename__ = 'question_duplicate_group_items'
    
    id = db.Column(db.Integer, primary_key=True, comment='记录ID')
    group_id = db.Column(db.Integer, db.ForeignKey('question_duplicate_groups.id', ondelete='CASCADE'), 
                         nullable=False, comment='组ID')
    task_id = db.Column(db.Integer, db.ForeignKey('dedup_tasks.id', ondelete='CASCADE'), 
                        nullable=False, comment='任务ID')
    question_id = db.Column(db.Integer, nullable=False, comment='题目ID')
    
    __table_args__ = (
        db.UniqueConstraint('group_id', 'question_id', name='uk_group_question'),
        db.Index('idx_question_id', 'question_id'),
    )


class QuestionDedupFeature(db.Model):
    """题目去重特征表"""
    __tablename__ = 'question_dedup_features'
    
    id = db.Column(db.Integer, primary_key=True, comment='记录ID')
    task_id = db.Column(db.Integer, db.ForeignKey('dedup_tasks.id', ondelete='CASCADE'), 
                        nullable=False, comment='任务ID')
    question_id = db.Column(db.Integer, nullable=False, comment='题目ID')
    cleaned_content = db.Column(db.Text, comment='清洗后的题目内容')
    content_hash = db.Column(db.String(32), comment='内容哈希值（MD5）')
    ngram_json = db.Column(db.Text, comment='N-gram特征（JSON数组格式）')
    minhash_json = db.Column(db.Text, comment='MinHash指纹（JSON数组格式）')
    group_type = db.Column(db.String(2), comment='题型')
    group_subject_id = db.Column(db.Integer, comment='科目ID')
    group_channel_code = db.Column(db.String(20), comment='渠道代码')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        db.UniqueConstraint('task_id', 'question_id', name='uk_task_question'),
        db.Index('idx_content_hash', 'content_hash'),
        db.Index('idx_group', 'group_type', 'group_subject_id', 'group_channel_code'),
    )
    
    def set_ngrams(self, ngrams):
        """设置N-gram特征（列表转JSON）"""
        if ngrams:
            if isinstance(ngrams, set):
                ngrams = list(ngrams)
            self.ngram_json = json.dumps(ngrams, ensure_ascii=False)
        else:
            self.ngram_json = None
    
    def get_ngrams(self):
        """获取N-gram特征（JSON转列表）"""
        if self.ngram_json:
            return json.loads(self.ngram_json)
        return []
    
    def set_minhash(self, minhash):
        """设置MinHash指纹（列表转JSON）"""
        if minhash:
            self.minhash_json = json.dumps(minhash, ensure_ascii=False)
        else:
            self.minhash_json = None
    
    def get_minhash(self):
        """获取MinHash指纹（JSON转列表）"""
        if self.minhash_json:
            return json.loads(self.minhash_json)
        return []
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'question_id': self.question_id,
            'cleaned_content': self.cleaned_content,
            'content_hash': self.content_hash,
            'ngrams': self.get_ngrams(),
            'minhash': self.get_minhash(),
            'group': {
                'type': self.group_type,
                'subject_id': self.group_subject_id,
                'channel_code': self.group_channel_code
            },
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

