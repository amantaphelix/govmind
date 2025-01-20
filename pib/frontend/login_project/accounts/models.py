# models.py
from django.db import models
from django.utils import timezone

class NewsArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='news_images/')
    date_posted = models.DateTimeField(default=timezone.now)
    positive_percentage = models.FloatField()
    negative_percentage = models.FloatField()
    neutral_percentage = models.FloatField()

    def __str__(self):
        return self.title

# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import NewsArticle

@login_required
def dashboard(request):
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('date', '')
    sentiment_filter = request.GET.get('sentiment', '')
    
    articles = NewsArticle.objects.all()
    
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        )
    
    if date_filter:
        articles = articles.filter(date_posted__date=date_filter)
    
    if sentiment_filter == 'positive':
        articles = articles.filter(positive_percentage__gt=50)
    elif sentiment_filter == 'negative':
        articles = articles.filter(negative_percentage__gt=50)
    elif sentiment_filter == 'neutral':
        articles = articles.filter(neutral_percentage__gt=50)
    
    context = {
        'articles': articles,
    }
    return render(request, 'dashboard.html', context)

@login_required
def article_detail(request, article_id):
    article = get_object_or_404(NewsArticle, id=article_id)
    return render(request, 'article_detail.html', {'article': article})

# urls.py (add to existing urls.py)
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
]