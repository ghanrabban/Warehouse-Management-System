import os
from django.core.management.base import BaseCommand
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from scanner.models import BarcodeEvent
import random

class Command(BaseCommand):
    help = "Generate a barcode image (EAN‑13 or Code128), save it in a dedicated folder, and log the event."

    def add_arguments(self, parser):
        parser.add_argument(
            'type', choices=['ean13', 'code128'],
            help='Barcode type: ean13 or code128'
        )
        parser.add_argument(
            '--data', '-d',
            help='Data string to encode (random if omitted)'
        )
        parser.add_argument(
            '--output', '-o', default='barcode',
            help='Output filename without extension'
        )
        parser.add_argument(
            '--format', '-f', choices=['png', 'svg'], default='png',
            help='Output format: png (requires Pillow) or svg'
        )
        parser.add_argument(
            '--folder', '-F', default='generated_barcodes',
            help='Folder to save generated barcode images'
        )

    def handle(self, *args, **options):
        btype = options['type']
        data = options.get('data') or self._random_data(btype)
        output_name = options['output']
        fmt = options['format']
        folder = options['folder']

        # Validate EAN‑13
        if btype == 'ean13' and (not data.isdigit() or len(data) != 12):
            self.stderr.write(self.style.ERROR("EAN‑13 requires exactly 12 digits."))
            return

        # Ensure output folder exists
        os.makedirs(folder, exist_ok=True)

        self.stdout.write(f"Generating {btype} barcode for: {data}")
        writer = None
        if fmt == 'png':
            try:
                writer = ImageWriter()
            except ImportError:
                self.stdout.write(self.style.WARNING("Pillow not installed; falling back to SVG."))
                writer = None

        BarcodeCls = get_barcode_class(btype)
        barcode_obj = BarcodeCls(data, writer=writer)
        # Save into the designated folder
        file_path = os.path.join(folder, output_name)
        fname = barcode_obj.save(file_path)
        ext = '.png' if writer else '.svg'
        full_path = fname + ext
        self.stdout.write(self.style.SUCCESS(f"Saved barcode to {full_path}"))

        # Log to database
        BarcodeEvent.objects.create(code=data, source=BarcodeEvent.GEN)
        self.stdout.write(self.style.SUCCESS(f"Logged event for: {data}"))

    def _random_data(self, btype):
        if btype == 'ean13':
            data = ''.join(str(random.randint(0,9)) for _ in range(12))
        else:  # code128
            choices = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            data = ''.join(random.choice(choices) for _ in range(10))
        self.stdout.write(f"Using random data: {data}")
        return data