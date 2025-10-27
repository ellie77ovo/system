from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123123@localhost:5432/grade_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 创建上传目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 在模板环境中注册 Python 内置函数
@app.context_processor
def utility_processor():
    return dict(hasattr=hasattr)

# 数据库模型
class Student(UserMixin, db.Model):
    __tablename__ = 'student'
    学号 = db.Column(db.String(20), primary_key=True)
    密码 = db.Column(db.String(100), nullable=False)
    姓名 = db.Column(db.String(20), nullable=False)
    班级 = db.Column(db.String(30), nullable=False)
    性别 = db.Column(db.String(2), nullable=False)
    
    # Flask-Login 需要的属性
    def get_id(self):
        return f"student_{self.学号}"

class Teacher(UserMixin, db.Model):
    __tablename__ = 'teacher'
    工号 = db.Column(db.String(20), primary_key=True)
    密码 = db.Column(db.String(100), nullable=False)
    姓名 = db.Column(db.String(20), nullable=False)
    
    # Flask-Login 需要的属性
    def get_id(self):
        return f"teacher_{self.工号}"
    
    @property
    def is_admin(self):
        return self.工号 == 'admin'

class Course(db.Model):
    __tablename__ = 'course'
    课程代码 = db.Column(db.String(20), primary_key=True)
    名称 = db.Column(db.String(50), nullable=False)
    开课学期 = db.Column(db.String(20), nullable=False)
    课程时间 = db.Column(db.String(100), nullable=False)
    教师工号 = db.Column(db.String(20), db.ForeignKey('teacher.工号'), nullable=False)
    成绩开放开始时间 = db.Column(db.DateTime, nullable=True)
    成绩开放结束时间 = db.Column(db.DateTime, nullable=True)
    
    # 关系
    教师 = db.relationship('Teacher', backref=db.backref('courses', lazy=True))
    
    @property
    def 成绩开放状态(self):
        if not self.成绩开放开始时间 or not self.成绩开放结束时间:
            return "未设置"
        
        current_time = datetime.now()
        if current_time < self.成绩开放开始时间:
            return "未开始"
        elif self.成绩开放开始时间 <= current_time <= self.成绩开放结束时间:
            return "开放中"
        else:
            return "已结束"

class Score(db.Model):
    __tablename__ = 'score'
    成绩记录id = db.Column(db.Integer, primary_key=True)
    学号 = db.Column(db.String(20), db.ForeignKey('student.学号'), nullable=False)
    课程代码 = db.Column(db.String(20), db.ForeignKey('course.课程代码'), nullable=False)
    分数 = db.Column(db.Float, nullable=False)
    录入教师工号 = db.Column(db.String(20), db.ForeignKey('teacher.工号'), nullable=False)
    录入修改时间 = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    学生 = db.relationship('Student', backref=db.backref('scores', lazy=True))
    课程 = db.relationship('Course', backref=db.backref('scores', lazy=True))
    录入教师 = db.relationship('Teacher', backref=db.backref('录入的成绩', lazy=True))

