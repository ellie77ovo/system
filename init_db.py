import os
import sys
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Student, Teacher, Course, Score

def init_database():
    with app.app_context():
        # 删除所有表并重新创建
        print("删除现有表...")
        db.drop_all()
        print("创建新表...")
        db.create_all()
        
        # 创建默认管理员账户
        print("创建默认账户...")
        admin = Teacher(
            工号='admin',
            密码='admin123',
            姓名='系统管理员'
        )
        db.session.add(admin)
        
        # 创建示例数据
        try:
            # 创建示例教师
            teacher1 = Teacher(
                工号='T001',
                密码='123456',
                姓名='张老师'
            )
            teacher2 = Teacher(
                工号='T002',
                密码='123456', 
                姓名='李老师'
            )
            db.session.add_all([teacher1, teacher2])
            
            # 创建示例学生
            students = [
                Student(学号='2023001', 密码='123456', 姓名='张三', 班级='计算机科学1班', 性别='男'),
                Student(学号='2023002', 密码='123456', 姓名='李四', 班级='计算机科学1班', 性别='女'),
                Student(学号='2023003', 密码='123456', 姓名='王五', 班级='计算机科学2班', 性别='男'),
                Student(学号='2023004', 密码='123456', 姓名='赵六', 班级='计算机科学2班', 性别='女')
            ]
            db.session.add_all(students)
            
            # 创建示例课程
            courses = [
                Course(课程代码='C0001', 名称='计算机基础', 开课学期='2023-2024第一学期', 课程时间='周一 1-2节', 教师工号='T001'),
                Course(课程代码='C0002', 名称='数据结构', 开课学期='2023-2024第一学期', 课程时间='周三 3-4节', 教师工号='T001'),
                Course(课程代码='C0003', 名称='数据库原理', 开课学期='2023-2024第一学期', 课程时间='周五 1-2节', 教师工号='T002')
            ]
            db.session.add_all(courses)
            
            # 创建示例成绩
            scores = [
                Score(学号='2023001', 课程代码='C0001', 分数=85.5, 录入教师工号='T001'),
                Score(学号='2023002', 课程代码='C0001', 分数=92.0, 录入教师工号='T001'),
                Score(学号='2023001', 课程代码='C0002', 分数=78.5, 录入教师工号='T001'),
                Score(学号='2023003', 课程代码='C0003', 分数=88.0, 录入教师工号='T002')
            ]
            db.session.add_all(scores)
            
            db.session.commit()
            print("数据库初始化完成！")
            print("\n测试账户信息:")
            print("管理员: admin/admin123")
            print("教师: T001/123456, T002/123456")
            print("学生: 2023001/123456, 2023002/123456, 2023003/123456, 2023004/123456")
            
        except Exception as e:
            db.session.rollback()
            print(f"初始化示例数据时出错: {e}")
            raise

if __name__ == '__main__':
    init_database()