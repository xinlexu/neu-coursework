from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
import json, threading, itertools
from datetime import datetime

def _now():
    return datetime.utcnow().isoformat() + "Z"

def hello(_request):
    return JsonResponse({"status": "running"})

_LOCK = threading.Lock()
_ID = itertools.count(1)
PRIORITIES = {"low","medium","high"}
TODO_ITEMS = [
    {"id": next(_ID), "title": "Set up Week6 project", "priority": "high", "tags": ["setup","cs5610"], "done": False, "created": _now(), "updated": _now()},
    {"id": next(_ID), "title": "Wire React to Django", "priority": "medium", "tags": ["api"], "done": True, "created": _now(), "updated": _now()},
    {"id": next(_ID), "title": "Write README steps", "priority": "low", "tags": ["docs"], "done": False, "created": _now(), "updated": _now()},
]

def _json(request):
    try: return json.loads(request.body or b"{}")
    except json.JSONDecodeError: return {}

def _tags(x):
    if x is None: return []
    if isinstance(x, list): return [str(t).strip() for t in x if str(t).strip()]
    if isinstance(x, str): return [t.strip() for t in x.split(",") if t.strip()]
    return []

@csrf_exempt
def todos_collection(request):
    if request.method == "GET":
        q = (request.GET.get("q") or "").strip().lower()
        status = (request.GET.get("status") or "all").lower()
        priority = (request.GET.get("priority") or "all").lower()
        tag = (request.GET.get("tag") or "").strip().lower()
        with _LOCK: items = list(TODO_ITEMS)
        def match(it):
            if status == "active" and it["done"]: return False
            if status == "done" and not it["done"]: return False
            if priority != "all" and it["priority"] != priority: return False
            if q and (q not in it["title"].lower() and all(q not in t.lower() for t in it["tags"])): return False
            if tag and tag not in [t.lower() for t in it["tags"]]: return False
            return True
        return JsonResponse({"items": [it for it in items if match(it)]})
    if request.method == "POST":
        data = _json(request)
        title = (data.get("title") or "").strip()
        priority = (data.get("priority") or "medium").lower()
        tags = _tags(data.get("tags"))
        if not title: return JsonResponse({"error":"title is required"}, status=400)
        if priority not in PRIORITIES: return JsonResponse({"error":"invalid priority"}, status=400)
        with _LOCK:
            item = {"id": next(_ID), "title": title, "priority": priority, "tags": tags, "done": False, "created": _now(), "updated": _now()}
            TODO_ITEMS.append(item)
        return JsonResponse(item, status=201)
    return HttpResponseNotAllowed(["GET","POST"])

@csrf_exempt
def todos_detail(request, item_id: int):
    with _LOCK:
        idx = next((i for i, it in enumerate(TODO_ITEMS) if it["id"] == item_id), None)
        item = TODO_ITEMS[idx] if idx is not None else None
    if item is None: return JsonResponse({"error":"not found"}, status=404)
    if request.method == "PATCH":
        data = _json(request)
        title = data.get("title", item["title"])
        priority = data.get("priority", item["priority"])
        tags = data.get("tags", item["tags"])
        done = data.get("done", item["done"])
        if not isinstance(done, bool): return JsonResponse({"error":"done must be boolean"}, status=400)
        if not isinstance(title, str) or not title.strip(): return JsonResponse({"error":"invalid title"}, status=400)
        if not isinstance(priority, str) or priority.lower() not in PRIORITIES: return JsonResponse({"error":"invalid priority"}, status=400)
        with _LOCK:
            item["title"] = title.strip()
            item["priority"] = priority.lower()
            item["tags"] = _tags(tags)
            item["done"] = done
            item["updated"] = _now()
            updated = dict(item)
        return JsonResponse(updated)
    if request.method == "DELETE":
        with _LOCK: TODO_ITEMS.pop(idx)
        return JsonResponse({"ok": True})
    return HttpResponseNotAllowed(["PATCH","DELETE"])

def todos_stats(_request):
    with _LOCK:
        total = len(TODO_ITEMS)
        done = sum(1 for it in TODO_ITEMS if it["done"])
        active = total - done
        by_priority = {
            "low": sum(1 for it in TODO_ITEMS if it["priority"] == "low"),
            "medium": sum(1 for it in TODO_ITEMS if it["priority"] == "medium"),
            "high": sum(1 for it in TODO_ITEMS if it["priority"] == "high"),
        }
    return JsonResponse({"total": total, "done": done, "active": active, "by_priority": by_priority})

@csrf_exempt
def feedback(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    data = _json(request)
    message = (data.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "message required"}, status=400)
    return JsonResponse({"ok": True})

def meta(_request):
    return JsonResponse({"service":"week6-backend","now":_now()})
