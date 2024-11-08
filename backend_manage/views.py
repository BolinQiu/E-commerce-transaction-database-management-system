from django.shortcuts import render

# Create your views here.
def app_index(request):
    return render(request, 'manage.html')
