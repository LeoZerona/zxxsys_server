"""检查特征表结构"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db

with app.app_context():
    inspector = db.inspect(db.engine)
    cols = inspector.get_columns('question_dedup_features')
    print('question_dedup_features 表字段:')
    for c in cols:
        print(f'  {c["name"]}: {str(c["type"])}')

