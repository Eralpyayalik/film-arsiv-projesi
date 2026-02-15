import MySQLdb
import requests
from flask import Flask, flash, redirect, render_template, session, request, url_for
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, FileField, SubmitField
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
from functools import wraps
from flask_caching import Cache
import time
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

API_KEY = os.getenv("TMDB_API_KEY")
app.secret_key = os.getenv("FLASK_SECRET_KEY")
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else: 
            flash("Bu sayfayı görüntülemek için giriş yapın...","danger")
        return redirect(url_for("login"))
    return decorated_function

class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.length(min=4,max=25)])
    username=StringField("Kullanıcı Adı",validators=[validators.length(min=4, max=35)])
    email=StringField("Email Adresi",validators=[validators.Email(message="LÜtfen Geçerli bir mail girin.")])

    password=PasswordField("Parola:",validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin."),
        validators.EqualTo(fieldname="confirm",message="Paraoli Uyuşmuyor...")
    ])
    confirm=PasswordField("parola Doğrula")

class LoginForm(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola")


app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 26850)) 

mysql = MySQL(app)


@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method=="POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()  

        sorgu="Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla Kayıt oldunuz.","success")
        return redirect(url_for("login")) 
    else:
        return render_template("register.html",form=form)
    
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method=="POST":
        username=form.username.data
        password_entered=form.password.data

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        sorgu="Select * From users where username= %s"
        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data['password']
          
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız!", "success")
                session["logged_in"]=True
                session["username"]= username
                session["id"] = data["id"]
                return redirect(url_for("index"))
            else:
                flash("Şifre yanlış!", "danger")
        else:
            flash("Kullanıcı bulunamadı!", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))



@app.route('/')
def index():
     
    BASE_URL = "https://api.themoviedb.org/3"

    def fetch_movies(endpoint, params=""):
        url = f"{BASE_URL}/{endpoint}?api_key={API_KEY}&language=tr-TR{params}"
        try:
            response = requests.get(url, timeout=3) 
            return response.json().get('results', [])[:6]
        except:
            return []

    endpoints = [
        ("movie/popular", ""),
        ("movie/top_rated", ""),
        ("discover/movie", "&with_genres=28"),
        ("discover/movie", "&with_genres=27"),
        ("discover/movie", "&with_genres=18")
    ]

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda p: fetch_movies(p[0], p[1]), endpoints))

    return render_template('index.html', 
                           popular=results[0], 
                           top_rated=results[1], 
                           action=results[2], 
                           horror=results[3],
                           drama=results[4])

@app.route('/search')
def search():
    query = request.args.get('q') 
    if not query:
        return redirect(url_for('index'))
        
    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={query}&language=tr-TR"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        results = data.get('results', [])
        filtered_results = [m for m in results if m.get('poster_path')]
        user_fav_ids = []
        if "id" in session:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT movie_id FROM favorites WHERE user_id = %s", (session.get('id'),))
            user_fav_ids = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
        return render_template('search_results.html', movies=filtered_results, query=query, user_fav_ids=user_fav_ids)
    except:
        flash("Arama yapılırken bir hata oluştu.", "warning")
        return redirect(url_for('index'))

