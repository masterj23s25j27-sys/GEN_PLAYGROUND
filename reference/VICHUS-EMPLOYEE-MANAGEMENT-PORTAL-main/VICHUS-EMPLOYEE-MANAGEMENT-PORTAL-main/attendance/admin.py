from django.contrib import admin
from .models import EmployeeProfile, DailyAttendance, PunchLog

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'qr_token')

@admin.register(DailyAttendance)
class DailyAttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'current_status', 'formatted_working_time', 'is_completed')
    list_filter = ('date', 'current_status', 'is_completed')

@admin.register(PunchLog)
class PunchLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'action', 'ip_address')
    list_filter = ('action', 'timestamp')
