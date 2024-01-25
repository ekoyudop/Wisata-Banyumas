import os
from os.path import join, dirname
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, jsonify
from pymongo import MongoClient
import jwt
import datetime
import hashlib
from werkzeug.utils import secure_filename
from bson import ObjectId

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)

SECRET_KEY = "WISATA"

@app.route('/', methods=['GET'])
def halaman_login():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        return redirect(url_for('home'))
    except jwt.ExpiredSignatureError:
        msg = request.args.get('msg')
        return render_template('login.html', msg =msg)
    except jwt.exceptions.DecodeError:
        msg = request.args.get('msg')
        return render_template('login.html', msg =msg)
    
@app.route('/halaman_signup', methods=['GET'])
def halaman_signup():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        return redirect(url_for('home'))
    except jwt.ExpiredSignatureError:
        msg = request.args.get('msg')
        return render_template('signup.html', msg =msg)
    except jwt.exceptions.DecodeError:
        msg = request.args.get('msg')
        return render_template('signup.html', msg =msg)

@app.route('/home', methods=['GET'])
def home():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({'useremail' :payload.get('useremail')})
        user_role = user_info['role']
        wisata_terbaru = db.wisata.find()
        wisata_populer = db.wisata.find()
        wisata_terlama = db.wisata.find()

        return render_template('index.html', user_role = user_role, wisata_terbaru = wisata_terbaru, wisata_populer=wisata_populer, wisata_terlama=wisata_terlama)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
        return redirect(url_for('halaman_login',msg = msg))
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
        return redirect(url_for('halaman_login',msg = msg))
    
@app.route('/search', methods=['GET'])
def search():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({'useremail' :payload.get('useremail')})
        user_role = user_info['role']

        keyword = request.args.get('keyword')

        wisata_terbaru = list(db.wisata.find({'nama_wisata': {'$regex': keyword, '$options': 'i'}}))
        wisata_populer = list(db.wisata.find({'nama_wisata': {'$regex': keyword, '$options': 'i'}}))
        wisata_terlama = list(db.wisata.find({'nama_wisata': {'$regex': keyword, '$options': 'i'}}))

        return render_template('search_results.html', user_role=user_role, wisata_terbaru=wisata_terbaru, wisata_populer=wisata_populer, wisata_terlama=wisata_terlama, keyword=keyword)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
        return redirect(url_for('halaman_login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
        return redirect(url_for('halaman_login', msg=msg))

@app.route('/detail/<id_wisata>', methods=['GET'])
def detail_wisata(id_wisata):
    token_receive = request.cookies.get("mytoken")
    from datetime import datetime
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )

        user_info = db.users.find_one({'useremail' : payload.get('useremail')})

        info_wisata = db.wisata.find_one({'_id' : ObjectId(id_wisata)})
        komentar_wisata = list(db.komentar.find({'id_wisata' : id_wisata}))
        komentar_wisata.sort(key=lambda x: datetime.strptime(x['tanggal'], '%d/%m/%Y-%H:%M:%S'))
        for komentar in komentar_wisata:
            komentar['tanggal'] = komentar['tanggal'].replace('-', ' ')
        jumlah_komentar = len(komentar_wisata)
        
        like_cek = bool(db.likes.find_one({
            'id_wisata' : id_wisata,
            'useremail' : payload.get('useremail')            
        }))
        like_cek= str(like_cek)
        return render_template('detail.html', 
                               info_wisata=info_wisata, 
                               komentar_wisata=komentar_wisata, 
                               jumlah_komentar=jumlah_komentar, 
                               like_cek=like_cek,
                               user_info=user_info)

    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/admin', methods=['GET'])
def admin():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({'useremail' : payload.get('useremail')})            
            role = user_info.get("role")

        else:
            user_info = None
           
        if role not in ["admin"]:
            return redirect(url_for("home"))
        
        list_wisata = db.wisata.find()
        list_komentar = db.komentar.find()
        list_likes = db.likes.find()
        list_users = db.users.find()

        return render_template('admin.html', list_wisata = list_wisata, list_komentar=list_komentar, list_likes=list_likes, list_users=list_users)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
        return redirect(url_for('halaman_login',msg = msg))
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
        return redirect(url_for('halaman_login',msg = msg))
    
@app.route('/halaman_tambah', methods=['GET'])
def halaman_tambah():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({'useremail' : payload.get('useremail')})            
            role = user_info.get("role")

        else:
            user_info = None
           
        if role not in ["admin"]:
            return redirect(url_for("home"))
        
        return render_template('tambah.html')
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/halaman_edit/<id_wisata>', methods=['GET'])
def halaman_edit(id_wisata):
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({'useremail' : payload.get('useremail')})            
            role = user_info.get("role")

        else:
            user_info = None
           
        if role not in ["admin"]:
            return redirect(url_for("home"))
        
        info_wisata = db.wisata.find_one({'_id' : ObjectId(id_wisata)})
        return render_template('edit.html', info_wisata=info_wisata)
    
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))