@app.route('/movies')
def all_movies():
    api_key = "dc73de6a9f1ff43ae6e806e739a26ca3"

    page = request.args.get('page', 1)
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=tr-TR&page={page}"
    response = requests.get(url).json()
    movies = response.get('results', [])
    user_fav_ids = []
    if "id" in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT movie_id FROM favorites WHERE user_id = %s", (session.get('id'),))
        user_fav_ids = [row[0] for row in cursor.fetchall()]
        cursor.close()
    
    return render_template('movies.html', movies=movies, current_page=int(page), user_fav_ids=user_fav_ids)
    

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=tr-TR"
    response = requests.get(url)
    movie = response.json() 

    user_id = session.get('id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor) #
    cursor.execute("SELECT * FROM comments WHERE movie_id = %s ORDER BY created_at DESC", (movie_id,))
    movie_comments = cursor.fetchall()
    

    existing_lists = []
    if user_id:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT DISTINCT list_name FROM user_lists WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        existing_lists = [row['list_name'] for row in rows] 
        cursor.close()
    
    return render_template('movie_detail.html', movie=movie, comments=movie_comments, existing_lists=existing_lists)


@app.route('/add_comment/<int:movie_id>', methods=['POST'])
@login_required
def add_comment(movie_id):

    comment_text = request.form.get('comment_text') 
    rating = request.form.get('rating', 5) 
    movie_title = request.form.get('movie_title') 
    movie_poster = request.form.get('movie_poster') 
    
    user_id = session.get('id') 
    username = session.get('username')

    if comment_text:
        cursor = mysql.connection.cursor()

        sorgu = """
            INSERT INTO comments (user_id, movie_id, username, comment_text, rating, movie_title, movie_poster) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sorgu, (user_id, movie_id, username, comment_text, rating, movie_title, movie_poster))
        
        mysql.connection.commit()
        cursor.close()
        flash("Yorumun başarıyla eklendi.", "success")
    else:
        flash("Yorum alanı boş bırakılamaz!", "danger")
    
 
    return redirect(url_for('movie_detail', movie_id=movie_id))
@app.route('/add_favorite/<int:movie_id>', methods=['POST'])
@login_required
def add_favorite(movie_id):
    user_id = session.get('id')
    movie_title = request.form.get('movie_title')
    movie_poster = request.form.get('movie_poster')

    
    if not movie_poster or movie_poster == "None":
        flash("Film verileri eksik, lütfen sayfayı yenileyip tekrar deneyin.", "danger")
        return redirect(request.referrer)

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM favorites WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
    exist = cursor.fetchone()

    if not exist:
        sorgu = "INSERT INTO favorites (user_id, movie_id, movie_title, movie_poster) VALUES (%s, %s, %s, %s)"
        cursor.execute(sorgu, (user_id, movie_id, movie_title, movie_poster))
        mysql.connection.commit()
        flash("Film kütüphanene eklendi!", "success")
    else:
        flash("Bu film zaten favorilerinde!", "info")

    cursor.close()
    return redirect(request.referrer)

@app.route('/favorites')
@login_required
def favorites():
    user_id = session.get('id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute("SELECT * FROM favorites WHERE user_id = %s", (user_id,))
    fav_movies = cursor.fetchall()
    
    cursor.execute("SELECT DISTINCT list_name FROM user_lists WHERE user_id = %s", (user_id,))
    existing_lists = [row['list_name'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM user_lists WHERE user_id = %s AND movie_id != 0", (user_id,))
    all_list_movies = cursor.fetchall() 
    
    cursor.close()
    
    return render_template('favorites.html', favorites=fav_movies, existing_lists=existing_lists, all_list_movies=all_list_movies)

@app.route('/delete_favorite/<int:fav_id>', methods=['POST'])
@login_required
def delete_favorite(fav_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM favorites WHERE id = %s AND user_id = %s", (fav_id, session.get('id')))
    mysql.connection.commit()
    cursor.close()
    flash("Film favorilerden kaldırıldı.", "info")
    return redirect(url_for('favorites'))


@app.route('/profile/<string:username>')
@login_required
def profile(username):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    sorgu = "SELECT * From users WHERE username=%s"
    result = cursor.execute(sorgu, (username,))
    
    if result == 0:
        flash("Böyle bir Kullanıcı yok!", "danger")
        return redirect(url_for("index"))
    
    user = cursor.fetchone()
    user_id = user['id'] 

    cursor.execute("SELECT * FROM favorites WHERE user_id = %s", (user_id,))
    favorites = cursor.fetchall()
    fav_count = len(favorites) 

    cursor.execute("SELECT * FROM comments WHERE user_id = %s", (user_id,))
    comments = cursor.fetchall()
    comment_count = len(comments)

    stats = {
        'fav': fav_count,
        'comment': comment_count,
        'avg': 0 
    }
    
    cursor.close()

    return render_template("profile.html", 
                           user=user, 
                           stats=stats, 
                           favorites=favorites, 
                           comments=comments)
@app.route('/add_to_list/<int:movie_id>', methods=['POST'])
@login_required
def add_to_list(movie_id):
    list_name = request.form.get('selected_list')
    title = request.form.get('title')
    poster = request.form.get('poster')
    user_id = session.get('id')

    cursor = mysql.connection.cursor()
    
    cursor.execute("SELECT * FROM user_lists WHERE user_id=%s AND list_name=%s AND movie_id=%s", 
                   (user_id, list_name, movie_id))
    exists = cursor.fetchone()

    if not exists:
        
        cursor.execute("INSERT INTO user_lists (user_id, list_name, movie_id, movie_title, movie_poster) VALUES (%s, %s, %s, %s, %s)", 
                       (user_id, list_name, movie_id, title, poster))
        mysql.connection.commit()
    
    cursor.close()
    flash(f'Film listeye eklendi!', 'info')
    return redirect(url_for('manage_list', list_name=list_name))

@app.route('/create_list', methods=['POST'])
@login_required
def create_list():
    list_name = request.form.get('list_name')
    user_id = session.get('id')
    if list_name:
        cursor = mysql.connection.cursor()

        cursor.execute("INSERT INTO user_lists (user_id, list_name, movie_id) VALUES (%s, %s, %s)", (user_id, list_name, 0))
        mysql.connection.commit()
        cursor.close()
    flash('Yeni liste başarıyla oluşturuldu!', 'success')
    return redirect(url_for('favorites'))

@app.route('/manage_list/<string:list_name>')
@login_required
def manage_list(list_name):
    user_id = session.get('id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute("SELECT * FROM user_lists WHERE user_id = %s AND list_name = %s AND movie_id != 0", (user_id, list_name))
    list_movies = cursor.fetchall()
    
    cursor.execute("SELECT * FROM favorites WHERE user_id = %s", (user_id,))
    fav_movies = cursor.fetchall()
    
    cursor.close()
    return render_template('manage_list.html', list_name=list_name, list_movies=list_movies, fav_movies=fav_movies)

@app.route('/remove_from_list/<int:list_id>', methods=['POST'])
@login_required
def remove_from_list(list_id):
    cursor = mysql.connection.cursor()

    cursor.execute("DELETE FROM user_lists WHERE id = %s", (list_id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(request.referrer or url_for('favorites'))

@app.route('/delete_list_entirely/<string:list_name>', methods=['POST'])
@login_required
def delete_list_entirely(list_name):
    user_id = session.get('id')
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM user_lists WHERE user_id = %s AND list_name = %s", (user_id, list_name))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('favorites'))

@app.route('/my-lists') 
@login_required
def user_lists_page(): 
    user_id = session.get('id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    

    cursor.execute("SELECT DISTINCT list_name FROM user_lists WHERE user_id = %s", (user_id,))
    existing_lists = [row['list_name'] for row in cursor.fetchall()]
    
    cursor.close()
    return render_template('lists.html', existing_lists=existing_lists)

@app.route('/view_list/<string:username>/<string:list_name>')
def view_list(username, list_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if user:
        cursor.execute("""
            SELECT * FROM user_lists 
            WHERE user_id = %s AND list_name = %s AND movie_id != 0
        """, (user['id'], list_name))
        list_movies = cursor.fetchall()
        cursor.close()
        return render_template('view_list.html', list_name=list_name, list_movies=list_movies, username=username)
    
    flash("Kullanıcı bulunamadı!", "danger")
    return redirect(url_for('users'))

@app.route('/users')
def users():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)


    cursor.execute("SELECT username, DATE_FORMAT(MIN(created_at), '%d.%m.%Y') as reg_date FROM users GROUP BY username ORDER BY MIN(created_at) DESC")
    all_users = cursor.fetchall()

    
    cursor.execute("""
    SELECT c.movie_title, c.movie_poster, c.comment_text as comment, u.username, 
           DATE_FORMAT(c.created_at, '%H:%i - %d.%m.%Y') as date, c.rating
    FROM comments c 
    JOIN users u ON c.user_id = u.id 
    ORDER BY c.created_at DESC LIMIT 5
    """)
    recent_reviews = cursor.fetchall()


    cursor.execute("""
        SELECT l.list_name, u.username, MAX(l.created_at) as last_added
        FROM user_lists l
        JOIN users u ON l.user_id = u.id
        GROUP BY l.list_name, u.username
        ORDER BY last_added DESC LIMIT 6
    """)
    recent_lists = cursor.fetchall()

    cursor.close()
    return render_template('users.html', 
                           all_users=all_users, 
                           recent_reviews=recent_reviews, 
                           recent_lists=recent_lists)
if __name__ == "__main__":
    app.run(debug=True)