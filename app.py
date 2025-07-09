from flask import Flask, request, redirect, render_template
from supabase import create_client, Client
import os
from dotenv import load_dotenv


load_dotenv()  # Baca file .env
# Supabase credentials
SUPABASE_URL = "https://etxyomkjynglfwmopytg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV0eHlvbWtqeW5nbGZ3bW9weXRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIwNDAzODcsImV4cCI6MjA2NzYxNjM4N30.ZWlhHLvpfLJ5E-oivh-BrdM01fpUzJOigdwgqi7__4E"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

import random, string

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        long_url = request.form['url']
        custom_code = request.form['custom_code'].strip()

        # Jika user isi custom code
        if custom_code:
            check = supabase.table("urls").select("code").eq("code", custom_code).execute()
            if check.data:
                return f"❌ Shortcode '{custom_code}' sudah digunakan. Coba kode lain.", 400
            code = custom_code
        else:
            code = generate_code()
            while supabase.table("urls").select("code").eq("code", code).execute().data:
                code = generate_code()

        # Simpan ke Supabase
        supabase.table("urls").insert({"code": code, "long_url": long_url}).execute()
        short_url = request.host_url + code
        return render_template('result.html', short_url=short_url)

    return render_template('form.html')

@app.route('/<code>')
def redirect_to_url(code):
    result = supabase.table("urls").select("long_url").eq("code", code).execute()
    if result.data:
        return redirect(result.data[0]['long_url'])
    return "URL not found", 404

# Admin dashboard
@app.route('/admin')
def admin():
    result = supabase.table("urls").select("*").execute()
    return render_template('admin.html', data=result.data)

# Edit
@app.route('/edit/<code>', methods=['GET', 'POST'])
def edit(code):
    result = supabase.table("urls").select("*").eq("code", code).execute()
    if not result.data:
        return "Shortcode tidak ditemukan", 404

    if request.method == 'POST':
        new_url = request.form['new_url'].strip()
        new_code = request.form['new_code'].strip()

        # Jika kode baru sudah digunakan dan beda dari yang sekarang
        if new_code != code:
            check = supabase.table("urls").select("code").eq("code", new_code).execute()
            if check.data:
                return "❌ Kode baru sudah digunakan", 400

        # Hapus lama, insert baru
        supabase.table("urls").delete().eq("code", code).execute()
        supabase.table("urls").insert({"code": new_code, "long_url": new_url}).execute()
        return redirect('/admin')

    return render_template('edit.html', code=code, url=result.data[0]['long_url'])

# Delete
@app.route('/delete/<code>', methods=['GET', 'POST'])
def delete(code):
    result = supabase.table("urls").select("*").eq("code", code).execute()
    if not result.data:
        return "Shortcode tidak ditemukan", 404

    if request.method == 'POST':
        supabase.table("urls").delete().eq("code", code).execute()
        return redirect('/admin')

    return render_template('delete.html', code=code, url=result.data[0]['long_url'])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
