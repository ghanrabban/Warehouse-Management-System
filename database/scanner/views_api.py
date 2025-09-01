# scanner/views_api.py
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.views.decorators.http import require_http_methods
from django.conf import settings
import traceback

def dictfetchall(cursor):
    "Return rows from a cursor as a list of dicts"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def json_error(msg, code=500):
    return JsonResponse({'error': msg}, status=code)

@csrf_exempt
@require_http_methods(["GET", "POST", "DELETE"])
def api_php_compat(request):
    """
    A compatibility endpoint that replaces api.php.
    Accepts the same `action` query param used by the frontend.
    """
    action = request.GET.get('action', '') or (request.POST.get('action') if request.POST else '')
    try:
        if action == 'getAllData':
            return handle_get_all_data()
        elif action == 'addItemIn':
            payload = json.loads(request.body or b'{}')
            return handle_add_item_in(payload)
        elif action == 'deleteItemIn':
            id_ = request.GET.get('id')
            return handle_delete_item_in(id_)
        elif action == 'addItemOut':
            payload = json.loads(request.body or b'{}')
            return handle_add_item_out(payload)
        elif action == 'deleteItemOut':
            id_ = request.GET.get('id')
            return handle_delete_item_out(id_)
        elif action == 'addSparepart':
            payload = json.loads(request.body or b'{}')
            return handle_add_sparepart(payload)
        elif action == 'deleteSparepart':
            id_ = request.GET.get('id')
            return handle_delete_sparepart(id_)
        else:
            return JsonResponse({'error': f"Unknown action '{action}'"}, status=400)
    except Exception as exc:
        # Helpful debug info while DEBUG=True; returns minimal message otherwise.
        if settings.DEBUG:
            tb = traceback.format_exc()
            return JsonResponse({'error': str(exc), 'traceback': tb}, status=500)
        return JsonResponse({'error': 'Internal server error'}, status=500)


# --- Handlers (use safe parameterization) ---
def handle_get_all_data():
    with connection.cursor() as cur:
        # items_in
        try:
            cur.execute("SELECT * FROM items_in ORDER BY id DESC")
            itemInData = dictfetchall(cur)
        except Exception:
            itemInData = []

        # items_out joined with items_in for details (if table exists)
        try:
            cur.execute("""
                SELECT o.*, i.category, i.subcategory, i.item_name
                FROM items_out o
                JOIN items_in i ON o.item_in_id = i.id
                ORDER BY o.id DESC
            """)
            itemOutData = dictfetchall(cur)
        except Exception:
            itemOutData = []

        # spareparts
        try:
            cur.execute("SELECT * FROM spareparts ORDER BY id DESC")
            sparepartData = dictfetchall(cur)
        except Exception:
            sparepartData = []

    return JsonResponse({
        'itemInData': itemInData,
        'itemOutData': itemOutData,
        'sparepartData': sparepartData
    })


def handle_add_item_in(payload):
    # minimal validation
    category = payload.get('category') or ''
    subcategory = payload.get('subcategory') or ''
    date_in = payload.get('dateIn') or None
    pic = payload.get('pic') or ''
    organic = payload.get('organic') or ''
    # create a unique item_name (mimic the PHP implementation)
    import time
    item_name = f"{category}-{subcategory}-{int(time.time())}"
    with connection.cursor() as cur:
        cur.execute(
            "INSERT INTO items_in (category, subcategory, item_name, date_in, pic, organic) VALUES (%s,%s,%s,%s,%s,%s)",
            [category, subcategory, item_name, date_in, pic, organic]
        )
        last = cur.lastrowid if hasattr(cur, 'lastrowid') else cur.connection.insert_id()
        cur.execute("SELECT * FROM items_in WHERE id=%s", [last])
        new_item = dictfetchall(cur)
    return JsonResponse(new_item[0] if new_item else {})


def handle_delete_item_in(id_):
    if not id_:
        return JsonResponse({'error': 'ID not provided'}, status=400)
    with connection.cursor() as cur:
        # delete dependent items_out then items_in (transaction-like)
        cur.execute("DELETE FROM items_out WHERE item_in_id = %s", [id_])
        cur.execute("DELETE FROM items_in WHERE id = %s", [id_])
    return JsonResponse({'success': True})


def handle_add_item_out(payload):
    item_in_id = payload.get('item_in_id')
    date_out = payload.get('dateOut')
    pic = payload.get('pic') or ''
    organic = payload.get('organic') or ''
    notes = payload.get('notes') or ''
    if not item_in_id:
        return JsonResponse({'error': 'item_in_id required'}, status=400)
    with connection.cursor() as cur:
        cur.execute("INSERT INTO items_out (item_in_id, date_out, pic, organic, notes) VALUES (%s,%s,%s,%s,%s)",
                    [item_in_id, date_out, pic, organic, notes])
        last = cur.lastrowid if hasattr(cur, 'lastrowid') else cur.connection.insert_id()
        cur.execute("""
            SELECT o.*, i.category, i.subcategory, i.item_name
            FROM items_out o
            JOIN items_in i ON o.item_in_id = i.id
            WHERE o.id = %s
        """, [last])
        new_item = dictfetchall(cur)
    return JsonResponse(new_item[0] if new_item else {})


def handle_delete_item_out(id_):
    if not id_:
        return JsonResponse({'error': 'ID not provided'}, status=400)
    with connection.cursor() as cur:
        cur.execute("DELETE FROM items_out WHERE id = %s", [id_])
    return JsonResponse({'success': True, 'deleted_id': id_})


def handle_add_sparepart(payload):
    date = payload.get('date')
    item_name = payload.get('item_name')
    qty = payload.get('qty') or 0
    satuan = payload.get('satuan') or ''
    price = payload.get('price') or 0
    with connection.cursor() as cur:
        cur.execute("INSERT INTO spareparts (date, item_name, qty, satuan, price) VALUES (%s,%s,%s,%s,%s)",
                    [date, item_name, qty, satuan, price])
        last = cur.lastrowid if hasattr(cur, 'lastrowid') else cur.connection.insert_id()
        cur.execute("SELECT * FROM spareparts WHERE id = %s", [last])
        new_item = dictfetchall(cur)
    return JsonResponse(new_item[0] if new_item else {})


def handle_delete_sparepart(id_):
    if not id_:
        return JsonResponse({'error': 'ID not provided'}, status=400)
    with connection.cursor() as cur:
        cur.execute("DELETE FROM spareparts WHERE id = %s", [id_])
    return JsonResponse({'success': True, 'deleted_id': id_})
