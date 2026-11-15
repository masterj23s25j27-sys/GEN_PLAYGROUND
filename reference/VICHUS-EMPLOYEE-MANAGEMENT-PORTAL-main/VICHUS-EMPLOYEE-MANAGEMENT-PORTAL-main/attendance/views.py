from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import UserRegistrationForm
from .models import EmployeeProfile, DailyAttendance, PunchLog
from .utils import get_client_ip, is_ip_allowed

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Create profile
            EmployeeProfile.objects.create(
                user=user,
                employee_id=form.cleaned_data['employee_id'],
                role=form.cleaned_data['role']
            )
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        role_selected = request.POST.get('role', 'developer')

        user = authenticate(request, username=u, password=p)
        if user is not None:
            # Check role
            if hasattr(user, 'profile'):
                if user.profile.role != role_selected:
                    messages.error(request, f"Access denied. You do not have the '{role_selected}' role.")
                    return redirect('login')
                
                auth_login(request, user)
                if role_selected == 'management':
                    return redirect('management_dashboard')
                return redirect('dashboard')
            else:
                # Fallback for superusers lacking profile
                auth_login(request, user)
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')
    
    return render(request, 'registration/login.html')

@login_required
def dashboard(request):
    # Route guard
    if hasattr(request.user, 'profile') and request.user.profile.role == 'management':
        return redirect('management_dashboard')

    attendance, created = DailyAttendance.objects.get_or_create(
        user=request.user,
        date=timezone.localdate()
    )
    ip = get_client_ip(request)
    network_allowed = is_ip_allowed(ip)
    
    context = {
        'attendance': attendance,
        'profile': request.user.profile,
        'has_8_hours': attendance.has_at_least_8_hours,
        'network_allowed': network_allowed,
        'current_ip': ip,
    }
    return render(request, 'attendance/dashboard.html', context)

@login_required
def management_dashboard(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'management':
        messages.error(request, 'Access restricted to Management role.')
        return redirect('dashboard')

    developers = EmployeeProfile.objects.filter(role='developer').select_related('user').order_by('employee_id')
    
    date_today = timezone.localdate()
    attendance_records = DailyAttendance.objects.filter(date=date_today)
    
    # Create map: user_id -> attendance object
    att_map = {att.user_id: att for att in attendance_records}
    
    dev_data = []
    for dev in developers:
        att = att_map.get(dev.user.id)
        dev_data.append({
            'employee_id': dev.employee_id,
            'name': dev.user.username,
            'status': att.get_current_status_display() if att else 'Not Punched In Today',
            'status_raw': att.current_status if att else 'OUT',
            'working_time': att.formatted_working_time if att else '00:00:00',
            'has_8_hours': att.has_at_least_8_hours if att else False
        })

    return render(request, 'attendance/management_dashboard.html', {
        'developers': dev_data
    })

@login_required
def action_punch(request):
    """
    Handles granular developer actions using the refactored model method.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        ip = get_client_ip(request)
        
        attendance, created = DailyAttendance.objects.get_or_create(
            user=request.user,
            date=timezone.localdate()
        )
        
        if attendance.is_completed:
            messages.error(request, "You have already completed your day.")
            return redirect('dashboard')

        def log_action(act):
            PunchLog.objects.create(user=request.user, action=act, ip_address=ip)

        if action == 'PUNCH_IN':
            if not is_ip_allowed(ip):
                messages.error(request, 'Punch in failed. You are not on the office network.')
                return redirect('dashboard')
            
            if attendance.current_status == DailyAttendance.STATUS_OUT:
                attendance.change_status(DailyAttendance.STATUS_WORKING)
                log_action('IN')
                messages.success(request, 'Successfully Punched In.')

        elif action == 'BREAK_START':
            attendance.change_status(DailyAttendance.STATUS_BREAK)
            log_action('BREAK_START')
            messages.success(request, 'Break started.')

        elif action in ['RESUME_WORK', 'NEED_HELP', 'TRAINING', 'RESEARCH', 'LEARNING', 'MEETING']:
            status_map = {
                'RESUME_WORK': DailyAttendance.STATUS_WORKING,
                'NEED_HELP': DailyAttendance.STATUS_NEED_HELP,
                'TRAINING': DailyAttendance.STATUS_TRAINING,
                'RESEARCH': DailyAttendance.STATUS_RESEARCH,
                'LEARNING': DailyAttendance.STATUS_LEARNING,
                'MEETING': DailyAttendance.STATUS_MEETING,
            }
            attendance.change_status(status_map[action])
            log_action(action)
            messages.success(request, f'Status updated to: {attendance.get_current_status_display()}')

        elif action == 'PUNCH_OUT':
            if not attendance.has_at_least_8_hours:
                messages.error(request, 'Failed to Punch Out. You have not completed 8 hours of work yet.')
                return redirect('dashboard')
            
            attendance.change_status(DailyAttendance.STATUS_OUT)
            attendance.is_completed = True
            attendance.save()
            log_action('OUT')
            messages.success(request, 'Successfully Punched Out. Have a good evening!')

    return redirect('dashboard')

@login_required
def manager_update_status(request, emp_id, action):
    """
    Allows a manager to override an employee's status.
    """
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'management':
        messages.error(request, 'Unauthorized. Manager role required.')
        return redirect('dashboard')

    profile = get_object_or_404(EmployeeProfile, employee_id=emp_id)
    attendance, created = DailyAttendance.objects.get_or_create(
        user=profile.user,
        date=timezone.localdate()
    )

    status_map = {
        'WORKING': DailyAttendance.STATUS_WORKING,
        'BREAK': DailyAttendance.STATUS_BREAK,
        'OUT': DailyAttendance.STATUS_OUT,
        'MEETING': DailyAttendance.STATUS_MEETING,
    }

    if action in status_map:
        new_status = status_map[action]
        attendance.change_status(new_status)
        
        # Log that manager changed it
        ip = get_client_ip(request)
        PunchLog.objects.create(
            user=profile.user, 
            action=f"MGR_{action}", 
            ip_address=ip
        )
        messages.success(request, f'Updated status for {profile.user.username} to {attendance.get_current_status_display()}')
    else:
        messages.error(request, 'Invalid action.')

    return redirect('management_dashboard')

@login_required
def scan_qr(request, token):
    profile = get_object_or_404(EmployeeProfile, qr_token=token)
    if profile.user != request.user:
        messages.warning(request, "This QR code belongs to another employee.")
    else:
        messages.info(request, "QR Code scanned successfully.")
    return redirect('dashboard')

@login_required
def delete_employee(request, emp_id):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'management':
        messages.error(request, 'Access restricted to Management role.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        profile = get_object_or_404(EmployeeProfile, employee_id=emp_id, role='developer')
        username = profile.user.username
        profile.user.delete() # This will cascade and delete the profile and attendance
        messages.success(request, f'Employee {username} ({emp_id}) successfully removed.')
        
    return redirect('management_dashboard')

@login_required
def reset_database(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'management':
        messages.error(request, 'Access restricted to Management role.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        from django.contrib.auth.models import User
        # Delete all users who have a developer profile
        dev_users = User.objects.filter(profile__role='developer')
        count = dev_users.count()
        dev_users.delete()
        messages.success(request, f'Database Reset: Removed {count} developers.')
        
    return redirect('management_dashboard')
