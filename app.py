import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'super_secret_antigravity_key'
DATABASE = 'roms.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            db.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            role TEXT NOT NULL
                        )''')
            # title, publisher, developer, genre, release_year, file_size_gb, min_requirements, image_url
            db.execute('''CREATE TABLE IF NOT EXISTS games (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            publisher TEXT,
                            developer TEXT,
                            genre TEXT,
                            release_year INTEGER,
                            file_size_gb REAL,
                            min_requirements TEXT,
                            image_url TEXT
                        )''')
            # Insert default admin and user
            db.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")
            db.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('user', 'user', 'user')")
            
            # Insert some sample games
            db.execute("""INSERT INTO games (title, publisher, developer, genre, release_year, file_size_gb, min_requirements, image_url) 
                          VALUES ('Pokemon FireRed', 'Nintendo', 'Game Freak', 'RPG', 2004, 0.016, 'Any GBA Emulator', 'https://upload.wikimedia.org/wikipedia/en/thumb/d/df/Pokémon_FireRed_boxart.jpg/220px-Pokémon_FireRed_boxart.jpg')""")
            db.execute("""INSERT INTO games (title, publisher, developer, genre, release_year, file_size_gb, min_requirements, image_url) 
                          VALUES ('The Legend of Zelda: The Minish Cap', 'Nintendo', 'Capcom', 'Action-Adventure', 2004, 0.016, 'Any GBA Emulator', 'https://upload.wikimedia.org/wikipedia/en/thumb/a/a5/The_Legend_of_Zelda_The_Minish_Cap_Game_Boy_Advance_Box_Art.png/220px-The_Legend_of_Zelda_The_Minish_Cap_Game_Boy_Advance_Box_Art.png')""")
            
            db.commit()
    else:
        # In case DB exists but games table doesn't (from previous session)
        with app.app_context():
            db = get_db()
            db.execute('''CREATE TABLE IF NOT EXISTS games (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            publisher TEXT,
                            developer TEXT,
                            genre TEXT,
                            release_year INTEGER,
                            file_size_gb REAL,
                            min_requirements TEXT,
                            image_url TEXT
                        )''')
            db.commit()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    q = request.args.get('q', '')
    
    db = get_db()
    if q:
        games = db.execute('SELECT * FROM games WHERE title LIKE ?', ('%' + q + '%',)).fetchall()
    else:
        games = db.execute('SELECT * FROM games').fetchall()
        
    return render_template('index.html', games=games, role=session.get('role'), q=q)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('manage'))
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/credits')
def credits():
    return render_template('credits.html')

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    db = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            title = request.form['title']
            publisher = request.form.get('publisher', '')
            developer = request.form.get('developer', '')
            genre = request.form.get('genre', '')
            release_year = request.form.get('release_year', None)
            file_size_gb = request.form.get('file_size_gb', 0)
            min_requirements = request.form.get('min_requirements', '')
            image_url = request.form.get('image_url', '')
            
            db.execute('''INSERT INTO games 
                          (title, publisher, developer, genre, release_year, file_size_gb, min_requirements, image_url) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (title, publisher, developer, genre, release_year, file_size_gb, min_requirements, image_url))
            db.commit()
            flash('Game added successfully!', 'success')
            
        elif action == 'delete':
            game_id = request.form.get('id')
            db.execute('DELETE FROM games WHERE id = ?', (game_id,))
            db.commit()
            flash('Game deleted successfully!', 'success')
            
        elif action == 'edit':
            game_id = request.form.get('id')
            title = request.form['title']
            publisher = request.form.get('publisher', '')
            developer = request.form.get('developer', '')
            genre = request.form.get('genre', '')
            release_year = request.form.get('release_year', None)
            file_size_gb = request.form.get('file_size_gb', 0)
            min_requirements = request.form.get('min_requirements', '')
            image_url = request.form.get('image_url', '')
            
            db.execute('''UPDATE games SET 
                          title = ?, publisher = ?, developer = ?, genre = ?, 
                          release_year = ?, file_size_gb = ?, min_requirements = ?, image_url = ? 
                          WHERE id = ?''', 
                       (title, publisher, developer, genre, release_year, file_size_gb, min_requirements, image_url, game_id))
            db.commit()
            flash('Game updated successfully!', 'success')
            
        return redirect(url_for('manage'))
        
    games = db.execute('SELECT * FROM games').fetchall()
    return render_template('manage.html', games=games, role=session.get('role'))

if __name__ == '__main__':
    # Initialize the database on first run
    init_db()
    
    # Ensure templates directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    
    # Run the application
    app.run()

# debug=True, port=5000