@app.route('/sign_up/check_email', methods=['POST'])
def check_dup():
    useremail_receive = request.form['useremail_give']
    username_receive = request.form['username_give']

    exists = bool(db.users.find_one({"$or": [{"useremail": useremail_receive}, {"username": username_receive}]}))
    return jsonify({'result': 'success', 'exists': exists})

@app.route("/sign_up/save", methods=["POST"])
def sign_up():
    useremail_receive = request.form['useremail_give']
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "useremail" : useremail_receive,
        "username"  : username_receive,
        "password"  : password_hash,
        "role"      : "user"
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route("/sign_in", methods=["POST"])
def sign_in():
    useremail_receive = request.form["useremail_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.users.find_one(
        {
            "useremail": useremail_receive,
            "password": pw_hash,
        }
    )
    if result:
        payload = {
            "useremail": useremail_receive,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=60*60*24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify({"result": "success","token": token,})
    else:
        return jsonify({"result": "fail","msg": "Email atau Password anda tidak sesuai"})
    
@app.route('/users/<users_id>', methods=['DELETE'])
def delete_users(users_id):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )

        user = db.users.find_one({'_id': ObjectId(users_id)})
        useremail = user["useremail"]

        likes_cursor = db.likes.find({'useremail': useremail})
        for like in likes_cursor:
            likes_idwisata = like["id_wisata"]

            db.wisata.update_one({'_id': ObjectId(likes_idwisata)}, {'$inc': {'like_counts': -1}})

        db.users.delete_one({'_id': ObjectId(users_id)})
        db.komentar.delete_many({'useremail': useremail})
        db.likes.delete_many({'useremail': useremail})

        return jsonify({'result': 'success', 'msg': 'Berhasil menghapus users'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/tambah_wisata', methods=['POST'])
def posting():
    from datetime import datetime
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )

        name_receive = request.form.get('name_give')
        lokasi_receive = request.form.get('lokasi_give')
        gmaps_receive = request.form.get('gmaps_give')
        iframe_receive = request.form.get('iframe_give')
        deskripsi_receive = request.form.get('deskripsi_give')

        today = datetime.now()
        mytime = today.strftime("%Y-%m-%d-%H-%M-%S")

        if 'file_give' in request.files:
            file = request.files.get('file_give')
            file_name = secure_filename(file.filename)
            picture_name= file_name.split(".")[0]
            ekstensi = file_name.split(".")[1]
            picture_name = f"{picture_name}[{name_receive}]-{mytime}.{ekstensi}"
            file_path = f'./static/wisata_pics/{picture_name}'
            file.save(file_path)
        else: picture_name =f"default.jpg"

        doc = {
            'nama_wisata' : name_receive,
            'lokasi_wisata' : lokasi_receive,
            'gambar_wisata' : picture_name,
            'link_gmaps' : gmaps_receive,
            'link_iframe' : iframe_receive,
            'deskripsi' : deskripsi_receive,
            'like_counts' : 0
        }
        db.wisata.insert_one(doc)
        return jsonify({
            'result' : 'success',
            'msg' : 'Konten baru telah ditambahkan!'
        })
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/edit_wisata/<id_wisata>', methods=['PUT'])
def edit(id_wisata):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )

        name_receive = request.form.get('name_give')
        lokasi_receive = request.form.get('lokasi_give')
        gmaps_receive = request.form.get('gmaps_give')
        iframe_receive = request.form.get('iframe_give')
        deskripsi_receive = request.form.get('deskripsi_give')

        if 'file_give' in request.files:
            data_lama = db.wisata.find_one({'_id' : ObjectId(id_wisata)})
            gambar_lama = data_lama['gambar_wisata']
            if gambar_lama != "default.jpg" :
                os.remove(f'./static/wisata_pics/{gambar_lama}')

            file = request.files.get('file_give')
            file_name = secure_filename(file.filename)
            picture_name= file_name.split(".")[0]
            ekstensi = file_name.split(".")[1]
            picture_name = f"{picture_name}[{name_receive}].{ekstensi}"
            file_path = f'./static/wisata_pics/{picture_name}'
            file.save(file_path)

            doc = {
                'nama_wisata' : name_receive,
                'lokasi_wisata' : lokasi_receive,
                'gambar_wisata' : picture_name,
                'link_gmaps' : gmaps_receive,
                'link_iframe' : iframe_receive,
                'deskripsi' : deskripsi_receive,
            }

        else :
            doc = {
                'nama_wisata' : name_receive,
                'lokasi_wisata' : lokasi_receive,
                'link_gmaps' : gmaps_receive,
                'link_iframe' : iframe_receive,
                'deskripsi' : deskripsi_receive,
            }
        db.wisata.update_one({'_id' : ObjectId(id_wisata)},{'$set': doc})
        return jsonify({
            'result' : 'success',
            'msg' : 'Data berhasil diedit'
        })
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/delete_wisata/<string:id_wisata>', methods=['DELETE'])
def delete_wisata(id_wisata):
    token_receive = request.cookies.get("mytoken")

    try:
        info_wisata = db.wisata.find_one({'_id' : ObjectId(id_wisata)})
        gambar_wisata = info_wisata['gambar_wisata']
        if gambar_wisata != "default.jpg":
            os.remove(f'./static/wisata_pics/{gambar_wisata}')

        db.wisata.delete_one({'_id': ObjectId(id_wisata)})
        db.likes.delete_many({'id_wisata': id_wisata})
        db.komentar.delete_many({'id_wisata': id_wisata})
        return jsonify({ 'result' : 'success' , 'msg' : 'Data wisata berhasil dihapus'})

    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/komentar', methods=['POST'])
