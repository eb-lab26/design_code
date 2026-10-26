import json
import os
import threading
from datetime import date
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
POSTS_FILE = BASE_DIR / "posts.json"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "kod-dizaina-dev-key")

# Блокировка, чтобы два одновременных запроса не перезаписали файл
_lock = threading.RLock()


def load_posts():
    """Читает факты из posts.json."""
    if not POSTS_FILE.exists():
        return []

    try:
        with POSTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        app.logger.exception("Не удалось прочитать posts.json")
        return []

    if isinstance(data, dict):
        return data.get("posts", [])
    return data


def save_posts(posts):
    """Сохраняет факты в posts.json."""
    with _lock:
        with POSTS_FILE.open("w", encoding="utf-8") as file:
            json.dump({"posts": posts}, file, ensure_ascii=False, indent=2)
            file.write("\n")


def next_id(posts):
    return max((post.get("id", 0) for post in posts), default=0) + 1


@app.get("/")
def index():
    posts = load_posts()
    posts.sort(key=lambda post: (post.get("created_at", ""), post.get("id", 0)), reverse=True)

    categories = sorted({post["category"] for post in posts if post.get("category")})
    active_category = request.args.get("category", "").strip()

    visible_posts = posts
    if active_category:
        visible_posts = [post for post in posts if post.get("category") == active_category]

    return render_template(
        "index.html",
        posts=visible_posts,
        total=len(posts),
        categories=categories,
        active_category=active_category,
        year=date.today().year,
    )


@app.route("/add", methods=["GET", "POST"])
def add_post():
    form = {"title": "", "text": "", "category": "", "source": ""}

    if request.method == "POST":
        form = {
            "title": request.form.get("title", "").strip(),
            "text": request.form.get("text", "").strip(),
            "category": request.form.get("category", "").strip(),
            "source": request.form.get("source", "").strip(),
        }

        errors = []
        if not form["title"]:
            errors.append("Добавьте заголовок факта.")
        elif len(form["title"]) > 120:
            errors.append("Заголовок не должен быть длиннее 120 символов.")

        if not form["text"]:
            errors.append("Добавьте текст факта.")
        elif len(form["text"]) < 20:
            errors.append("Текст факта слишком короткий — минимум 20 символов.")
        elif len(form["text"]) > 1200:
            errors.append("Текст факта не должен быть длиннее 1200 символов.")

        if not form["category"]:
            errors.append("Укажите категорию.")
        elif len(form["category"]) > 40:
            errors.append("Категория не должна быть длиннее 40 символов.")

        if len(form["source"]) > 200:
            errors.append("Источник не должен быть длиннее 200 символов.")

        for error in errors:
            flash(error, "error")

        if not errors:
            with _lock:
                posts = load_posts()
                post = {
                    "id": next_id(posts),
                    "title": form["title"],
                    "text": form["text"],
                    "category": form["category"],
                    "source": form["source"],
                    "created_at": date.today().isoformat(),
                }
                posts.append(post)
                save_posts(posts)

            flash("Факт опубликован — он уже на главной странице.", "success")
            return redirect(url_for("index"))

    return render_template("add_post.html", form=form, year=date.today().year)


@app.post("/post/<int:post_id>/smm")
def generate_smm(post_id):
    """Заглушка: оживим генератор SMM-постов на следующем уроке."""
    posts = load_posts()
    post = next((item for item in posts if item.get("id") == post_id), None)

    if post is None:
        flash("Такой факт не найден — возможно, он уже удалён.", "error")
        return redirect(url_for("index"))

    flash(
        f"Генератор SMM-постов скоро появится. Факт «{post['title']}» уже выбран — "
        "функция оживёт на следующем уроке.",
        "info",
    )

    category = request.form.get("category", "").strip()
    if category:
        return redirect(url_for("index", category=category))
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
