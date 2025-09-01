from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Shift(models.TextChoices):
    DAY   = 'day',   'Day'
    NIGHT = 'night', 'Night'

class DailyRoster(models.Model):
    """
    Assigns which users are on which shift for a given date.
    """
    date     = models.DateField()
    shift    = models.CharField(max_length=10, choices=Shift.choices)
    users    = models.ManyToManyField(User, related_name='rosters')

    class Meta:
        unique_together = ('date','shift')
        ordering = ['-date','shift']

    def __str__(self):
        return f"{self.date:%d/%m/%Y} – {self.get_shift_display()} Shift"

class BarcodeEvent(models.Model):
    SCAN, MANUAL, GEN = 'scan','manual','gen'
    SOURCE_CHOICES = [
      (SCAN,'Scan'),
      (MANUAL,'Manual'),
      (GEN,'Generated'),
    ]

    code       = models.CharField(max_length=128)
    source     = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    # new audit fields:
    user       = models.ForeignKey(User, null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   help_text="Who performed this action")
    shift      = models.CharField(max_length=10,
                                  choices=Shift.choices,
                                  default=Shift.DAY,
                                  help_text="Shift at time of event",
                                  editable=False)

    def save(self, *args, **kwargs):
        # If user not set, attempt to pull from thread‑local request
        try:
            from django_currentuser.middleware import get_current_user
            self.user = get_current_user()
        except ImportError:
            pass

        # Determine shift by hour if not set
        if not self.shift:
            hour = self.created_at.hour if self.created_at else timezone.now().hour
            self.shift = Shift.DAY if 6 <= hour < 18 else Shift.NIGHT

        super().save(*args, **kwargs)

class Report(models.Model):
    file = models.FileField(upload_to='reports/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report {self.id} @ {self.uploaded_at:%Y-%m-%d %H:%M}"

class ItemIn(models.Model):
    category = models.CharField(max_length=200)
    subcategory = models.CharField(max_length=200, blank=True)
    item_name = models.CharField(max_length=255)
    date_in = models.DateField(null=True, blank=True)
    pic = models.CharField(max_length=200, blank=True)
    organic = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_name} ({self.pk})"

class ItemOut(models.Model):
    item_in = models.ForeignKey(ItemIn, on_delete=models.CASCADE, related_name='outs')
    date_out = models.DateField(null=True, blank=True)
    pic = models.CharField(max_length=200, blank=True)
    organic = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Out {self.pk} -> {self.item_in_id}"

class Sparepart(models.Model):
    date = models.DateField(null=True, blank=True)
    item_name = models.CharField(max_length=255)
    qty = models.IntegerField(default=1)
    satuan = models.CharField(max_length=64, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_name} ({self.qty})"

