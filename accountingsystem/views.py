#coding:utf-8
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .utils.RawFiles import delete_uploaded_file, get_uploaded_file


def index(request):
    return HttpResponse("Hi there. You're at the index page of our Accounting System.")


@require_http_methods(["DELETE"])
@csrf_exempt # TODO: for test，若未加這行，使用 postman 測試 post 時，會報 403，因為沒有 CSRF token
def delete_file(request, comp_id, rpt_id, acc_id, table_name):
    result = delete_uploaded_file(rpt_id, table_name)
    return HttpResponse(result) # TODO: for test


def get_import_page(request,comp_id, rpt_id, acc_id):
    return render (request,'<<import_page.html>>',{ 'acc_id': acc_id})
