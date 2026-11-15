from django.conf import settings

def is_ip_allowed(ip_address):
    allowed_subnets = getattr(settings, 'ALLOWED_OFFICE_SUBNETS', ['127.0.0.1'])
    for subnet in allowed_subnets:
        if ip_address and ip_address.startswith(subnet):
            return True
    return False

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
