from flask import Flask, render_template, request, redirect
import sqlite3
import webbrowser

app = Flask(__name__)

# 重大事故時の通知ロジック
def send_mail(date, location, title, detail):
    print("\n===== ⚠️ 重大事故通知 =====")
    print(f"発生日: {date}")
    print(f"場所 : {location}")
    print(f"件名 : {title}")
    print(f"詳細 : {detail}")
    print("==========================\n")

# データベース初期化（『場所』カラムをしっかり追加）
def init_db():
    conn = sqlite3.connect("incidents.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS incidents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        location TEXT,
        title TEXT,
        level TEXT,
        detail TEXT
    )
    """)
    conn.commit()
    conn.close()

# 一覧表示（ソート機能 ＆ 繰り返し検出付き）
@app.route("/")
def index():
    # 画面からどの順で並び替えるか（ソート条件）を受け取る
    sort_by = request.args.get("sort", "date_desc")
    
    conn = sqlite3.connect("incidents.db")
    cur = conn.cursor()

    # ソート条件によってSQLを切り替える
    if sort_by == "date_asc":
        cur.execute("SELECT * FROM incidents ORDER BY date ASC")
    elif sort_by == "level_desc":
        # 重大 ➔ 中 ➔ 軽微 の順に並ぶように調整
        cur.execute("""
            SELECT * FROM incidents 
            ORDER BY CASE level WHEN '重大' THEN 1 WHEN '中' THEN 2 ELSE 3 END ASC
        """)
    else:
        # デフォルトは日付の新しい順
        cur.execute("SELECT * FROM incidents ORDER BY date DESC")
        
    incidents = cur.fetchall()

    # 繰り返し発生しているインシデント（同じ件名が2回以上）を検出
    cur.execute("""
        SELECT title, COUNT(*) as occurrence_count 
        FROM incidents 
        GROUP BY title 
        HAVING occurrence_count >= 2
    """)
    repeated_incidents = cur.fetchall()

    conn.close()

    return render_template(
        "index.html",
        incidents=incidents,
        repeated_incidents=repeated_incidents,
        current_sort=sort_by
    )

# 新規登録
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        date = request.form["date"]
        location = request.form["location"]  # 場所を取得
        title = request.form["title"]
        level = request.form["level"]
        detail = request.form["detail"]

        conn = sqlite3.connect("incidents.db")
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO incidents (date, location, title, level, detail)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date, location, title, level, detail)
        )
        conn.commit()
        conn.close()

        # 重大事故の場合は通知を実行
        if level == "重大":
            send_mail(date, location, title, detail)

        return redirect("/")

    return render_template("add.html")

# 編集
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = sqlite3.connect("incidents.db")
    cur = conn.cursor()

    if request.method == "POST":
        date = request.form["date"]
        location = request.form["location"]  # 場所を取得
        title = request.form["title"]
        level = request.form["level"]
        detail = request.form["detail"]

        cur.execute(
            """
            UPDATE incidents
            SET date=?, location=?, title=?, level=?, detail=?
            WHERE id=?
            """,
            (date, location, title, level, detail, id)
        )
        conn.commit()
        conn.close()
        return redirect("/")

    cur.execute("SELECT * FROM incidents WHERE id=?", (id,))
    incident = cur.fetchone()
    conn.close()

    return render_template("edit.html", incident=incident)

# 削除
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("incidents.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM incidents WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# アプリ起動のメイン処理
if __name__ == "__main__":
    init_db()
    
    # アプリ起動時にブラウザを自動でポップアップさせる
    webbrowser.open("http://127.0.0.1:5000")
    
    app.run(debug=True, use_reloader=False)
