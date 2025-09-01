import io
import json
from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie   # we render token into templates too
from django.forms.models import model_to_dict
from xhtml2pdf import pisa
from .models import BarcodeEvent, Report, ItemIn, ItemOut, Sparepart
from .forms import ReportUploadForm, GenerateBarcodeForm, ManualInputForm

# You’ll want to parameterize port & baud, but hard‑coding for now:
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE   = 9600

def index(request):
    return render(request, 'scanner/index.html')

def today_roster(request):
    today = timezone.localdate()
    rosters = DailyRoster.objects.filter(date=today)
    return render(request, 'scanner/today_roster.html', {'rosters': rosters})

def event_list(request):
    events = BarcodeEvent.objects.order_by('-created_at')[:50]
    upload_form = ReportUploadForm()
    return render(request, 'scanner/event_list.html', {
      'events': events,
      'upload_form': upload_form,
    })

def generate_view(request):
    if request.method == "POST":
        form = GenerateBarcodeForm(request.POST)
        if form.is_valid():
            form.create_barcode()
            return redirect("event_list")
    else:
        form = GenerateBarcodeForm()
    return render(request, "scanner/generate.html", {"form": form})

def manual_input_view(request):
    if request.method == 'POST':
        form = ManualInputForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            BarcodeEvent.objects.create(code=code, source=BarcodeEvent.MANUAL)
            return redirect('event_list')
    else:
        form = ManualInputForm()
    return render(request, 'scanner/manual.html', {'form': form})

def scan_view(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if code:
            BarcodeEvent.objects.create(code=code, source=BarcodeEvent.SCAN)
        return redirect('scan')   # reload page
    return render(request, 'scanner/scan.html')

def scan_page(request):
    # existing GET/POST handling
    if request.method == 'POST':
        code = request.POST.get('code','').strip()
        if code:
            BarcodeEvent.objects.create(code=code, source=BarcodeEvent.SCAN)
        return redirect('scan')
    return render(request, 'scanner/scan.html')

def scan_stream(request):
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=None)
    except Exception as e:
        return StreamingHttpResponse(
            f"data:ERROR opening port: {e}\n\n",
            content_type='text/event-stream',
        )

    def event_stream():
        buf = ''
        while True:
            ch = ser.read().decode(errors='ignore')
            if ch in ('\r','\n'):
                code = buf.strip(); buf = ''
                if code:
                    yield f"data:{code}\n\n"
            else:
                buf += ch

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

def export_events_pdf(request):
    events = BarcodeEvent.objects.order_by('-created_at')[:1000]  # or filter by date
    html = render_to_string('scanner/event_list_pdf.html', {'events': events})
    buffer = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(html.encode('utf-8')), dest=buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True,
                        filename='wms_events.pdf')

def import_report(request):
    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            rpt = form.save()
            # optional: parse the PDF with PyPDF2 here...
            return redirect('event_list')
    return redirect('event_list')

# Render index (ensure CSRF cookie is set)
@ensure_csrf_cookie
def index(request):
    return render(request, 'scanner/index.html')

@require_http_methods(["GET", "POST", "DELETE"])
def api_router(request):
    action = request.GET.get('action', '')
    # GET: getAllData
    if request.method == "GET":
        if action == 'getAllData':
            items_in = list(ItemIn.objects.order_by('-id').values())
            item_out_qs = ItemOut.objects.select_related('item_in').order_by('-id')
            item_outs = []
            for o in item_out_qs:
                d = {
                    'id': o.id,
                    'item_in_id': o.item_in_id,
                    'date_out': o.date_out.isoformat() if o.date_out else None,
                    'pic': o.pic,
                    'organic': o.organic,
                    'notes': o.notes,
                    'category': o.item_in.category,
                    'subcategory': o.item_in.subcategory,
                    'item_name': o.item_in.item_name,
                }
                item_outs.append(d)
            spareparts = list(Sparepart.objects.order_by('-id').values())
            return JsonResponse({
                'itemInData': items_in,
                'itemOutData': item_outs,
                'sparepartData': spareparts
            })
        return HttpResponseBadRequest(json.dumps({'error': 'unknown GET action'}), content_type='application/json')

    # POST: addItemIn, addItemOut, addSparepart
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode() or '{}')
        except json.JSONDecodeError:
            return HttpResponseBadRequest(json.dumps({'error': 'invalid json'}), content_type='application/json')
        if action == 'addItemIn':
            item_name = f"{data.get('category','')}-{data.get('subcategory','')}-{int(__import__('time').time())}"
            obj = ItemIn.objects.create(
                category = data.get('category',''),
                subcategory = data.get('subcategory',''),
                item_name = item_name,
                date_in = data.get('dateIn') or None,
                pic = data.get('pic',''),
                organic = data.get('organic',''),
            )
            return JsonResponse(model_to_dict(obj))
        if action == 'addItemOut':
            if 'item_in_id' not in data:
                return HttpResponseBadRequest(json.dumps({'error': 'missing item_in_id'}), content_type='application/json')
            item_in = ItemIn.objects.filter(id=data['item_in_id']).first()
            if not item_in:
                return HttpResponseBadRequest(json.dumps({'error': 'item_in not found'}), content_type='application/json')
            obj = ItemOut.objects.create(
                item_in = item_in,
                date_out = data.get('dateOut') or None,
                pic = data.get('pic',''),
                organic = data.get('organic',''),
                notes = data.get('notes',''),
            )
            # return joined representation
            resp = {
                'id': obj.id,
                'item_in_id': obj.item_in_id,
                'date_out': obj.date_out.isoformat() if obj.date_out else None,
                'pic': obj.pic,
                'organic': obj.organic,
                'notes': obj.notes,
                'category': item_in.category,
                'subcategory': item_in.subcategory,
                'item_name': item_in.item_name,
            }
            return JsonResponse(resp)
        if action == 'addSparepart':
            obj = Sparepart.objects.create(
                date = data.get('date') or None,
                item_name = data.get('item_name',''),
                qty = int(data.get('qty') or 0),
                satuan = data.get('satuan',''),
                price = data.get('price') or 0
            )
            return JsonResponse(model_to_dict(obj))
        return HttpResponseBadRequest(json.dumps({'error': 'unknown POST action'}), content_type='application/json')

    # DELETE: deleteItemIn, deleteItemOut, deleteSparepart
    if request.method == "DELETE":
        if action == 'deleteItemIn':
            _id = request.GET.get('id')
            if not _id:
                return HttpResponseBadRequest(json.dumps({'error': 'missing id'}), content_type='application/json')
            ItemOut.objects.filter(item_in_id=_id).delete()
            ItemIn.objects.filter(id=_id).delete()
            return JsonResponse({'success': True})
        if action == 'deleteItemOut':
            _id = request.GET.get('id')
            if not _id:
                return HttpResponseBadRequest(json.dumps({'error': 'missing id'}), content_type='application/json')
            ItemOut.objects.filter(id=_id).delete()
            return JsonResponse({'success': True})
        if action == 'deleteSparepart':
            _id = request.GET.get('id')
            if not _id:
                return HttpResponseBadRequest(json.dumps({'error': 'missing id'}), content_type='application/json')
            Sparepart.objects.filter(id=_id).delete()
            return JsonResponse({'success': True})
        return HttpResponseBadRequest(json.dumps({'error': 'unknown DELETE action'}), content_type='application/json')