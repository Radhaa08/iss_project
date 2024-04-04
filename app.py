from flask import Flask, render_template, send_file, request, redirect, url_for, flash, session, jsonify, send_from_directory
import mysql.connector
import os
import jwt
import tempfile
from moviepy.editor import ImageSequenceClip, concatenate_videoclips
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from PIL import Image
from moviepy.editor import AudioFileClip,VideoFileClip
from moviepy.editor import ImageClip
from datetime import datetime
import base64
import io
import psycopg2
import shutil

app = Flask(__name__)
app.secret_key = 'lalala'
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Update this path as needed
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['JWT_SECRET_KEY'] = 'lalala'
IMAGES_DIR = os.path.join(os.getcwd(), 'static','saved_images')
# MySQL database connection parameters
db_config = {
    'host': 'newcluster-8912.8nk.gcp-asia-southeast1.cockroachlabs.cloud',  # Change this if your MySQL database is hosted elsewhere
    'user': 'radha',
    'port': 26257, 
    'password': 'T-6zxK6IsKE61zXRI4-I3Q',
    'database': 'project',
    'sslmode':'verify-full',
    'sslrootcert':'root.crt'
}

# Function to connect to MySQL database
def connect_to_database():
    return psycopg2.connect(**db_config)
def generate_token(email):
    payload = {'email': email}
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
# Function to decode JWT token
def decode_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload['email']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'
def check_column_exists(column_name,table_name):
    conn = connect_to_database()
    cursor = conn.cursor()
    check_query = """
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    );
    """
    cursor.execute(check_query, (column_name,table_name))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

# Function to add the jwt_token column to the users table if it doesn't exist
def add_jwt_token_column():
    conn = connect_to_database()
    cursor = conn.cursor()
    alter_query = "ALTER TABLE users ADD COLUMN jwt_token VARCHAR(255)"
    try:
        cursor.execute(alter_query)
        conn.commit()
        print("jwt_token column added successfully")
    except mysql.connector.Error as err:
        print(f"Error adding jwt_token column: {err}")
    finally:
        cursor.close()
        conn.close()