def tambah_komentar():
    token_receive = request.cookies.get("mytoken")
    from datetime import datetime
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({'useremail' : payload.get('useremail')})

        id_wisata = request.form.get('id_wisata_give')
        useremail = user_info['useremail']
        username = user_info['username']
        komentar_receive = request.form.get('komentar_give')

        doc = {
            'id_wisata' : id_wisata,
            'useremail' : useremail,
            'username' : username,
            'komentar': komentar_receive,
            'tanggal' : datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
        }
        db.komentar.insert_one(doc)
        return jsonify({ 'result' : 'success' , 'msg' : 'Berhasil menambahkan komentar'})

    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/komentar/<komentar_id>', methods=['PUT'])
def update_komentar(komentar_id):
    token_receive = request.cookies.get("mytoken")
    from datetime import datetime
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )

        updated_komentar = request.form.get('updated_komentar')
        db.komentar.update_one(
            {'_id': ObjectId(komentar_id)},
            {'$set': {'komentar': updated_komentar, 'tanggal': datetime.now().strftime('%d/%m/%Y-%H:%M:%S')}}
        )

        return jsonify({'result': 'success', 'msg': 'Berhasil memperbarui komentar'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/komentar/<komentar_id>', methods=['DELETE'])
def delete_komentar(komentar_id):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )

        db.komentar.delete_one({'_id': ObjectId(komentar_id)})

        return jsonify({'result': 'success', 'msg': 'Berhasil menghapus komentar'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/update_like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({'useremail' : payload.get('useremail')})
        id_wisata = request.form.get('id_wisata_give')
        action_receive = request.form.get('action_give')
        doc = {
            'id_wisata' : id_wisata,
            'useremail' : user_info.get('useremail')
        }

        doc2 = {
            '$inc': {'like_counts': 1}
        }
        doc3 = {
            '$inc': {'like_counts': -1}
        }
        if action_receive == 'like' :
            db.likes.insert_one(doc)
            db.wisata.update_one({'_id': ObjectId(id_wisata)}, doc2)
        else : 
            db.likes.delete_one(doc)
            db.wisata.update_one({'_id': ObjectId(id_wisata)}, doc3)

        return jsonify({
            'result' : 'success',
            'msg' : 'Updated!',
        })
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/likes/<likes_id>', methods=['DELETE'])
def delete_likes(likes_id):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )

        doc = {
            '$inc': {'like_counts': -1}
        }

        likes = db.likes.find_one({'_id': ObjectId(likes_id)})
        likes_idwisata = likes["id_wisata"]

        db.likes.delete_one({'_id': ObjectId(likes_id)})
        db.wisata.update_one({'_id': ObjectId(likes_idwisata)}, doc)

        return jsonify({'result': 'success', 'msg': 'Berhasil menghapus likes'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))
    
@app.route('/api/users', methods=['POST'])
def post_users_api():
    from datetime import datetime
    try:
        useremail = request.form.get('useremail')
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        existing_user_email = db.users.find_one({'useremail': useremail})
        existing_user_username = db.users.find_one({'username': username})

        if existing_user_email and existing_user_username:
            return jsonify({
                'result': 'error',
                'msg': 'Email and username are already in use!'
            })
        elif existing_user_email:
            return jsonify({
                'result': 'error',
                'msg': 'Email is already in use!'
            })
        elif existing_user_username:
            return jsonify({
                'result': 'error',
                'msg': 'Username is already in use!'
            })


        doc = {
            'useremail': useremail,
            'username': username,
            'password': password_hash,
            'role': "user"
        }

        result = db.users.insert_one(doc)

        return jsonify({
            'result': 'success',
            'msg': 'Users added successfully!'
        })

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/wisata', methods=['POST'])
def post_wisata_api():
    from datetime import datetime
    try:
        name = request.form.get('name')
        lokasi = request.form.get('lokasi')
        gmaps = request.form.get('gmaps')
        iframe = request.form.get('iframe')
        deskripsi = request.form.get('deskripsi')

        today = datetime.now()
        mytime = today.strftime("%Y-%m-%d-%H-%M-%S")

        if 'file_give' in request.files:
            file = request.files.get('file_give')
            file_name = secure_filename(file.filename)
            picture_name = file_name.split(".")[0]
            ekstensi = file_name.split(".")[1]
            picture_name = f"{picture_name}[{name}]-{mytime}.{ekstensi}"
            file_path = f'./static/wisata_pics/{picture_name}'
            file.save(file_path)
        else:
            picture_name = f"default.jpg"

        doc = {
            'nama_wisata': name,
            'lokasi_wisata': lokasi,
            'gambar_wisata': picture_name,
            'link_gmaps': gmaps,
            'link_iframe': iframe,
            'deskripsi': deskripsi,
            'like_counts': 0
        }

        result = db.wisata.insert_one(doc)

        return jsonify({
            'result': 'success',
            'msg': 'Wisata added successfully!'
        })

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/likes', methods=['POST'])
def post_likes_api():
    try:
        id_wisata = request.form.get('id_wisata')
        useremail = request.form.get('useremail')

        doc = {
            'id_wisata': id_wisata,
            'useremail': useremail,
        }

        doc2 = {
            '$inc': {'like_counts': 1}
        }

        db.likes.insert_one(doc)
        db.wisata.update_one({'_id': ObjectId(id_wisata)}, doc2)

        return jsonify({
            'result': 'success',
            'msg': 'Like added successfully!'
        })

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/komentar', methods=['POST'])
def post_komentar_api():
    from datetime import datetime
    try:
        id_wisata = request.form.get('id_wisata')
        useremail = request.form.get('useremail')
        username = request.form.get('username')
        komentar = request.form.get('komentar')

        comment_doc = {
            'id_wisata': id_wisata,
            'useremail': useremail,
            'username': username,
            'komentar': komentar,
            'tanggal': datetime.now().strftime('%d/%m/%Y-%H:%M:%S'),
        }

        result = db.komentar.insert_one(comment_doc)

        return jsonify({
            'result': 'success',
            'msg': 'Comment added successfully!'
        })

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/users', methods=['GET'])
def get_users_api():
    try:
        users_collection = db.users
        result = []
        for users in users_collection.find():
            result.append({
                '_id': str(users['_id']),
                'useremail': users['useremail'],
                'username': users['username'],
                'password': users['password']
            })
        return jsonify({'data': result})

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/wisata', methods=['GET'])
def get_wisata_api():
    try:
        wisata_collection = db.wisata
        result = []
        for wisata in wisata_collection.find():
            result.append({
                '_id': str(wisata['_id']),
                'nama_wisata': wisata['nama_wisata'],
                'lokasi_wisata': wisata['lokasi_wisata'],
                'gambar_wisata': wisata['gambar_wisata'],
                'link_gmaps': wisata['link_gmaps'],
                'link_iframe': wisata['link_iframe'],
                'deskripsi': wisata['deskripsi'],
                'like_counts': wisata['like_counts']
            })
        return jsonify({'data': result})

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/likes', methods=['GET'])
def get_likes_api():
    try:
        likes_collection = db.likes
        result = []
        for likes in likes_collection.find():
            result.append({
                '_id': str(likes['_id']),
                'id_wisata': likes['id_wisata'],
                'useremail': likes['useremail'],
            })
        return jsonify({'data': result})

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/komentar', methods=['GET'])
def get_komentar_api():
    try:
        komentar_collection = db.komentar
        result = []
        for komentar in komentar_collection.find():
            result.append({
                '_id': str(komentar['_id']),
                'id_wisata': komentar['id_wisata'],
                'useremail': komentar['useremail'],
                'username': komentar['username'],
                'komentar': komentar['komentar'],
                'tanggal': komentar['tanggal'],
            })
        return jsonify({'data': result})

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/users', methods=['PUT'])
def put_users_api():
    try:
        useremail = request.form.get('useremail')
        username = request.form.get('username')
        password = request.form.get('password')
        new_useremail = request.form.get('new_useremail')
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')

        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest() if new_password else None

        # Check if the user with the given email or username exists
        existing_user = db.users.find_one({'$or': [{'useremail': useremail}, {'username': username}, {'password': password_hash}]})

        if not existing_user:
            return jsonify({
                'result': 'error',
                'msg': 'User not found!'
            })
        
        existing_user_email = db.users.find_one({'useremail': new_useremail})
        existing_user_username = db.users.find_one({'username': new_username})

        if existing_user_email and existing_user_username:
            return jsonify({
                'result': 'error',
                'msg': 'Email and username are already in use!'
            })
        elif existing_user_email:
            return jsonify({
                'result': 'error',
                'msg': 'Email is already in use!'
            })
        elif existing_user_username:
            return jsonify({
                'result': 'error',
                'msg': 'Username is already in use!'
            })

        # Update user information
        update_data = {
            'useremail': new_useremail if new_useremail else existing_user['useremail'],
            'username': new_username if new_username else existing_user['username'],
            'password': new_password_hash if new_password else existing_user['password']
        }

        db.users.update_one({'$or': [{'useremail': useremail}, {'username': username}, {'password': password_hash}]}, {'$set': update_data})
        db.komentar.update_many({'$or': [{'useremail': useremail}, {'username': username}]}, 
                                {'$set': {'useremail' : new_useremail if new_useremail else existing_user['useremail'], 'username' : new_username if new_username else existing_user['username']}})
        db.likes.update_many({'useremail': useremail}, 
                            {'$set': {'useremail': new_useremail if new_useremail else existing_user['useremail']}})

        return jsonify({
            'result': 'success',
            'msg': 'User updated successfully!'
        })

    except Exception as e:
        return jsonify({'result': 'error', 'msg': str(e)})
    
@app.route('/api/wisata/<wisata_id>', methods=['PUT'])
def put_wisata_api(wisata_id):
    try:
        from datetime import datetime
        from bson import ObjectId

        info_wisata = db.wisata.find_one({'_id': ObjectId(wisata_id)})
        gambar_wisata = info_wisata['gambar_wisata']
        
        # Check if the image is not the default one, then delete it
        if gambar_wisata != "default.jpg":
            os.remove(f'./static/wisata_pics/{gambar_wisata}')
        
        name = request.form.get('name')
        lokasi = request.form.get('lokasi')
        gmaps = request.form.get('gmaps')
        iframe = request.form.get('iframe')
        deskripsi = request.form.get('deskripsi')

        if 'file_give' in request.files:
            file = request.files.get('file_give')
            file_name = secure_filename(file.filename)
            picture_name = file_name.split(".")[0]
            ekstensi = file_name.split(".")[1]
            today = datetime.now()
            mytime = today.strftime("%Y-%m-%d-%H-%M-%S")
            picture_name = f"{picture_name}[{name}]-{mytime}.{ekstensi}"
            file_path = f'./static/wisata_pics/{picture_name}'
            file.save(file_path)
        else:
            picture_name = f"default.jpg"

        doc = {
            'nama_wisata': name,
            'lokasi_wisata': lokasi,
            'gambar_wisata': picture_name,
            'link_gmaps': gmaps,
            'link_iframe': iframe,
            'deskripsi': deskripsi,
        }

        result = db.wisata.update_one(
            {'_id': ObjectId(wisata_id)},
            {'$set': doc}
        )

        if result.modified_count > 0:
            return jsonify({
                'result': 'success',
                'msg': 'Wisata updated successfully!'
            })
        else:
            return jsonify({
                'result': 'failure',
                'msg': 'No records were updated. Wisata may not exist.'
            })

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/likes/<likes_id>', methods=['PUT'])
def put_like_api(likes_id):
    try:
        doc = {
            '$inc': {'like_counts': -1}
        }
        likes = db.likes.find_one({'_id': ObjectId(likes_id)})
        likes_idwisata = likes["id_wisata"]
        db.wisata.update_one({'_id': ObjectId(likes_idwisata)}, doc)

        id_wisata = request.form.get('id_wisata')
        useremail = request.form.get('useremail')
        doc2 = {
            'id_wisata': id_wisata,
            'useremail': useremail,
        }
        db.likes.update_one(
            {'_id': ObjectId(likes_id)},
            {'$set': doc2}
        )

        doc3 = {
            '$inc': {'like_counts': 1}
        }
        likes2 = db.likes.find_one({'_id': ObjectId(likes_id)})
        likes_idwisata2 = likes2["id_wisata"]
        db.wisata.update_one({'_id': ObjectId(likes_idwisata2)}, doc3)

        

        return jsonify({
            'result': 'success',
            'msg': 'Like updated successfully!'
        })

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/api/komentar/<komentar_id>', methods=['PUT'])
def put_comment_api(komentar_id):
    from datetime import datetime
    try:
        komentar = request.form.get('komentar')

        doc = {
            'komentar': komentar,
            'tanggal': datetime.now().strftime('%d/%m/%Y-%H:%M:%S'),
        }

        result = db.komentar.update_one(
            {'_id': ObjectId(komentar_id)},
            {'$set': doc}
        )

        return jsonify({
            'result': 'success',
            'msg': 'Comment updated successfully!'
        })

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/users/<string:id>', methods=['DELETE'])
def delete_users_api(id):
    try:
        users = db.users.find_one({'_id': ObjectId(id)})
        users_email = users["useremail"]

        likes_cursor = db.likes.find({'useremail': users_email})
        for like in likes_cursor:
            likes_idwisata = like["id_wisata"]

            db.wisata.update_one({'_id': ObjectId(likes_idwisata)}, {'$inc': {'like_counts': -1}})

        result_users = db.users.delete_one({'_id': ObjectId(id)})
        db.likes.delete_many({'useremail': users_email})
        db.komentar.delete_many({'useremail': users_email})

        if result_users.deleted_count > 0:
            return jsonify({'message': 'Users deleted successfully'})
        else:
            return jsonify({'message': 'Users not found'})

    except Exception as e:
        return jsonify({'error': str(e)})
      
@app.route('/api/wisata/<string:id>', methods=['DELETE'])
def delete_wisata_api(id):
    try:
        info_wisata = db.wisata.find_one({'_id': ObjectId(id)})
        gambar_wisata = info_wisata['gambar_wisata']
        
        # Check if the image is not the default one, then delete it
        if gambar_wisata != "default.jpg":
            os.remove(f'./static/wisata_pics/{gambar_wisata}')

        wisata_collection = db.wisata
        likes_collection = db.likes
        komentar_collection = db.komentar

        result_wisata = wisata_collection.delete_one({'_id': ObjectId(id)})
        result_likes = likes_collection.delete_many({'id_wisata': id})
        result_komentar = komentar_collection.delete_many({'id_wisata': id})

        if result_wisata.deleted_count > 0:
            return jsonify({'message': 'Wisata deleted successfully'})
        else:
            return jsonify({'message': 'Wisata not found'})

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/likes/<string:id>', methods=['DELETE'])
def delete_likes_api(id):
    try:
        doc = {
            '$inc': {'like_counts': -1}
        }

        likes = db.likes.find_one({'_id': ObjectId(id)})
        likes_idwisata = likes["id_wisata"]

        result = db.likes.delete_one({'_id': ObjectId(id)})
        db.wisata.update_one({'_id': ObjectId(likes_idwisata)}, doc)
        if result.deleted_count > 0:
            return jsonify({'message': 'Like entry deleted successfully'})
        else:
            return jsonify({'message': 'Like entry not found'})

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/komentar/<string:id>', methods=['DELETE'])
def delete_komentar_api(id):
    try:
        komentar_collection = db.komentar
        result = komentar_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return jsonify({'message': 'Komentar deleted successfully'})
        else:
            return jsonify({'message': 'Komentar not found'})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)