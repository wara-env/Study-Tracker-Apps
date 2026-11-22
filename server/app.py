import json
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, g, jsonify, request
from sqlalchemy import func

from models import ConceptMap, StudySession, Subject, Task, User, db, now


def create_app(db_uri="sqlite:///study_tracker.db"):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    db.init_app(app)
    with app.app_context():
        db.create_all()

    def auth(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            header = request.headers.get("Authorization", "")
            token = header.removeprefix("Bearer ").strip()
            user = User.query.filter_by(token=token).first() if token else None
            if not user:
                return jsonify(error="unauthorized"), 401
            g.user = user
            return fn(*a, **kw)

        return wrapper

    def parse_dt(s):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None

    # ---------- auth ----------
    @app.post("/api/register")
    def register():
        d = request.get_json(silent=True) or {}
        username, pw = (d.get("username") or "").strip(), d.get("password") or ""
        if len(username) < 3 or len(pw) < 6:
            return jsonify(error="username min 3, password min 6 karakter"), 400
        if User.query.filter_by(username=username).first():
            return jsonify(error="username sudah dipakai"), 409
        u = User(username=username)
        u.set_password(pw)
        token = u.new_token()
        db.session.add(u)
        db.session.commit()
        return jsonify(token=token, username=username), 201

    @app.post("/api/login")
    def login():
        d = request.get_json(silent=True) or {}
        u = User.query.filter_by(username=(d.get("username") or "").strip()).first()
        if not u or not u.check_password(d.get("password") or ""):
            return jsonify(error="username/password salah"), 401
        token = u.new_token()
        db.session.commit()
        return jsonify(token=token, username=u.username)

    # ---------- subjects ----------
    @app.get("/api/subjects")
    @auth
    def list_subjects():
        rows = Subject.query.filter_by(user_id=g.user.id).order_by(Subject.name).all()
        return jsonify([s.to_dict() for s in rows])

    @app.post("/api/subjects")
    @auth
    def add_subject():
        name = ((request.get_json(silent=True) or {}).get("name") or "").strip()
        if not name:
            return jsonify(error="nama wajib diisi"), 400
        s = Subject.query.filter_by(user_id=g.user.id, name=name).first()
        if not s:
            s = Subject(user_id=g.user.id, name=name)
            db.session.add(s)
            db.session.commit()
        return jsonify(s.to_dict()), 201

    # ---------- study sessions ----------
    @app.get("/api/sessions")
    @auth
    def list_sessions():
        rows = (
            StudySession.query.filter_by(user_id=g.user.id)
            .order_by(StudySession.created_at.desc())
            .limit(200)
            .all()
        )
        return jsonify([r.to_dict() for r in rows])

    @app.post("/api/sessions")
    @auth
    def add_session():
        d = request.get_json(silent=True) or {}
        subject = Subject.query.filter_by(id=d.get("subject_id"), user_id=g.user.id).first()
        minutes = d.get("minutes")
        if not subject:
            return jsonify(error="subject tidak ditemukan"), 404
        if not isinstance(minutes, int) or not 1 <= minutes <= 720:
            return jsonify(error="minutes harus 1-720"), 400
        s = StudySession(
            user_id=g.user.id, subject_id=subject.id, minutes=minutes, note=d.get("note", "")[:255]
        )
        db.session.add(s)
        db.session.commit()
        return jsonify(s.to_dict()), 201

    # ---------- tasks ----------
    @app.get("/api/tasks")
    @auth
    def list_tasks():
        rows = (
            Task.query.filter_by(user_id=g.user.id)
            .order_by(Task.done, Task.deadline.is_(None), Task.deadline)
            .all()
        )
        return jsonify([t.to_dict() for t in rows])

    @app.post("/api/tasks")
    @auth
    def add_task():
        d = request.get_json(silent=True) or {}
        title = (d.get("title") or "").strip()
        if not title:
            return jsonify(error="judul wajib diisi"), 400
        t = Task(
            user_id=g.user.id,
            title=title[:200],
            deadline=parse_dt(d.get("deadline")),
            subject_id=d.get("subject_id"),
        )
        db.session.add(t)
        db.session.commit()
        return jsonify(t.to_dict()), 201

    @app.patch("/api/tasks/<int:tid>")
    @auth
    def update_task(tid):
        t = Task.query.filter_by(id=tid, user_id=g.user.id).first_or_404()
        d = request.get_json(silent=True) or {}
        if "done" in d:
            t.done = bool(d["done"])
        if "title" in d and d["title"].strip():
            t.title = d["title"].strip()[:200]
        if "deadline" in d:
            t.deadline = parse_dt(d["deadline"])
        db.session.commit()
        return jsonify(t.to_dict())

    @app.delete("/api/tasks/<int:tid>")
    @auth
    def delete_task(tid):
        t = Task.query.filter_by(id=tid, user_id=g.user.id).first_or_404()
        db.session.delete(t)
        db.session.commit()
        return "", 204

    # ---------- stats ----------
    @app.get("/api/stats")
    @auth
    def stats():
        days = min(max(int(request.args.get("days", 7)), 1), 90)
        since = now() - timedelta(days=days - 1)
        since = since.replace(hour=0, minute=0, second=0, microsecond=0)

        daily = {
            (since + timedelta(days=i)).date().isoformat(): 0 for i in range(days)
        }
        sessions = StudySession.query.filter(
            StudySession.user_id == g.user.id, StudySession.created_at >= since
        ).all()
        for s in sessions:
            daily[s.created_at.date().isoformat()] += s.minutes

        by_subject = (
            db.session.query(Subject.name, func.sum(StudySession.minutes))
            .join(StudySession, StudySession.subject_id == Subject.id)
            .filter(StudySession.user_id == g.user.id, StudySession.created_at >= since)
            .group_by(Subject.name)
            .all()
        )

        # streak: hari berturut-turut (sampai hari ini) dengan >=1 sesi
        all_days = {
            r[0]
            for r in db.session.query(func.date(StudySession.created_at))
            .filter(StudySession.user_id == g.user.id)
            .distinct()
            .all()
        }
        streak, cur = 0, now().date()
        while cur.isoformat() in all_days:
            streak += 1
            cur -= timedelta(days=1)

        return jsonify(
            daily=daily,
            by_subject={name: int(total) for name, total in by_subject},
            total_minutes=sum(daily.values()),
            streak=streak,
        )

    # ---------- concept maps ----------
    @app.get("/api/maps")
    @auth
    def list_maps():
        rows = ConceptMap.query.filter_by(user_id=g.user.id).order_by(ConceptMap.updated_at.desc()).all()
        return jsonify([m.to_dict(with_data=False) for m in rows])

    @app.post("/api/maps")
    @auth
    def add_map():
        title = ((request.get_json(silent=True) or {}).get("title") or "").strip()
        if not title:
            return jsonify(error="judul wajib diisi"), 400
        m = ConceptMap(user_id=g.user.id, title=title[:150])
        db.session.add(m)
        db.session.commit()
        return jsonify(m.to_dict()), 201

    @app.get("/api/maps/<int:mid>")
    @auth
    def get_map(mid):
        m = ConceptMap.query.filter_by(id=mid, user_id=g.user.id).first_or_404()
        return jsonify(m.to_dict())

    @app.put("/api/maps/<int:mid>")
    @auth
    def save_map(mid):
        m = ConceptMap.query.filter_by(id=mid, user_id=g.user.id).first_or_404()
        d = request.get_json(silent=True) or {}
        data = d.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("nodes"), list) or not isinstance(data.get("edges"), list):
            return jsonify(error="data harus berisi nodes & edges"), 400
        m.data = json.dumps(data)
        if d.get("title"):
            m.title = d["title"][:150]
        db.session.commit()
        return jsonify(m.to_dict())

    @app.delete("/api/maps/<int:mid>")
    @auth
    def delete_map(mid):
        m = ConceptMap.query.filter_by(id=mid, user_id=g.user.id).first_or_404()
        db.session.delete(m)
        db.session.commit()
        return "", 204

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
