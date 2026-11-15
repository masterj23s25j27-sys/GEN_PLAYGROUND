import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

class EmployeeProfile(models.fields.related.OneToOneField):
    pass # Wait, extending from OneToOneField directly is weird, I'll use composition.

# Correcting to composition
class EmployeeProfile(models.Model):
    ROLE_CHOICES = (
        ('developer', 'Developer'),
        ('management', 'Management'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    employee_id = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    qr_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Generate QR Code handling
        if not self.qr_code:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            # The QR code will contain the unique token. We'll construct the absolute URL in the view
            # but for the QR content itself, we can store just the token or a relative url.
            qr.add_data(f"/scan/{self.qr_token}/")
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            file_name = f'qr_{self.employee_id}.png'
            self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id}) - {self.role}"

class DailyAttendance(models.Model):
    """
    Maintains the state for a single day for a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    
    # States: OUT, WORKING, BREAK and extended
    STATUS_OUT = 'OUT'
    STATUS_WORKING = 'WORKING'
    STATUS_BREAK = 'BREAK'
    STATUS_NEED_HELP = 'NEED_HELP'
    STATUS_TRAINING = 'TRAINING'
    STATUS_RESEARCH = 'RESEARCH'
    STATUS_LEARNING = 'LEARNING'
    STATUS_MEETING = 'MEETING'

    STATUS_CHOICES = [
        (STATUS_OUT, 'Out'),
        (STATUS_WORKING, 'Working'),
        (STATUS_BREAK, 'Break'),
        (STATUS_NEED_HELP, 'Need Help'),
        (STATUS_TRAINING, 'Self Training'),
        (STATUS_RESEARCH, 'Research'),
        (STATUS_LEARNING, 'Learning New Topics'),
        (STATUS_MEETING, 'In Meeting'),
    ]
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OUT)
    
    # Timing
    last_status_change = models.DateTimeField(null=True, blank=True)
    accumulated_working_seconds = models.IntegerField(default=0)
    
    # For completion
    is_completed = models.BooleanField(default=False) # True when they strictly punch out for the day
    
    class Meta:
        unique_together = ('user', 'date')
        
    def total_working_seconds(self):
        # If currently in any working state (not OUT, not BREAK)
        total = self.accumulated_working_seconds
        working_states = [self.STATUS_WORKING, self.STATUS_NEED_HELP, self.STATUS_TRAINING, self.STATUS_RESEARCH, self.STATUS_LEARNING, self.STATUS_MEETING]
        if self.current_status in working_states and self.last_status_change:
            elapsed = (timezone.now() - self.last_status_change).total_seconds()
            total += elapsed
        return total

    def change_status(self, new_status):
        """
        Updates the status and handles time accumulation logic.
        """
        now = timezone.now()
        working_states = [self.STATUS_WORKING, self.STATUS_NEED_HELP, self.STATUS_TRAINING, self.STATUS_RESEARCH, self.STATUS_LEARNING, self.STATUS_MEETING]
        
        # If moving FROM a working state, accumulate the time spent in that state
        if self.current_status in working_states and self.last_status_change:
            elapsed = (now - self.last_status_change).total_seconds()
            self.accumulated_working_seconds += int(elapsed)
        
        # Update to new status
        self.current_status = new_status
        self.last_status_change = now
        
        # Special case: If punching out, check if day is completed (can be set by manager too)
        if new_status == self.STATUS_OUT:
            # We don't automatically mark is_completed here because that might have 8-hour logic
            # but usually, manual punch output sets it.
            pass

        self.save()

    @property
    def has_at_least_8_hours(self):
        return self.total_working_seconds() >= 8 * 3600
        
    @property
    def formatted_working_time(self):
        hours, remainder = divmod(self.total_working_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

class PunchLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=20) # IN, OUT, BREAK_START, BREAK_END
    ip_address = models.GenericIPAddressField(null=True, blank=True)
