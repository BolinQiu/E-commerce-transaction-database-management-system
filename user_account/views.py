from django.shortcuts import render

# Create your views here.

def app_index(request):
    return render(request, 'user_account/index.html')