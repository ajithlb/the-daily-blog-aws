import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import boto3
except ImportError:
    boto3 = None

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'blog.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'change-this-before-deployment')


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(author_id) REFERENCES users(id)
        )''')
        count = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        if count == 0:
            # Optional starter content, visible on first run.
            conn.execute('''INSERT OR IGNORE INTO users(username,email,password_hash,created_at)
                VALUES(?,?,?,?)''', ('demo', 'demo@example.com', generate_password_hash('DemoPassword123!'), datetime.utcnow().isoformat()))
            user = conn.execute('SELECT id FROM users WHERE username=?', ('demo',)).fetchone()
            conn.execute('''INSERT INTO posts(title,summary,content,author_id,created_at) VALUES(?,?,?,?,?)''',
                ('Getting Started with Flask', 'A quick introduction to building a small blog with Flask.',
                 'This is a sample article. Create an account to publish your own posts. Replace this sample content before using the site publicly.',
                 user['id'], datetime.utcnow().isoformat()))


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'info')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def notify_new_post(title, summary):
    """Publish an SNS notification when SNS_TOPIC_ARN is configured."""
    topic_arn = os.environ.get('SNS_TOPIC_ARN')
    region = os.environ.get('AWS_REGION', 'ap-south-1')
    if not topic_arn or boto3 is None:
        return
    try:
        boto3.client('sns', region_name=region).publish(
            TopicArn=topic_arn,
            Subject=f'New blog post: {title[:100]}',
            Message=f'{title}\n\n{summary}'
        )
    except Exception as exc:
        # A notification failure should not prevent publishing the post.
        app.logger.warning('SNS notification failed: %s', exc)


@app.route('/')
def index():
    with db() as conn:
        posts = conn.execute('''SELECT posts.*, users.username FROM posts
            JOIN users ON users.id=posts.author_id ORDER BY posts.id DESC''').fetchall()
    return render_template('index.html', posts=posts)


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    with db() as conn:
        post = conn.execute('''SELECT posts.*, users.username FROM posts
            JOIN users ON users.id=posts.author_id WHERE posts.id=?''', (post_id,)).fetchone()
    if post is None:
        abort(404)
    return render_template('post.html', post=post)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not username or not email or len(password) < 8:
            flash('Enter a username, valid email, and password with at least 8 characters.', 'error')
            return render_template('register.html')
        try:
            with db() as conn:
                conn.execute('INSERT INTO users(username,email,password_hash,created_at) VALUES(?,?,?,?)',
                    (username, email, generate_password_hash(password), datetime.utcnow().isoformat()))
            flash('Account created. You can now log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('That username or email is already registered.', 'error')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identity = request.form.get('identity', '').strip().lower()
        password = request.form.get('password', '')
        with db() as conn:
            user = conn.execute('SELECT * FROM users WHERE lower(username)=? OR lower(email)=?', (identity, identity)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome back, {user['username']}!", 'success')
            return redirect(url_for('index'))
        flash('Invalid username/email or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not summary or not content:
            flash('Please complete every field.', 'error')
            return render_template('create.html')
        with db() as conn:
            conn.execute('INSERT INTO posts(title,summary,content,author_id,created_at) VALUES(?,?,?,?,?)',
                (title, summary, content, session['user_id'], datetime.utcnow().isoformat()))
        notify_new_post(title, summary)
        flash('Your post has been published.', 'success')
        return redirect(url_for('index'))
    return render_template('create.html')


@app.errorhandler(404)
def not_found(_error):
    return render_template('404.html'), 404


with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=os.environ.get('FLASK_DEBUG') == '1')
