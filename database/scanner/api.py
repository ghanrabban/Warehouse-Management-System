import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import ItemIn, ItemOut, Sparepart
from django.shortcuts import get_object_or_404
from django.db import transaction

def serialize_item_in(obj):
    return {
        "id": obj.id,
        "category": obj.category,
        "subcategory": obj.subcategory,
        "item_name": obj.item_name,
        "date_in": obj.date_in.isoformat() if obj.date_in else None,
        "pic": obj.pic,
        "organic": obj.organic,
        "created_at": obj.created_at.isoformat(),
    }

def serialize_item_out(obj):
    return {
        "id": obj.id,
        "item_in_id": obj.item_in_id,
        "date_out": obj.date_out.isoformat() if obj.date_out else None,
        "pic": obj.pic,
        "organic": obj.organic,
        "notes": obj.notes,
        "created_at": obj.created_at.isoformat(),
        "category": obj.item_in.category,
        "subcategory": obj.item_in.subcategory,
        "item_name": obj.item_in.item_name,
    }

def serialize_sparepart(obj):
    return {
        "id": obj.id,
        "date": obj.date.isoformat() if obj.date else None,
        "item_name": obj.item_name,
        "qty": obj.qty,
        "satuan": obj.satuan,
        "price": float(obj.price),
        "created_at": obj.created_at.isoformat(),
    }

@csrf_exempt
def api_router(request):
    action = request.GET.get('action', '')
    try:
        if action == 'getAllData':
            return get_all_data(request)
        if action == 'addItemIn':
            return add_item_in(request)
        if action == 'deleteItemIn':
            return delete_item_in(request)
        if action == 'addItemOut':
            return add_item_out(request)
        if action == 'deleteItemOut':
            return delete_item_out(request)
        if action == 'addSparepart':
            return add_sparepart(request)
        if action == 'deleteSparepart':
            return delete_sparepart(request)

        return JsonResponse({"error": "Aksi tidak valid"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_all_data(request):
    item_in_qs = ItemIn.objects.all().order_by('-id')
    item_in = [serialize_item_in(i) for i in item_in_qs]

    item_out_qs = ItemOut.objects.select_related('item_in').all().order_by('-id')
    item_out = [serialize_item_out(o) for o in item_out_qs]

    spare_qs = Sparepart.objects.all().order_by('-id')
    sparepart = [serialize_sparepart(s) for s in spare_qs]

    return JsonResponse({
        "itemInData": item_in,
        "itemOutData": item_out,
        "sparepartData": sparepart
    })

@csrf_exempt
def add_item_in(request):
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    category = data.get('category', '')
    subcategory = data.get('subcategory', '')
    # generate item_name similar to PHP: category-subcategory-timestamp
    import time
    item_name = f"{category}-{subcategory}-{int(time.time())}"
    date_in = data.get('dateIn') or None
    pic = data.get('pic') or ''
    organic = data.get('organic') or ''

    item = ItemIn.objects.create(
        category=category, subcategory=subcategory, item_name=item_name,
        date_in=date_in, pic=pic, organic=organic
    )
    return JsonResponse(serialize_item_in(item))

@csrf_exempt
def delete_item_in(request):
    id = request.GET.get('id')
    if not id:
        return JsonResponse({"error": "ID tidak ditemukan"}, status=400)
    try:
        with transaction.atomic():
            ItemOut.objects.filter(item_in_id=id).delete()
            ItemIn.objects.filter(pk=id).delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def add_item_out(request):
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    item_in_id = data.get('item_in_id')
    if not item_in_id:
        return JsonResponse({"error": "Data input tidak lengkap"}, status=400)

    date_out = data.get('dateOut') or None
    pic = data.get('pic') or ''
    organic = data.get('organic') or ''
    notes = data.get('notes') or ''

    item_in = get_object_or_404(ItemIn, pk=item_in_id)
    out = ItemOut.objects.create(item_in=item_in, date_out=date_out, pic=pic, organic=organic, notes=notes)
    # return joined result similar to PHP
    out_full = ItemOut.objects.select_related('item_in').get(pk=out.pk)
    return JsonResponse(serialize_item_out(out_full))

@csrf_exempt
def delete_item_out(request):
    id = request.GET.get('id')
    if not id:
        return JsonResponse({"error": "ID tidak ditemukan"}, status=400)
    ItemOut.objects.filter(pk=id).delete()
    return JsonResponse({"success": True, "deleted_id": id})

@csrf_exempt
def add_sparepart(request):
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    date = data.get('date') or None
    item_name = data.get('item_name') or ''
    qty = int(data.get('qty') or 0)
    satuan = data.get('satuan') or ''
    price = float(data.get('price') or 0)
    s = Sparepart.objects.create(date=date, item_name=item_name, qty=qty, satuan=satuan, price=price)
    return JsonResponse(serialize_sparepart(s))

@csrf_exempt
def delete_sparepart(request):
    id = request.GET.get('id')
    if not id:
        return JsonResponse({"error": "ID tidak ditemukan"}, status=400)
    Sparepart.objects.filter(pk=id).delete()
    return JsonResponse({"success": True, "deleted_id": id})
