from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


from .utils.RawFiles import delete_uploaded_file


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@require_http_methods(["POST"])
@csrf_exempt # TODO: for test，若未加這行，使用 postman 測試 post 時，會報 403，因為沒有 CSRF token
def delete_file(request, comp_id, rpt_id, acc_id, table_name):
    result = delete_uploaded_file(rpt_id, table_name)
    return HttpResponse(result) # TODO: for test
