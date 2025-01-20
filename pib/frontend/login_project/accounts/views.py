from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required 
from django.contrib import messages
import logging
logger = logging.getLogger(__name__)
def login_view(request):
    logger.debug("Trying to render template: accounts/login.html")
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to a home page after login
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')

def dashboard(request):
    return render(request, 'accounts/dashboard.html') 
def home_view(request):
    return render(request, 'home.html')
def signup_view(request):
    # Your signup logic
    return render(request, 'accounts/signup.html')
