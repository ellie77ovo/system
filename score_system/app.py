from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grades.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 创建上传目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, teacher, admin
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50))  # 仅学生需要

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QueryPeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由和视图函数
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('admin_dashboard'))
        else:
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
    if current_user.role != 'student':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    # 检查是否在查询时间段内
    current_time = datetime.utcnow()
    active_period = QueryPeriod.query.filter(
        QueryPeriod.start_date <= current_time,
        QueryPeriod.end_date >= current_time,
        QueryPeriod.is_active == True
    ).first()
    
    if not active_period:
        flash('当前不在成绩查询时间段内')
        return render_template('student_dashboard.html', grades=[], can_query=False)
    
    grades = Grade.query.filter_by(student_id=current_user.id).all()
    return render_template('student_dashboard.html', grades=grades, can_query=True)

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    return render_template('teacher_dashboard.html')

@app.route('/teacher/upload_grades', methods=['GET', 'POST'])
@login_required
def upload_grades():
    if current_user.role != 'teacher':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 处理单个成绩录入
        if 'single_grade' in request.form:
            student_username = request.form.get('student_username')
            course_name = request.form.get('course_name')
            score = request.form.get('score')
            semester = request.form.get('semester')
            
            student = User.query.filter_by(username=student_username, role='student').first()
            if student:
                grade = Grade(
                    student_id=student.id,
                    course_name=course_name,
                    score=float(score),
                    semester=semester
                )
                db.session.add(grade)
                db.session.commit()
                flash('成绩录入成功')
            else:
                flash('未找到该学生')
        
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
                    required_columns = ['学号', '课程', '分数', '学期']
                    if not all(col in df.columns for col in required_columns):
                        flash('文件格式错误，缺少必要列')
                        return redirect(url_for('upload_grades'))
                    
                    # 批量导入成绩
                    success_count = 0
                    for _, row in df.iterrows():
                        student = User.query.filter_by(username=str(row['学号']), role='student').first()
                        if student:
                            grade = Grade(
                                student_id=student.id,
                                course_name=row['课程'],
                                score=float(row['分数']),
                                semester=row['学期']
                            )
                            db.session.add(grade)
                            success_count += 1
                    
                    db.session.commit()
                    flash(f'成功导入 {success_count} 条成绩记录')
                    
                except Exception as e:
                    flash(f'导入失败: {str(e)}')
    
    return render_template('upload_grades.html')

@app.route('/teacher/query_period', methods=['GET', 'POST'])
@login_required
def set_query_period():
    if current_user.role != 'teacher':
        flash('无权访问此页面')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
        
        # 停用其他活跃的时间段
        QueryPeriod.query.filter_by(is_active=True).update({'is_active': False})
        
        new_period = QueryPeriod(
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        db.session.add(new_period)
        db.session.commit()
        flash('查询时间段设置成功')
    
    current_period = QueryPeriod.query.filter_by(is_active=True).first()
    return render_template('query_period.html', current_period=current_period)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)