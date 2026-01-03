"""
数据模型模块
统一导出所有模型
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# 初始化数据库实例（单例模式）
db = SQLAlchemy()

# 导入所有模型（必须放在 db 初始化之后）
from src.models.user import User
from src.models.email_verification import EmailVerification
from src.models.refresh_token import RefreshToken
from src.models.login_attempt import LoginAttempt
from src.models.question import (
    Question, SingleChoiceAnswer, SingleChoiceOption,
    MultChoiceAnswer, MultChoiceOption, JudgmentAnswer,
    BlankAnswer, CalcParentAnswer, CalcChildAnswer,
    CalcChildItem, BlankChildAnswer
)
from src.models.question_dedup import (
    DedupTask, QuestionDuplicatePair, QuestionDuplicateGroup,
    QuestionDuplicateGroupItem, QuestionDedupFeature
)

# 统一导出
__all__ = [
    'db', 'User', 'EmailVerification', 'RefreshToken', 'LoginAttempt', 'datetime',
    'Question', 'SingleChoiceAnswer', 'SingleChoiceOption',
    'MultChoiceAnswer', 'MultChoiceOption', 'JudgmentAnswer',
    'BlankAnswer', 'CalcParentAnswer', 'CalcChildAnswer',
    'CalcChildItem', 'BlankChildAnswer',
    'DedupTask', 'QuestionDuplicatePair', 'QuestionDuplicateGroup',
    'QuestionDuplicateGroupItem', 'QuestionDedupFeature'
]

