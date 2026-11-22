import requests


class ApiError(Exception):
    pass


class Api:
    def __init__(self, base="http://127.0.0.1:5000"):
        self.base = base.rstrip("/")
        self.token = None
        self.http = requests.Session()

    def _req(self, method, path, **kw):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            r = self.http.request(method, self.base + path, headers=headers, timeout=5, **kw)
        except requests.RequestException:
            raise ApiError("Tidak bisa terhubung ke server. Jalankan server/app.py dulu.")
        if not r.ok:
            try:
                msg = r.json().get("error")
            except ValueError:
                msg = None
            raise ApiError(msg or f"Error {r.status_code}")
        return r.json() if r.content else None

    # auth
    def login(self, username, password):
        d = self._req("POST", "/api/login", json={"username": username, "password": password})
        self.token = d["token"]
        return d

    def register(self, username, password):
        d = self._req("POST", "/api/register", json={"username": username, "password": password})
        self.token = d["token"]
        return d

    # subjects & sessions
    def subjects(self):
        return self._req("GET", "/api/subjects")

    def add_subject(self, name):
        return self._req("POST", "/api/subjects", json={"name": name})

    def add_session(self, subject_id, minutes, note=""):
        return self._req("POST", "/api/sessions", json={"subject_id": subject_id, "minutes": minutes, "note": note})

    # tasks
    def tasks(self):
        return self._req("GET", "/api/tasks")

    def add_task(self, title, deadline=None, subject_id=None):
        return self._req("POST", "/api/tasks", json={"title": title, "deadline": deadline, "subject_id": subject_id})

    def update_task(self, tid, **fields):
        return self._req("PATCH", f"/api/tasks/{tid}", json=fields)

    def delete_task(self, tid):
        return self._req("DELETE", f"/api/tasks/{tid}")

    # stats
    def stats(self, days=7):
        return self._req("GET", "/api/stats", params={"days": days})

    # concept maps
    def maps(self):
        return self._req("GET", "/api/maps")

    def add_map(self, title):
        return self._req("POST", "/api/maps", json={"title": title})

    def get_map(self, mid):
        return self._req("GET", f"/api/maps/{mid}")

    def save_map(self, mid, data):
        return self._req("PUT", f"/api/maps/{mid}", json={"data": data})

    def delete_map(self, mid):
        return self._req("DELETE", f"/api/maps/{mid}")
