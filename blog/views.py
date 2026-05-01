from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import BlogPost, Portfolio, Category, Profile, Comment, PageView, SiteSettings, ProjectImage, Lead, NewsletterSubscriber
from .forms import (
    UserRegistrationForm, LoginForm, BlogPostForm, PortfolioForm,
    CategoryForm, ProfileForm, CommentForm, UserProfileForm, SiteSettingsForm,
    ProjectImageForm, LeadForm, NewsletterForm
)
import json


def is_admin(user):
    return user.is_authenticated and user.is_staff


def track_page_view(request):
    PageView.objects.create(
        url=request.get_full_path(),
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )


def custom_login(request):
    next_url = request.GET.get('next', 'home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'blog/login.html', {'form': form, 'next': next_url})


def custom_register(request):
    next_url = request.GET.get('next', 'home')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to DesignStudio.')
            return redirect(next_url)
    else:
        form = UserRegistrationForm()
    return render(request, 'blog/register.html', {'form': form, 'next': next_url})


def custom_logout(request):
    if request.user.is_staff:
        logout(request)
        messages.success(request, 'Logged out successfully.')
    return redirect('home')


def home(request):
    track_page_view(request)
    posts = BlogPost.objects.filter(is_published=True)[:5]
    portfolio = Portfolio.objects.filter(is_featured=True)[:5]
    try:
        profile = Profile.objects.first()
    except Profile.DoesNotExist:
        profile = None
    newsletter_form = NewsletterForm()
    lead_form = LeadForm()
    return render(request, 'blog/home.html', {
        'posts': posts, 'portfolio': portfolio, 'profile': profile,
        'newsletter_form': newsletter_form, 'lead_form': lead_form
    })


def blog_list(request):
    track_page_view(request)
    posts = BlogPost.objects.filter(is_published=True)
    if request.user.is_staff:
        query = request.GET.get('q')
        category = request.GET.get('category')
        if query:
            posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
        if category:
            posts = posts.filter(category__slug=category)
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    posts_page = paginator.get_page(page_number)
    categories = Category.objects.filter(blog_posts__is_published=True).distinct()
    return render(request, 'blog/blog_list.html', {'posts': posts_page, 'categories': categories})


def blog_detail(request, slug):
    track_page_view(request)
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    if not post.views:
        post.views = 0
    post.views += 1
    post.save(update_fields=['views'])
    comments = post.comments.filter(is_approved=True)
    liked = False
    if request.user.is_authenticated and not request.user.is_staff:
        liked = post.likes.filter(id=request.user.id).exists()
        if request.method == 'POST' and 'comment' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.blog_post = post
                comment.name = request.user.get_full_name() or request.user.username
                comment.email = request.user.email
                comment.save()
                messages.success(request, 'Comment submitted for review.')
                return redirect('blog_detail', slug=slug)
        else:
            form = CommentForm()
    else:
        form = None
    return render(request, 'blog/blog_detail.html', {'post': post, 'comments': comments, 'form': form, 'liked': liked})


@require_POST
@login_required
def blog_like(request, slug):
    if request.user.is_staff:
        return JsonResponse({'error': 'Admin cannot like posts'}, status=403)
    post = get_object_or_404(BlogPost, slug=slug)
    if request.user.likes.filter(id=post.id).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return JsonResponse({'likes': post.total_likes(), 'liked': request.user in post.likes.all()})


@require_POST
def blog_share(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    post.shares += 1
    post.save(update_fields=['shares'])
    return JsonResponse({'shares': post.shares})


@require_POST
def portfolio_share(request, slug):
    item = get_object_or_404(Portfolio, slug=slug)
    item.shares += 1
    item.save(update_fields=['shares'])
    return JsonResponse({'shares': item.shares})


@user_passes_test(is_admin)
def blog_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blog post created successfully.')
            return redirect('blog_list')
    else:
        form = BlogPostForm()
    return render(request, 'blog/blog_form.html', {'form': form, 'action': 'Create'})


@user_passes_test(is_admin)
def blog_update(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blog post updated successfully.')
            return redirect('blog_detail', slug=post.slug)
    else:
        form = BlogPostForm(instance=post)
    return render(request, 'blog/blog_form.html', {'form': form, 'action': 'Edit'})


@user_passes_test(is_admin)
def blog_delete(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Blog post deleted successfully.')
        return redirect('blog_list')
    return render(request, 'blog/blog_confirm_delete.html', {'post': post})


def portfolio_list(request):
    track_page_view(request)
    items = Portfolio.objects.all()
    if request.user.is_staff:
        query = request.GET.get('q')
        category = request.GET.get('category')
        if query:
            items = items.filter(Q(title__icontains=query) | Q(description__icontains=query))
        if category:
            items = items.filter(category__slug=category)
    paginator = Paginator(items, 5)
    page_number = request.GET.get('page')
    items_page = paginator.get_page(page_number)
    categories = Category.objects.filter(Q(portfolio_items__isnull=False)).distinct()
    return render(request, 'blog/portfolio_list.html', {'items': items_page, 'categories': categories})


def portfolio_detail(request, slug):
    track_page_view(request)
    item = get_object_or_404(Portfolio, slug=slug)
    if not item.views:
        item.views = 0
    item.views += 1
    item.save(update_fields=['views'])
    gallery = item.additional_images.all()
    return render(request, 'blog/portfolio_detail.html', {'item': item, 'gallery': gallery})


@user_passes_test(is_admin)
def portfolio_create(request):
    if request.method == 'POST':
        form = PortfolioForm(request.POST, request.FILES)
        if form.is_valid():
            portfolio = form.save()
            images = request.FILES.getlist('additional_images')
            for img in images:
                ProjectImage.objects.create(portfolio=portfolio, image=img)
            messages.success(request, 'Portfolio item created successfully.')
            return redirect('portfolio_list')
    else:
        form = PortfolioForm()
    return render(request, 'blog/portfolio_form.html', {'form': form, 'action': 'Create'})


@user_passes_test(is_admin)
def portfolio_update(request, slug):
    item = get_object_or_404(Portfolio, slug=slug)
    if request.method == 'POST':
        form = PortfolioForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            images = request.FILES.getlist('additional_images')
            for img in images:
                ProjectImage.objects.create(portfolio=item, image=img)
            messages.success(request, 'Portfolio item updated successfully.')
            return redirect('portfolio_detail', slug=item.slug)
    else:
        form = PortfolioForm(instance=item)
    gallery_images = item.additional_images.all()
    return render(request, 'blog/portfolio_form.html', {'form': form, 'action': 'Edit', 'gallery_images': gallery_images})


@user_passes_test(is_admin)
def portfolio_image_delete(request, pk):
    image = get_object_or_404(ProjectImage, pk=pk)
    portfolio_slug = image.portfolio.slug
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image deleted.')
    return redirect('portfolio_update', slug=portfolio_slug)


@user_passes_test(is_admin)
def portfolio_delete(request, slug):
    item = get_object_or_404(Portfolio, slug=slug)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Portfolio item deleted successfully.')
        return redirect('portfolio_list')
    return render(request, 'blog/portfolio_confirm_delete.html', {'item': item})


def lead_submit(request):
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Thank you! We will contact you soon.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return redirect('home')


def newsletter_subscribe(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Subscribed successfully!')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return redirect('home')


@user_passes_test(is_admin)
def comment_list(request):
    comments = Comment.objects.all().order_by('-created_at')
    paginator = Paginator(comments, 10)
    page_number = request.GET.get('page')
    comments_page = paginator.get_page(page_number)
    return render(request, 'blog/comment_list.html', {'comments': comments_page})


@user_passes_test(is_admin)
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.is_approved = True
    comment.save()
    messages.success(request, 'Comment approved.')
    return redirect('comment_list')


@user_passes_test(is_admin)
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted.')
    return redirect('comment_list')


@user_passes_test(is_admin)
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile_view')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'blog/profile_form.html', {'form': form, 'profile': profile})


@user_passes_test(is_admin)
def category_list(request):
    categories = Category.objects.annotate(blog_count=Count('blog_posts'), portfolio_count=Count('portfolio_items'))
    return render(request, 'blog/category_list.html', {'categories': categories})


@user_passes_test(is_admin)
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'blog/category_form.html', {'form': form, 'action': 'Create'})


@user_passes_test(is_admin)
def category_update(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'blog/category_form.html', {'form': form, 'action': 'Edit'})


@user_passes_test(is_admin)
def category_delete(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('category_list')
    return render(request, 'blog/category_confirm_delete.html', {'category': category})


@user_passes_test(is_admin)
def analytics_dashboard(request):
    total_posts = BlogPost.objects.count()
    total_portfolio = Portfolio.objects.count()
    total_comments = Comment.objects.count()
    approved_comments = Comment.objects.filter(is_approved=True).count()
    pending_comments = Comment.objects.filter(is_approved=False).count()
    total_views = sum(p.views or 0 for p in BlogPost.objects.all()) + sum(p.views or 0 for p in Portfolio.objects.all())
    total_likes = sum(p.total_likes() for p in BlogPost.objects.all())
    total_shares = sum(p.shares for p in BlogPost.objects.all()) + sum(p.shares for p in Portfolio.objects.all())
    total_leads = Lead.objects.count()
    total_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
    popular_posts = BlogPost.objects.order_by('-views')[:5]
    popular_portfolio = Portfolio.objects.order_by('-views')[:5]
    recent_leads = Lead.objects.order_by('-created_at')[:5]
    top_categories = Category.objects.annotate(
        blog_count=Count('blog_posts'),
        portfolio_count=Count('portfolio_items')
    ).order_by('-blog_count')[:5]
    context = {
        'total_posts': total_posts,
        'total_portfolio': total_portfolio,
        'total_comments': total_comments,
        'approved_comments': approved_comments,
        'pending_comments': pending_comments,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_shares': total_shares,
        'total_leads': total_leads,
        'total_subscribers': total_subscribers,
        'popular_posts': popular_posts,
        'popular_portfolio': popular_portfolio,
        'recent_leads': recent_leads,
        'top_categories': top_categories,
    }
    return render(request, 'blog/analytics.html', context)


@user_passes_test(is_admin)
def leads_list(request):
    leads = Lead.objects.all().order_by('-created_at')
    paginator = Paginator(leads, 10)
    page_number = request.GET.get('page')
    leads_page = paginator.get_page(page_number)
    return render(request, 'blog/leads_list.html', {'leads': leads_page})


@user_passes_test(is_admin)
def lead_mark_contacted(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    lead.is_contacted = True
    lead.save()
    messages.success(request, 'Lead marked as contacted.')
    return redirect('leads_list')


@user_passes_test(is_admin)
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        lead.delete()
        messages.success(request, 'Lead deleted.')
    return redirect('leads_list')


@user_passes_test(is_admin)
def site_settings_view(request):
    settings = SiteSettings.get_settings()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site settings updated successfully.')
            return redirect('site_settings')
    else:
        form = SiteSettingsForm(instance=settings)
    return render(request, 'blog/site_settings.html', {'form': form})


@login_required
def user_profile_view(request):
    if request.user.is_staff:
        return redirect('profile_view')
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()
            profile.phone = form.cleaned_data['phone_number']
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'phone_number': profile.phone,
        })
    return render(request, 'blog/user_profile.html', {'form': form})
