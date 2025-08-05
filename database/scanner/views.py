from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from .models import BarcodeEvent
from .forms import GenerateBarcodeForm, ManualInputForm

# You’ll want to parameterize port & baud, but hard‑coding for now:
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE   = 9600

def today_roster(request):
    today = timezone.localdate()
    rosters = DailyRoster.objects.filter(date=today)
    return render(request, 'scanner/today_roster.html', {'rosters': rosters})

def event_list(request):
    events = BarcodeEvent.objects.order_by("-created_at")[:50]
    return render(request, "scanner/event_list.html", {"events": events})

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