def create_user_images_table():
    conn = connect_to_database()
    cursor = conn.cursor()
    create_query = """
   CREATE TABLE IF NOT EXISTS user_images (
        id SERIAL PRIMARY KEY,
        user_id INT,
        image BYTEA,
        format VARCHAR(10),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    cursor.execute(create_query)
    conn.commit()
    cursor.close()
    conn.close()
@app.route('/save_image', methods=['POST'])
def save_image():
    try:
        # Get image data URI from request
        image_data_uri = request.json['image']
        
        # Decode data URI (remove metadata prefix)
        _, encoded_data = image_data_uri.split(',', 1)
        image_data = base64.b64decode(encoded_data)

        # Create a BytesIO object to read the image data
        image_stream = BytesIO(image_data)

        # Open the image using PIL (Python Imaging Library)
        image = Image.open(image_stream)

        # Generate a unique filename or use some identifier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
        filename = f'image_{timestamp}.png'

        # Save the image file to the 'saved_images' folder
        save_folder = os.path.join('static', 'saved_images', filename)
        image.save(save_folder)

        print('Image saved:', filename)

        # Return success message to the client
        return jsonify({'message': 'Image saved successfully'}), 200

    except Exception as e:
        print('Error saving image:', e)
        # Return error message to the client
        return jsonify({'message': 'Error saving image'}), 500


def save_image_to_database(image_file, user_id):
    if image_file.content_length > 1024 * 1024:  # 1 MB limit
        return jsonify({'error': 'Image size too large'}), 400

    binary_data = io.BytesIO()
    try:
        image_file.save(binary_data)
        binary_data.seek(0)
        image_blob = binary_data.read()
    except Exception as e:
        return jsonify({'error': f'Error saving image: {str(e)}'}), 500

    image_format = image_file.filename.split('.')[-1]

    conn = connect_to_database()
    cursor = conn.cursor()

    insert_query = "INSERT INTO user_images (user_id, image, format) VALUES (%s, %s, %s)"
    try:
        cursor.execute(insert_query, (user_id, image_blob, image_format))
        conn.commit()
        return jsonify({'success': 'File uploaded successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Error uploading file to database: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/images', methods=['GET'])
def list_images():
    image_files = [f for f in os.listdir(IMAGES_DIR) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    image_urls = [f'/static/saved_images/{filename}' for filename in image_files]
    return jsonify(image_urls)

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

def fetch_user_images(user_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    create_user_images_table()
    select_query = "SELECT image,format FROM user_images WHERE user_id = %s"
    cursor.execute(select_query, (user_id,))
    images = cursor.fetchall()
    cursor.close()
    conn.close()
    return images

@app.route('/uploadimages')
def upload():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        user_id = session.get('id')
        save_image_to_database(file, user_id)
        return jsonify({'success': 'File uploaded successfully'}), 200

@app.route('/gallery')
def gallery():
    user_id = session.get('id')
    images = fetch_user_images(user_id)
    image_urls = []
    for image_data, image_format in images:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_url = f"data:image/{image_format};base64,{image_base64}"
        image_urls.append(image_url)
    return render_template('gallery.html', image_urls=image_urls)

@app.route('/user_images', methods=['GET'])
def fetch_user_images_p():
    user_id = session.get('id')
    if not user_id:
        return jsonify({'error': 'User ID not found in session'}), 400

    conn = connect_to_database()
    cursor = conn.cursor()
    select_query = "SELECT id, image, format FROM user_images WHERE user_id = %s"
    cursor.execute(select_query, (user_id,))
    images = cursor.fetchall()
    cursor.close()
    conn.close()

    response_data = [{'id': image[0], 'image': base64.b64encode(image[1]).decode('utf-8'), 'format': image[2]} for image in images]
    return jsonify({'images': response_data}), 200


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_images(images_path):
    temp_dir = tempfile.mkdtemp()
    for img_file in os.listdir(images_path):
        img_path = os.path.join(images_path, img_file)
        img = Image.open(img_path)
        img = img.resize((640, 480))  # Adjust size as per your requirement
        img.save(os.path.join(temp_dir, img_file))
    return temp_dir

   
@app.route('/create')
def createvideo():
    # Render your main HTML page here
    return render_template('createvid.html')


# Add a route to fetch the list of available audio files
@app.route('/available_audios', methods=['GET'])
def get_available_audios():
    # Define the paths for the audio files
    audio_files = [
        {'name': 'Song 1', 'url': '/static/song1.mp3'},
        {'name': 'Song 2', 'url': '/static/song2.mp3'},
        {'name': 'Song 3', 'url': '/static/song3.mp3'},
        {'name': 'Song 4', 'url': '/static/song4.mp3'}
    ]
    return jsonify(audio_files)

# Modify the create_video route to accept the selected audio file and include it in the video
@app.route('/create_video', methods=['POST'])
def create_video():
    # Paths for images and audio
    images_path = os.path.join('static', 'saved_images')
    audio_folder = 'static'  # Adjust this path as per your audio file location
    
    # Get all image files
    images = [img for img in os.listdir(images_path) if img.endswith((".png", ".jpg"))]
    if not images:
        return "No images found in the uploads folder", 400

    # Resize images if needed
    resized_images_path = resize_images(images_path)

    # Get the list of image files with their full paths
    image_files = [os.path.join(resized_images_path, img) for img in images]
    total_duration = len(image_files)
    # Create a video
    video = concatenate_videoclips([ImageClip(img).set_duration(1) for img in image_files])

    # Get the selected audio filename from the request
    selected_audio = request.form.get('audio_src')  # This should match the name of your hidden input field

    # If the selected audio file exists, set it as the audio for the video
    if selected_audio:
        audio_path = os.path.join(audio_folder, selected_audio)
        if os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            audio = audio.subclip(0, total_duration)
            video = video.set_audio(audio)

    # Export the video with specified fps
    output_path = os.path.join(tempfile.mkdtemp(), 'output.mp4')
    video.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)  # Specify fps=24

    return send_file(output_path, mimetype='video/mp4')


@app.route('/signup', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if not check_column_exists('jwt_token', 'users'):
            # If the column doesn't exist, add it to the table
            add_jwt_token_column()
        hashed_password = generate_password_hash(password)
        conn = connect_to_database()
        cursor = conn.cursor()
        # Hash the password
        check_query = "SELECT COUNT(*) FROM users WHERE email = %s"
        cursor.execute(check_query, (email,))
        result = cursor.fetchone()

        if result[0] > 0:
            # Close database connection
            cursor.close()
            conn.close()
            # Flash a message and redirect to the sign-up page
            flash("Account already exists for this email. Please login.")
            return redirect(url_for('sign'))
        token=generate_token(email)
        insert_query = "INSERT INTO users (name, email, password,jwt_token) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (name, email, hashed_password,token))
        conn.commit()

        # Close database connection
        cursor.close()
        conn.close()
        flash("Account created.Login now.")
        # Redirect to the login page
        return redirect(url_for('login'))

    return render_template('sign.html')

@app.route('/')
def main():
    # Render your main HTML page here
    return render_template('main.html')

@app.route('/home')
def home():
    username = session.get('username')  # Get the username from session
    return render_template('home.html', username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        password = request.form['password']
        conn = connect_to_database()
        cursor = conn.cursor()
        if email == 'admin@gmail.com' and password == 'admin1234':
            # Fetch all users for admin
            all_users_query = "SELECT * FROM users"
            cursor.execute(all_users_query)
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template('admin.html', users=users)
        # Connect to MySQL database
        else:
       
        # Retrieve user data from database for the given email
            select_query = "SELECT id, email, name, password ,jwt_token FROM users WHERE email = %s"
            cursor.execute(select_query, (email,))
        
        # Fetch all results from the cursor
            user = cursor.fetchone()

        # Check if any user with the given email exists
            if user:
                if  check_password_hash(user[3], password):
                    if user[4]:
                        decoded_email = decode_token(user[4])
                        if decoded_email==email:
                             session['username'] = user[2]
                             session['id']=user[0]
                             session['email'] = email
                             saved_images_dir = os.path.join(os.getcwd(), 'static','saved_images')
                             if os.path.exists(saved_images_dir):
                                 shutil.rmtree(saved_images_dir)
                             os.makedirs(saved_images_dir, exist_ok=True)
                # Close database connection
                             cursor.close()
                             conn.close()
                             return redirect(url_for('home'))
                        else:
                            flash("Invalid JWT token. Please log in again.")
                            return redirect(url_for('login'))
                    else:
                        flash("JWT token not found for the user. Please log in again.")
                        return redirect(url_for('login'))
                else:
                    flash("invalid email or password")
                    return redirect(url_for('login'))
            else:
                flash("User with the provided email does not exist")
                return redirect(url_for('login'))      

    return render_template('login.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)

