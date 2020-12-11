from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def get_import_page(request,comp_id, rpt_id, acc_id):
    return render (request,'<<匯入頁面 HTML 位置>>',{ 'acc_id': acc_id})

