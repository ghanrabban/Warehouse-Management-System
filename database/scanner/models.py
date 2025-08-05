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
