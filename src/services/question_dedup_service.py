"""
题目去重服务
实现题目重复性排查功能，支持单分组处理、进度记录和断点续传
"""
import json
import os
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from src.models import db
from src.models.question import Question
from src.models.question_dedup import (
    DedupTask, QuestionDuplicatePair, QuestionDuplicateGroup,
    QuestionDuplicateGroupItem, QuestionDedupFeature
)
from src.services.question_service import QuestionService


class QuestionDedupService:
    """题目去重服务"""
    
    # 进度文件路径（放在项目根目录）
    PROGRESS_FILE = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')),
        'question_dedup_progress.json'
    )
    
    @staticmethod
    def get_progress() -> Dict[str, Any]:
        """
        获取当前处理进度
        
        Returns:
            进度信息字典，包含：
            - current_group_index: 当前处理的分组索引（从0开始）
            - total_groups: 总分组数
            - processed_groups: 已处理的分组数
            - current_group: 当前分组信息
            - status: 状态（pending/running/completed/error）
            - last_update: 最后更新时间
        """
        if os.path.exists(QuestionDedupService.PROGRESS_FILE):
            try:
                with open(QuestionDedupService.PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"读取进度文件失败: {e}")
                return QuestionDedupService._init_progress()
        else:
            return QuestionDedupService._init_progress()
    
    @staticmethod
    def _init_progress() -> Dict[str, Any]:
        """初始化进度信息"""
        return {
            'current_group_index': 0,
            'total_groups': 0,
            'processed_groups': 0,
            'current_group': None,
            'status': 'pending',  # pending/running/completed/error
            'last_update': None,
            'groups': []  # 所有分组列表
        }
    
    @staticmethod
    def save_progress(progress: Dict[str, Any]):
        """保存进度信息到文件"""
        progress['last_update'] = datetime.now().isoformat()
        try:
            with open(QuestionDedupService.PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存进度文件失败: {e}")
            raise
    
    @staticmethod
    def init_dedup_session(task_name: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        初始化去重会话
        获取所有分组并初始化进度，同时创建数据库任务记录
        
        Args:
            task_name: 任务名称（可选）
            config: 任务配置（可选）
            
        Returns:
            初始化的进度信息（包含task_id）
        """
        # 获取所有分组
        groups = QuestionService.get_question_groups()
        
        # 创建数据库任务记录
        task = DedupTask(
            task_name=task_name,
            status='pending',
            total_groups=len(groups),
            processed_groups=0,
            total_questions=0,
            exact_duplicate_groups=0,
            exact_duplicate_pairs=0,
            similar_duplicate_pairs=0
        )
        if config:
            task.set_config(config)
        
        db.session.add(task)
        db.session.commit()
        task_id = task.id
        
        progress = {
            'task_id': task_id,  # 添加task_id到进度
            'current_group_index': 0,
            'total_groups': len(groups),
            'processed_groups': 0,
            'current_group': None,
            'status': 'pending',
            'last_update': datetime.now().isoformat(),
            'groups': groups
        }
        
        QuestionDedupService.save_progress(progress)
        return progress
    
    @staticmethod
    def get_next_group() -> Optional[Dict[str, Any]]:
        """
        获取下一个待处理的分组
        
        Returns:
            分组信息字典，如果所有分组都已处理完则返回 None
        """
        progress = QuestionDedupService.get_progress()
        
        # 如果没有初始化，先初始化
        if progress['total_groups'] == 0 or not progress.get('groups'):
            progress = QuestionDedupService.init_dedup_session()
        
        current_index = progress['current_group_index']
        groups = progress['groups']
        
        # 检查是否还有未处理的分组
        if current_index >= len(groups):
            progress['status'] = 'completed'
            QuestionDedupService.save_progress(progress)
            return None
        
        # 获取当前分组
        current_group = groups[current_index]
        progress['current_group'] = current_group
        progress['status'] = 'running'
        QuestionDedupService.save_progress(progress)
        
        # 更新数据库任务状态
        task_id = progress.get('task_id')
        if task_id:
            task = DedupTask.query.get(task_id)
            if task and current_index >= len(groups):
                task.status = 'completed'
                task.completed_at = datetime.now()
                db.session.commit()
        
        return current_group
    
    @staticmethod
    def _save_group_results_to_db(task_id: int, results: Dict[str, Any]):
        """
        保存分组处理结果到数据库
        
        Args:
            task_id: 任务ID
            results: 处理结果字典
        """
        group = results.get('group', {})
        group_type = group.get('type')
        group_subject_id = group.get('subject_id')
        group_channel_code = group.get('channel_code')
        
        try:
            # 保存完全重复组
            exact_duplicates = results.get('exact_duplicates', [])
            for dup_group in exact_duplicates:
                # 创建组记录
                db_group = QuestionDuplicateGroup(
                    task_id=task_id,
                    content_hash=dup_group.get('content_hash', ''),
                    question_count=dup_group.get('count', 0),
                    group_type=group_type,
                    group_subject_id=group_subject_id,
                    group_channel_code=group_channel_code
                )
                db.session.add(db_group)
                db.session.flush()  # 获取group_id
                
                # 创建组明细记录
                question_ids = dup_group.get('question_ids', [])
                for qid in question_ids:
                    item = QuestionDuplicateGroupItem(
                        group_id=db_group.id,
                        task_id=task_id,
                        question_id=qid
                    )
                    db.session.add(item)
            
            # 保存相似重复对
            similar_duplicates = results.get('similar_duplicates', [])
            for dup_pair in similar_duplicates:
                pair = QuestionDuplicatePair(
                    task_id=task_id,
                    question_id_1=dup_pair.get('question_id_1'),
                    question_id_2=dup_pair.get('question_id_2'),
                    similarity=dup_pair.get('similarity', 0.0),
                    duplicate_type='similar',
                    group_type=group_type,
                    group_subject_id=group_subject_id,
                    group_channel_code=group_channel_code
                )
                db.session.add(pair)
            
            # 更新任务统计
            task = DedupTask.query.get(task_id)
            if task:
                # 完全重复对数 = 每组C(n,2)的和
                for dup_group in exact_duplicates:
                    count = dup_group.get('count', 0)
                    if count > 1:
                        pairs_count = count * (count - 1) // 2
                        task.exact_duplicate_pairs += pairs_count
                        task.exact_duplicate_groups += 1
                
                # 相似重复对数
                task.similar_duplicate_pairs += len(similar_duplicates)
                
                # 总题目数
                task.total_questions += results.get('total_questions', 0)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"保存数据到数据库失败: {e}")
            raise
    
    @staticmethod
    def mark_group_completed(results: Optional[Dict[str, Any]] = None):
        """
        标记当前分组处理完成，并更新数据库任务记录
        
        Args:
            results: 该分组的处理结果（可选）
        """
        progress = QuestionDedupService.get_progress()
        task_id = progress.get('task_id')
        
        # 如果提供了结果，保存结果到JSON（用于断点续传）
        if results:
            if 'results' not in progress:
                progress['results'] = []
            progress['results'].append({
                'group_index': progress['current_group_index'],
                'group': progress['current_group'],
                'results': results,
                'processed_at': datetime.now().isoformat()
            })
            
            # 保存数据到数据库
            if task_id:
                QuestionDedupService._save_group_results_to_db(task_id, results)
        
        # 更新进度
        progress['current_group_index'] += 1
        progress['processed_groups'] += 1
        progress['current_group'] = None
        
        # 更新数据库任务记录
        if task_id:
            task = DedupTask.query.get(task_id)
            if task:
                task.processed_groups = progress['processed_groups']
                # 检查是否全部完成
                if progress['current_group_index'] >= progress['total_groups']:
                    task.status = 'completed'
                    task.completed_at = datetime.now()
                    progress['status'] = 'completed'
                else:
                    task.status = 'running'
                    progress['status'] = 'pending'
                db.session.commit()
        else:
            # 如果没有task_id，只更新JSON
            if progress['current_group_index'] >= progress['total_groups']:
                progress['status'] = 'completed'
            else:
                progress['status'] = 'pending'
        
        QuestionDedupService.save_progress(progress)
    
    @staticmethod
    def reset_progress():
        """重置进度（重新开始）"""
        if os.path.exists(QuestionDedupService.PROGRESS_FILE):
            os.remove(QuestionDedupService.PROGRESS_FILE)
        return QuestionDedupService.init_dedup_session()
    
    @staticmethod
    def _clean_question_content(content: str) -> str:
        """
        清洗题干内容
        
        Args:
            content: 原始题干内容
            
        Returns:
            清洗后的题干内容
        """
        if not content:
            return ""
        
        # 1. 去除 HTML 标签
        content = re.sub(r'<[^>]+>', '', content)
        
        # 2. 全角转半角
        def full_to_half(text):
            """全角转半角"""
            result = ""
            for char in text:
                code = ord(char)
                # 全角空格（12288）转半角空格（32）
                if code == 12288:
                    result += chr(32)
                # 全角字符转半角（65281-65374 对应 33-126）
                elif 65281 <= code <= 65374:
                    result += chr(code - 65248)
                else:
                    result += char
            return result
        
        content = full_to_half(content)
        
        # 3. 图片/公式占位符标准化
        # [图片1] [图片2] ... → [IMG]
        content = re.sub(r'\[图片\d+\]', '[IMG]', content)
        # [公式1] [公式2] ... → [FORMULA]
        content = re.sub(r'\[公式\d+\]', '[FORMULA]', content)
        
        # 4. 空格标准化：多个连续空格合并为一个，去除首尾空白
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # 5. 去除不可见字符（控制字符、零宽字符等）
        # 保留常见的空格、换行符、制表符，去除其他控制字符
        content = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F\u200B-\u200D\uFEFF]', '', content)
        
        return content
    
    @staticmethod
    def _clean_questions(questions: List[Question]) -> List[Dict[str, Any]]:
        """
        批量清洗题目
        
        Args:
            questions: 题目列表
            
        Returns:
            清洗后的题目列表，每个元素包含 question_id 和 cleaned_content
        """
        cleaned = []
        for q in questions:
            cleaned_content = QuestionDedupService._clean_question_content(q.content or "")
            cleaned.append({
                'question_id': q.question_id,
                'cleaned_content': cleaned_content,
                'original_content': q.content
            })
        return cleaned
    
    @staticmethod
    def _find_exact_duplicates(cleaned_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        找出完全相同的题目（通过哈希值）
        
        Args:
            cleaned_questions: 清洗后的题目列表
            
        Returns:
            完全重复的题目组列表
            [
                {
                    'question_ids': [123, 456, 789],
                    'count': 3,
                    'similarity': 1.0
                },
                ...
            ]
        """
        # 1. 计算每个题目的 MD5 哈希值
        hash_to_questions = {}
        for item in cleaned_questions:
            content = item['cleaned_content']
            # 空内容跳过
            if not content:
                continue
            
            # 计算 MD5 哈希值
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if content_hash not in hash_to_questions:
                hash_to_questions[content_hash] = []
            hash_to_questions[content_hash].append(item['question_id'])
        
        # 2. 找出数量>1的组（完全重复的题目）
        exact_duplicates = []
        for content_hash, question_ids in hash_to_questions.items():
            if len(question_ids) > 1:
                exact_duplicates.append({
                    'question_ids': question_ids,
                    'count': len(question_ids),
                    'similarity': 1.0,
                    'content_hash': content_hash
                })
        
        return exact_duplicates
    
    @staticmethod
    def process_single_group(group: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个分组
        
        Args:
            group: 分组信息字典，包含 type, subject_id, channel_code, count 等
            
        Returns:
            处理结果字典，包含重复题目对等信息
        """
        # 获取该分组的所有题目
        questions = QuestionService.get_questions_by_group(
            question_type=group['type'],
            subject_id=group['subject_id'],
            channel_code=group['channel_code']
        )
        
        print(f"\n处理分组: {group['type_name']} - {group['subject_name']} ({group['channel_code']})")
        print(f"题目数量: {len(questions)}")
        
        # 步骤1 - 清洗题干
        cleaned_questions = QuestionDedupService._clean_questions(questions)
        print(f"清洗完成: {len(cleaned_questions)} 题")
        
        # 步骤2 - 秒筛完全一样的题
        exact_duplicates = QuestionDedupService._find_exact_duplicates(cleaned_questions)
        print(f"完全重复: {len(exact_duplicates)} 组")
        
        # TODO: 步骤3 - 提取特征片段（N-gram）
        # ngram_features = QuestionDedupService._extract_ngrams(cleaned_questions)
        
        # TODO: 步骤4 - 生成指纹（MinHash）
        # fingerprints = QuestionDedupService._generate_fingerprints(ngram_features)
        
        # TODO: 步骤5 - LSH 分桶
        # buckets = QuestionDedupService._lsh_bucketing(fingerprints)
        
        # TODO: 步骤6 - 桶内精算重复程度
        # duplicates = QuestionDedupService._calculate_similarity(buckets)
        
        return {
            'group': group,
            'total_questions': len(questions),
            'exact_duplicates': exact_duplicates,  # 完全重复的题目组
            'similar_duplicates': [],  # 相似重复的题目对（待实现）
            'processed_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def process_next_group() -> Optional[Dict[str, Any]]:
        """
        处理下一个分组（便捷方法）
        
        Returns:
            处理结果字典，如果所有分组都处理完则返回 None
        """
        # 获取下一个分组
        group = QuestionDedupService.get_next_group()
        if not group:
            print("所有分组都已处理完成！")
            return None
        
        try:
            # 处理该分组
            results = QuestionDedupService.process_single_group(group)
            
            # 标记完成
            QuestionDedupService.mark_group_completed(results)
            
            return results
        except Exception as e:
            # 记录错误
            progress = QuestionDedupService.get_progress()
            progress['status'] = 'error'
            progress['last_error'] = str(e)
            progress['error_time'] = datetime.now().isoformat()
            QuestionDedupService.save_progress(progress)
            raise
    
    @staticmethod
    def get_summary() -> Dict[str, Any]:
        """
        获取处理摘要信息
        
        Returns:
            摘要信息字典
        """
        progress = QuestionDedupService.get_progress()
        
        summary = {
            'status': progress.get('status', 'pending'),
            'total_groups': progress.get('total_groups', 0),
            'processed_groups': progress.get('processed_groups', 0),
            'remaining_groups': progress.get('total_groups', 0) - progress.get('processed_groups', 0),
            'progress_percentage': 0.0,
            'current_group': progress.get('current_group'),
            'last_update': progress.get('last_update')
        }
        
        if summary['total_groups'] > 0:
            summary['progress_percentage'] = (summary['processed_groups'] / summary['total_groups']) * 100
        
        return summary

