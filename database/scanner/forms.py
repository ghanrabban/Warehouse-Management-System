from django import forms
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from .models import BarcodeEvent
import os, random

class GenerateBarcodeForm(forms.Form):
    TYPE_CHOICES = [("ean13","EAN-13"), ("code128","Code128")]
    btype   = forms.ChoiceField(choices=TYPE_CHOICES, help_text="Select barcode type.")
    data    = forms.CharField(
        required=False,
        help_text="Enter barcode data (leave blank to auto-generate)."
    )
    format  = forms.ChoiceField(
        choices=[("png","PNG"),("svg","SVG")],
        initial="png",
        help_text="Choose output format. PNG requires Pillow."
    )
    folder  = forms.CharField(
        initial="generated_barcodes",
        help_text="Folder where barcode images will be saved."
    )

    def create_barcode(self):
        btype = self.cleaned_data["btype"]
        data  = self.cleaned_data["data"] or self._random_data(btype)
        fmt   = self.cleaned_data["format"]
        folder= self.cleaned_data["folder"]
        os.makedirs(folder, exist_ok=True)

        writer = ImageWriter() if fmt == "png" else None
        BarcodeCls = get_barcode_class(btype)
        barcode_obj = BarcodeCls(data, writer=writer)
        filename = os.path.join(folder, data)
        saved = barcode_obj.save(filename) + (".png" if writer else ".svg")

        # Log event
        BarcodeEvent.objects.create(code=data, source=BarcodeEvent.GEN)
        return saved

    def _random_data(self, btype):
        if btype == 'ean13':
            return ''.join(str(random.randint(0,9)) for _ in range(12))
        choices = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join(random.choice(choices) for _ in range(10))

class ManualInputForm(forms.Form):
    code = forms.CharField(
        label="Barcode Number",
        max_length=128,
        help_text="Enter the barcode number manually."
    )

class ScanForm(forms.Form):
    code = forms.CharField(
        label="Scan Barcode",
        max_length=128,
        widget=forms.TextInput(attrs={"autofocus": True}),
        help_text="Use your barcode scanner to scan directly into this field."
    )