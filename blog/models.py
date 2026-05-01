from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=200, default='My Service Business')
    tagline = models.CharField(max_length=300, blank=True, default='Quality Expert Services')
    hero_subtext = models.TextField(blank=True, default='From plumbing to electrical work, teaching to construction showcasing skilled professionals and their outstanding work')
    logo = models.ImageField(upload_to='settings/', blank=True, null=True, help_text='Site logo (recommended: transparent PNG)')
    favicon = models.ImageField(upload_to='settings/', blank=True, null=True, help_text='Browser tab icon (32x32 PNG)')

    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]
    default_theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')

    primary_color = models.CharField(max_length=20, default='#e94560', help_text='Main brand color (hex)')
    primary_dark = models.CharField(max_length=20, default='#d63a54', help_text='Darker shade for hover')
    secondary_color = models.CharField(max_length=20, default='#16213e', help_text='Secondary brand color')
    dark_color = models.CharField(max_length=20, default='#1a1a2e', help_text='Darkest color (navy/black)')
    light_color = models.CharField(max_length=20, default='#f8f9fa', help_text='Light background color')
    text_color = models.CharField(max_length=20, default='#343a40', help_text='Primary text color')

    NAVBAR_POSITION = [
        ('top', 'Top (Default)'),
        ('bottom', 'Bottom Fixed'),
        ('left', 'Vertical Left'),
    ]
    navbar_position = models.CharField(max_length=10, choices=NAVBAR_POSITION, default='top')

    NAVBAR_WIDTH = [
        ('full', 'Full Width (100%)'),
        ('contained', 'Contained (90%)'),
    ]
    navbar_width = models.CharField(max_length=20, choices=NAVBAR_WIDTH, default='full')

    BORDER_RADIUS = [
        ('sharp', 'Sharp (0px)'),
        ('moderate', 'Moderate (6px)'),
        ('smooth', 'Smooth (12px)'),
        ('extra', 'Extra Round (20px)'),
    ]
    border_radius = models.CharField(max_length=10, choices=BORDER_RADIUS, default='smooth')

    footer_content = models.TextField(blank=True, default='Empowering skilled professionals to showcase their work and grow their business.')
    footer_links = models.TextField(blank=True, default='[{"title": "Home", "url": "/"}, {"title": "Blog", "url": "/blog/"}, {"title": "Portfolio", "url": "/portfolio/"}]', help_text='JSON array of links')
    social_links = models.TextField(blank=True, default='{"facebook": "", "instagram": "", "twitter": "", "linkedin": ""}', help_text='JSON object of social URLs')

    LEAD_CAPTURE_TEXT = [
        ('cta_text', models.CharField(max_length=200, blank=True, default='Get a Free Quote Today', help_text='Lead capture CTA text')),
    ]
    lead_cta_text = models.CharField(max_length=200, blank=True, default='Get a Free Quote Today', help_text='Lead capture CTA text')
    lead_contact_info = models.TextField(blank=True, default='We respond within 24 hours. Fast, reliable service guaranteed.', help_text='Text shown near contact/lead forms')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(default='Welcome to my creative studio.')
    cta = models.CharField(max_length=100, blank=True, help_text='Short call-to-action')
    avatar = models.ImageField(upload_to='profiles/', blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    social_links = models.TextField(help_text='JSON format: {"facebook": "url", "twitter": "url"}', blank=True, default='{}')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} Profile'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    image = models.ImageField(upload_to='blog/')
    content = models.TextField()
    video_url = models.URLField(blank=True, null=True, help_text='YouTube/Vimeo embed URL or direct video link')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    views = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def total_likes(self):
        return self.likes.count()

    def total_comments(self):
        return self.comments.filter(is_approved=True).count()

    def __str__(self):
        return self.title


class Portfolio(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    image = models.ImageField(upload_to='portfolio/', help_text='Cover image')
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='portfolio_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProjectImage(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='portfolio/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'Image for {self.portfolio.title}'


class Comment(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.name} on {self.blog_post.title}'


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email


class Lead(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    service = models.CharField(max_length=100, blank=True, help_text='Service interested in')
    message = models.TextField()
    source = models.CharField(max_length=50, blank=True, default='contact_form')
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Lead: {self.name} ({self.email})'


class PageView(models.Model):
    url = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.url} - {self.created_at}'
