# Project 1 — Personal Homepage (Student)

---

## Assignment Intro

In this assignment you will be implementing your homepage using CSS, Java script, HTML and postgreSQL OR MongoDB

Please provide a creative addition to your page, something that will differentiate it from every other page. 

Please commit your project code into a individual repo under the class Org, named Project1-FirstNameLastName

Potential Rubric :

Design document including at least:
* Project description
* User Personas
* User stories (use cases but with a story)

*Add least 2 tables using postgreSQL OR MongoDB

PLEASE ADD THESE IN README FILES

---

## Author & Course Info
- **Name:** Student  
- **Course:** CS5610 Web Development  
- **Time:** Oct.10.2025  
- **Term:** Fall 2025
- **Repo:** `project1-personal-homepage`

---

## Design Document

### Project Description
My simple and personal website built for **CS5610 Web Development project 1**.  
It includes a homepage, an About page, a Gallery with custom animation, a CS5610 Links page backed by PostgreSQL, and a Guestbook page.  

| Page | Purpose |
|:----|:----|
| Home | Short intro and contact email |
| About | Education & interests |
| Gallery | Personal photos with a custom lightbox |
| Links | CS5610 GitHub repos from PostgreSQL |
| Guestbook | Simple page for visitors to post messages |

### User Personas
1. **Prof & TA ** — verifies rubric requirements and database integration.  
2. **Classmates / Visitors** — browse photos and leave a message.  

### User Stories
- As a visitor, I can browse photos and open them with keyboard ← → Esc navigation.  
- As a TA, I can see database-driven links on `/links.html`and access previous HWs.  
- As a visitor, I can switch themes and the site remembers my choice.  
- As a visitor, I can leave a short message on the Guestbook page.

---

## Creative Features
- **Animated Lightbox** — custom JS with smooth transitions and keyboard support.  
- **Three-state Theme Switcher** (System / Light / Dark).  
- **Guestbook** — stores messages to PostgreSQL in real time.

---

## Tech Stack
- **Frontend:** HTML5, CSS, vanilla JavaScript  
- **Backend:** Node.js
- **Database:** PostgreSQL with two tables:  
  - `links`
  - `guestbook`

---

## Folder Structure
```
project1-personal-homepage/
├── assets/
│   ├── icons/               # favicon
│   └── images/              # personal photos
├── public/
│   ├── index.html           # homepage
│   ├── about.html
│   ├── gallery.html
│   ├── links.html
│   └── guestbook.html
├── scripts/
│   └── app.js               # theme, lightbox, links, guestbook
├── styles/
│   └── main.css             # global styles
├── server/
│   ├── server.js            # Express server + API routes
│   ├── schema.sql           # create + seed tables
│   └── .env                 # local DB config
├── package.json
└── README.md
```

---

## Setup Steps (macOS)

### 1 — Start PostgreSQL
```bash
brew services start postgresql@16
```

### 2 — Create User and Database
```bash
psql postgres -c "CREATE ROLE project1 LOGIN PASSWORD '<password>';"
psql postgres -c "CREATE DATABASE project1_student OWNER project1;"
```

### 3 — Environment Variables (`server/.env`)
```
PGHOST=localhost
PGUSER=project1
PGPASSWORD=<password>
PGDATABASE=project1_student
PGPORT=5432
PORT=3000
```

### 4 — Create Tables + Seed Data
```bash
psql "postgresql://project1:<password>@localhost:5432/project1_student" -f server/schema.sql
```

### 5 — Install and Run
```bash
npm install
npm start
```

### 6 — Open in Browser
- Home: <http://localhost:3000/>  
- About: <http://localhost:3000/about.html>  
- Gallery: <http://localhost:3000/gallery.html>  
- Links: <http://localhost:3000/links.html>  
- Guestbook: <http://localhost:3000/guestbook.html>  
- API check: <http://localhost:3000/api/links> and <http://localhost:3000/api/guestbook>

---

## W3C Validation
Validated at <https://validator.w3.org/> for all pages.  
Each HTML file shows:  
> “Document checking completed. No errors or warnings to show.”