# 自定义用户加载器 - 修复 SQLAlchemy 2.0 兼容性
@login_manager.user_loader
def load_user(user_id):
    try:
        if user_id.startswith('student_'):
            student_id = user_id.replace('student_', '')
            return db.session.get(Student, student_id)  # 使用新的查询语法
        elif user_id.startswith('teacher_'):
            teacher_id = user_id.replace('teacher_', '')
            return db.session.get(Teacher, teacher_id)  # 使用新的查询语法
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# 路由和视图函数
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 先尝试作为学生登录 - 修复查询语法
        student = db.session.get(Student, username)
        if student and student.密码 == password:
            login_user(student)
            return redirect(url_for('student_dashboard'))
        
        # 再尝试作为教师/管理员登录 - 修复查询语法
        teacher = db.session.get(Teacher, username)
        if teacher and teacher.密码 == password:
            login_user(teacher)
            if teacher.工号 == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('teacher_dashboard'))
        
        flash('用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if not hasattr(current_user, '学号'):
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    # 查询当前学生的所有成绩记录
    scores = db.session.query(Score).filter_by(学号=current_user.学号).all()
    
    # 获取学生选修的所有课程（用于显示课程列表）
    student_courses = db.session.query(Course).join(Score).filter(
        Score.学号 == current_user.学号
    ).all()
    
    # 检查每门课程的成绩开放时间，构建可查询的成绩列表
    valid_grades = []
    for score in scores:
        course = db.session.get(Course, score.课程代码)
        current_time = datetime.now()
        
        # 检查成绩开放时间是否设置且当前时间在开放时间内
        if (course.成绩开放开始时间 and course.成绩开放结束时间 and 
            course.成绩开放开始时间 <= current_time <= course.成绩开放结束时间):
            valid_grades.append({
                'course_name': course.名称,
                'course_code': course.课程代码,
                'score': score.分数,
                'semester': course.开课学期,
                'course_time': course.课程时间,
                'teacher_name': course.教师.姓名
            })
    
    return render_template('student_dashboard.html', 
                         grades=valid_grades,
                         all_courses=student_courses,
                         can_query=len(valid_grades) > 0)

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if not hasattr(current_user, '工号') or current_user.工号 == 'admin':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    # 获取教师教授的课程 - 修复查询语法
    teacher_courses = db.session.query(Course).filter_by(教师工号=current_user.工号).all()
    
    return render_template('teacher_dashboard.html', courses=teacher_courses)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not hasattr(current_user, '工号') or current_user.工号 != 'admin':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    # 获取所有学生和教师信息 - 修复查询语法
    students = db.session.query(Student).all()
    teachers = db.session.query(Teacher).filter(Teacher.工号 != 'admin').all()
    
    return render_template('admin_dashboard.html', 
                         students=students, 
                         teachers=teachers)

@app.route('/teacher/upload_grades', methods=['GET', 'POST'])
@login_required
def upload_grades():
    if not hasattr(current_user, '工号') or current_user.工号 == 'admin':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    # 获取教师教授的课程 - 修复查询语法
    teacher_courses = db.session.query(Course).filter_by(教师工号=current_user.工号).all()
    
    if request.method == 'POST':
        # 处理单个成绩录入
        if 'single_grade' in request.form:
            student_id = request.form.get('student_id')
            course_code = request.form.get('course_code')
            score_value = request.form.get('score')
            
            # 验证学生存在 - 修复查询语法
            student = db.session.get(Student, student_id)
            if not student:
                flash('未找到该学生')
                return redirect(url_for('upload_grades'))
            
            # 验证课程属于当前教师 - 修复查询语法
            course = db.session.get(Course, course_code)
            if not course or course.教师工号 != current_user.工号:
                flash('无权操作该课程')
                return redirect(url_for('upload_grades'))
            
            # 检查是否已有成绩记录 - 修复查询语法
            existing_score = db.session.query(Score).filter_by(
                学号=student_id, 课程代码=course_code
            ).first()
            
            if existing_score:
                existing_score.分数 = float(score_value)
                existing_score.录入修改时间 = datetime.now()
                flash('成绩更新成功')
            else:
                new_score = Score(
                    学号=student_id,
                    课程代码=course_code,
                    分数=float(score_value),
                    录入教师工号=current_user.工号
                )
                db.session.add(new_score)
                flash('成绩录入成功')
            
            db.session.commit()
        
        # 处理批量导入
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                
                try:
                    # 处理Excel文件
                    if file.filename.endswith('.xlsx'):
                        df = pd.read_excel(filepath)
                    # 处理CSV文件
                    elif file.filename.endswith('.csv'):
                        df = pd.read_csv(filepath)
                    else:
                        flash('不支持的文件格式')
                        return redirect(url_for('upload_grades'))
                    
                    # 验证数据格式
                    required_columns = ['学号', '课程代码', '分数']
                    if not all(col in df.columns for col in required_columns):
                        flash('文件格式错误，缺少必要列')
                        return redirect(url_for('upload_grades'))
                    
                    # 批量导入成绩
                    success_count = 0
                    for _, row in df.iterrows():
                        student_id = str(row['学号'])
                        course_code = str(row['课程代码'])
                        score_value = float(row['分数'])
                        
                        # 验证学生存在 - 修复查询语法
                        student = db.session.get(Student, student_id)
                        if not student:
                            continue
                        
                        # 验证课程属于当前教师 - 修复查询语法
                        course = db.session.get(Course, course_code)
                        if not course or course.教师工号 != current_user.工号:
                            continue
                        
                        # 更新或插入成绩 - 修复查询语法
                        existing_score = db.session.query(Score).filter_by(
                            学号=student_id, 课程代码=course_code
                        ).first()
                        
                        if existing_score:
                            existing_score.分数 = score_value
                            existing_score.录入修改时间 = datetime.now()
                        else:
                            new_score = Score(
                                学号=student_id,
                                课程代码=course_code,
                                分数=score_value,
                                录入教师工号=current_user.工号
                            )
                            db.session.add(new_score)
                        
                        success_count += 1
                    
                    db.session.commit()
                    flash(f'成功导入 {success_count} 条成绩记录')
                    
                except Exception as e:
                    flash(f'导入失败: {str(e)}')
    
    return render_template('upload_grades.html', courses=teacher_courses)

@app.route('/teacher/query_period', methods=['GET', 'POST'])
@login_required
def set_query_period():
    if not hasattr(current_user, '工号') or current_user.工号 == 'admin':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    # 获取特定课程（如果通过URL参数指定）- 修复查询语法
    course_code = request.args.get('course_code')
    selected_course = None
    if course_code:
        selected_course = db.session.get(Course, course_code)
        if not selected_course or selected_course.教师工号 != current_user.工号:
            flash('无权操作该课程')
            selected_course = None
    
    # 获取教师教授的课程 - 修复查询语法
    teacher_courses = db.session.query(Course).filter_by(教师工号=current_user.工号).all()
    
    if request.method == 'POST':
        course_code = request.form.get('course_code')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        # 验证课程属于当前教师 - 修复查询语法
        course = db.session.get(Course, course_code)
        if course and course.教师工号 == current_user.工号:
            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
                course.成绩开放开始时间 = start_date
                course.成绩开放结束时间 = end_date
            else:
                # 清除开放时间设置
                course.成绩开放开始时间 = None
                course.成绩开放结束时间 = None
                
            db.session.commit()
            flash('查询时间段设置成功')
            return redirect(url_for('set_query_period', course_code=course_code))
        else:
            flash('无权操作该课程')
    
    return render_template('query_period.html', 
                         courses=teacher_courses, 
                         selected_course=selected_course)

@app.route('/admin/student_management', methods=['GET', 'POST'])
@login_required
def student_management():
    if not hasattr(current_user, '工号') or current_user.工号 != 'admin':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # 添加学生
            new_student = Student(
                学号=request.form.get('student_id'),
                密码=request.form.get('password'),
                姓名=request.form.get('name'),
                班级=request.form.get('class_name'),
                性别=request.form.get('gender')
            )
            db.session.add(new_student)
            flash('学生添加成功')
            
        elif action == 'edit':
            # 编辑学生 - 修复查询语法
            student_id = request.form.get('student_id')
            student = db.session.get(Student, student_id)
            if student:
                student.姓名 = request.form.get('name')
                student.班级 = request.form.get('class_name')
                student.性别 = request.form.get('gender')
                if request.form.get('password'):
                    student.密码 = request.form.get('password')
                flash('学生信息更新成功')
            
        elif action == 'delete':
            # 删除学生 - 修复查询语法
            student_id = request.form.get('student_id')
            student = db.session.get(Student, student_id)
            if student:
                db.session.delete(student)
                flash('学生删除成功')
        
        db.session.commit()
    
    # 获取所有学生 - 修复查询语法
    students = db.session.query(Student).all()
    return render_template('student_management.html', students=students)

@app.route('/admin/teacher_management', methods=['GET', 'POST'])
@login_required
def teacher_management():
    if not hasattr(current_user, '工号') or current_user.工号 != 'admin':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # 添加教师
            new_teacher = Teacher(
                工号=request.form.get('teacher_id'),
                密码=request.form.get('password'),
                姓名=request.form.get('name')
            )
            db.session.add(new_teacher)
            flash('教师添加成功')
            
        elif action == 'edit':
            # 编辑教师 - 修复查询语法
            teacher_id = request.form.get('teacher_id')
            teacher = db.session.get(Teacher, teacher_id)
            if teacher and teacher.工号 != 'admin':
                teacher.姓名 = request.form.get('name')
                if request.form.get('password'):
                    teacher.密码 = request.form.get('password')
                flash('教师信息更新成功')
            
        elif action == 'delete':
            # 删除教师 - 修复查询语法
            teacher_id = request.form.get('teacher_id')
            teacher = db.session.get(Teacher, teacher_id)
            if teacher and teacher.工号 != 'admin':
                db.session.delete(teacher)
                flash('教师删除成功')
        
        db.session.commit()
    
    # 获取所有教师（除了管理员）- 修复查询语法
    teachers = db.session.query(Teacher).filter(Teacher.工号 != 'admin').all()
    return render_template('teacher_management.html', teachers=teachers)

@app.route('/teacher/course_management', methods=['GET', 'POST'])
@login_required
def course_management():
    if not hasattr(current_user, '工号') or current_user.工号 == 'admin':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # 添加课程
            new_course = Course(
                课程代码=request.form.get('course_code'),
                名称=request.form.get('course_name'),
                开课学期=request.form.get('semester'),
                课程时间=request.form.get('course_time'),
                教师工号=current_user.工号,
            )
            db.session.add(new_course)
            db.session.commit()
            flash('课程添加成功')
            
        elif action == 'edit':
            # 编辑课程基本信息 - 修复查询语法
            course_code = request.form.get('course_code')
            course = db.session.get(Course, course_code)
            if course and course.教师工号 == current_user.工号:
                course.名称 = request.form.get('course_name')
                course.开课学期 = request.form.get('semester')
                course.课程时间 = request.form.get('course_time')
                db.session.commit()
                flash('课程信息更新成功')
            else:
                flash('无权操作该课程')
    
    # 获取教师教授的课程 - 修复查询语法
    teacher_courses = db.session.query(Course).filter_by(教师工号=current_user.工号).all()
    return render_template('course_management.html', courses=teacher_courses)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)