# NEU Coursework

Curated Northeastern University computer science coursework and projects.

## Project navigation

| Project | Focus | Location |
| --- | --- | --- |
| Smart Study Assistant | Full-stack RAG chat with document retrieval and citations | [CS5610 final project](CS5610/final-project-rag-chat/) |
| Secure Reliable File Transfer | UDP protocol, reliability and authenticated encryption; group project | [CS5700 SRFT](CS5700/reliable-file-transfer/) · [upstream provenance](CS5700/reliable-file-transfer/UPSTREAM.md) |
| Educational QA demo | Document-grounded answers, citations and guardrails | [CS5100 workshop](CS5100/workshop-qa-tool/) |
| Route planning | Search algorithms and supporting map data | [CS5100 homework 2](CS5100/hw2-route-planning/) |

These are coursework snapshots. Setup instructions and dependencies belong to each project; this repository does not have a single shared build command.

## Contents

- [CS5010](CS5010/) - Program Design Paradigms
  - Java OOP midterm source and tests extracted from the local archive.
- [CS5100](CS5100/) - Intro to AI
  - `final-project/` - machine learning notebooks and cleaned data from the former `CS5100-FinalProject` GitHub repository.
  - `hw1-recommender/` - recommendation-system notebook and public MovieLens 100K data.
  - `hw2-route-planning/` - route-planning/search source, grader harness, and small San Jose support data.
  - `hw3-adversarial-search/` - adversarial-search source and notebook.
  - `hw4/` - cleaned notebook submission.
  - `hw5-clustering/` - cleaned clustering notebook submission.
  - `hw6-ui-prediction/` - UI-event prediction source with small public/support data; trained models and large logs are omitted.
  - `workshop-qa-tool/` - educational QA demo with citation and guardrail logic.
- [CS5200](CS5200/) - Database
  - `lab2-er-model/` - database modeling artifacts.
  - `lab6-invoice/` - SQL/Python invoice query exercise.
  - `lab7-triggers/` - trigger SQL exercise.
  - `lab9-transactions/` - SQL and Python transaction/isolation exercises.
- [CS5610](CS5610/) - Web Dev
  - Weekly web development assignments.
  - `project1-personal-homepage/`
  - `project2-auto-mpg/`
  - `final-project-rag-chat/` - CS5610 Smart Study Assistant / RAG chat app; includes a small sample `rag.jsonl`; local vector DB/cache artifacts are omitted.
- [CS5700](CS5700/) - Computer Network
  - `assignment5-socket-programming/`
  - `assignment6-proxy-server/`
  - `reliable-file-transfer/` - group SRFT project, synchronized from `tszwinglitw/cs5700-group-05` with large test-result artifacts omitted.
- [CS6120](CS6120/) - Natural Language Processing
  - `assignment1/`, `assignment3/`, `assignment5/`, `assignment6/` - NLP assignment source.
  - `midterm/` - cleaned notebook.
  - `final-recipe-project/` - cleaned final-project notebooks; generated vectors, reports, and large recipe/news datasets are omitted.

## Curation Notes

This repository intentionally excludes local dependencies, virtual environments, `.env` files, build outputs, PDFs, archives, packet captures, videos, and large VM/lab materials. Notebook outputs were cleared before publishing so local machine paths and transient runtime output are not stored in git.
