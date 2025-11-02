from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    # is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    todos = db.relationship('Todo', backref='user', lazy=True)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('todo'))
    return redirect(url_for('auth'))

@app.route('/auth')
def auth():
    if 'user_id' in session:
        return redirect(url_for('todo'))
    return render_template('login_register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.full_name
        flash('Login successful!', 'success')
        return redirect(url_for('todo'))
    else:
        flash('Invalid email or password', 'error')
        return redirect(url_for('auth'))

@app.route('/register', methods=['POST'])
def register():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('auth'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists', 'error')
        return redirect(url_for('auth'))
    
    hashed_password = generate_password_hash(password)
    new_user = User(
        full_name=full_name,
        email=email,
        password=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('auth'))

@app.route('/todo')
def todo():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    todos = Todo.query.filter_by(user_id=session['user_id']).order_by(Todo.created_at.desc()).all()
    return render_template('todo.html', todos=todos)

@app.route('/add_todo', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    
    new_todo = Todo(
        title=title,
        description=description,
        user_id=session['user_id']
    )
    
    db.session.add(new_todo)
    db.session.commit()
    
    flash('Todo added successfully!', 'success')
    return redirect(url_for('todo'))

@app.route('/update_todo/<int:todo_id>', methods=['POST'])
def update_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    todo = Todo.query.filter_by(id=todo_id, user_id=session['user_id']).first()
    if todo:
        todo.completed = not todo.completed
        db.session.commit()
        flash('Todo updated successfully!', 'success')
    
    return redirect(url_for('todo'))

@app.route('/delete_todo/<int:todo_id>')
def delete_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    todo = Todo.query.filter_by(id=todo_id, user_id=session['user_id']).first()
    if todo:
        db.session.delete(todo)
        db.session.commit()
        flash('Todo deleted successfully!', 'success')
    
    return redirect(url_for('todo'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('auth'))

if __name__ == '__main__':
    app.run(debug=True)