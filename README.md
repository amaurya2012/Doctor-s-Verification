# DoctorVerify India

A full-stack healthcare social platform: find verified doctors, share
posts, and get help fast in an emergency — all in one app.

Built with FastAPI (backend) and React + Vite (frontend), fully tested.

---

## What it does

Finding a doctor you can trust online is hard — anyone can claim
credentials. DoctorVerify India fixes that by only showing doctors
who've been reviewed and approved by an admin, with a visible
"Verified" badge.

On top of that, it has:
- **A social feed** — posts, likes, comments, follows, notifications
- **An SOS button** — sends your live location to a responder with one tap
- **A report system** — flag a fake doctor, a bad post, or a problem user

## Who it's for

- **Patients** — search verified doctors, follow them, ask questions, get help fast if something feels unsafe
- **Doctors** — register, get verified, build a presence through posts
- **Admins** — approve doctors, respond to SOS alerts, resolve complaints

This is a portfolio project — a real working prototype, not a live
service with real doctors yet.

---

## Tech stack

**Backend:** FastAPI, SQLAlchemy, Alembic, JWT auth, Google OAuth, Cloudinary

**Frontend:** React, Vite, Tailwind CSS

**Testing:** pytest (22/22 tests passing)

---

## Project structure

```
doctorverify/
├── backend/     FastAPI API — models, routes, business logic, tests
└── frontend/    React app — pages, components, API client
```

---

## Running it locally

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Then open the URL Vite prints (usually `http://localhost:5173`).

### Running tests

```bash
cd backend
source venv/Scripts/activate
python -m pytest tests/ -v
```

---

## Known limitations

- No UI yet for registering as a verified retired-police SOS responder
- Generic user profile pages are minimal (doctor profiles are fully built out)
- No image upload for posts yet
- Email verification doesn't actually send emails yet (stubbed)
- Certificate upload needs real Cloudinary credentials to work