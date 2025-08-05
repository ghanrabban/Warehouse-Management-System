from django.core.management.base import BaseCommand
import serial
import serial.tools.list_ports
from scanner.models import BarcodeEvent

class Command(BaseCommand):
    help = "Continuously scan barcodes from the serial port and log events."

    def add_arguments(self, parser):
        parser.add_argument(
            '--port', '-p',
            help='Serial port to use, e.g. /dev/ttyACM0 (auto-detected if omitted)'
        )

    def handle(self, *args, **options):
        # Determine serial device
        port = options['port'] or self._detect_port()
        try:
            ser = serial.Serial(port, baudrate=9600, timeout=1)
            self.stdout.write(self.style.SUCCESS(f"Connected to scanner on {port}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error opening {port}: {e}"))
            return

        buffer = ''
        try:
            self.stdout.write("Start scanning (Ctrl+C to stop)...")
            while True:
                byte = ser.read()
                if not byte:
                    continue
                if byte == b'\r':  # end of barcode
                    code = buffer.strip()
                    if code:
                        event = BarcodeEvent.objects.create(code=code, source=BarcodeEvent.SCAN)
                        self.stdout.write(f"Scanned & saved: {event.code} @ {event.created_at}")
                    buffer = ''
                else:
                    buffer += byte.decode('utf-8', errors='ignore')
        except KeyboardInterrupt:
            self.stdout.write("Stopping scan loop.")
        finally:
            ser.close()

    def _detect_port(self):
        ports = serial.tools.list_ports.comports()
        if not ports:
            raise RuntimeError("No serial ports found.")
        return ports[-1].device