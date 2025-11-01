from django.http import JsonResponse

from apps.client_apis.common import request_debug_log


# Create your views here.

@request_debug_log
def index(request):
    # cookies = request.COOKIES
    # print(cookies)
    # print(dict(cookies))
    # for key, value in cookies.items():
    #     print(f"{key}: {value}")
    return JsonResponse({'message': 'Web正在开发中'})
