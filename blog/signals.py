from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mass_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models import BlogPost, Portfolio, NewsletterSubscriber


def get_subscriber_emails():
    return list(NewsletterSubscriber.objects.filter(is_active=True).values_list('email', flat=True))


def send_notification_email(subject, content_type, instance, recipients):
    if not recipients:
        return
    try:
        from_email = settings.DEFAULT_FROM_EMAIL
        html_content = render_to_string('blog/emails/new_content.html', {
            'subject': subject,
            'content_type': content_type,
            'instance': instance,
            'site_name': 'My Service Business',
        })
        for email in recipients[:50]:
            msg = EmailMessage(
                subject=f'New {content_type}: {subject}',
                body=html_content,
                from_email=from_email,
                to=[email],
            )
            msg.content_subtype = 'html'
            msg.send(fail_silently=True)
    except Exception:
        pass


@receiver(post_save, sender=BlogPost)
def notify_blog_post_created(sender, instance, created, **kwargs):
    if created and instance.is_published:
        recipients = get_subscriber_emails()
        send_notification_email(
            instance.title,
            'Blog Post',
            instance,
            recipients
        )


@receiver(post_save, sender=Portfolio)
def notify_portfolio_created(sender, instance, created, **kwargs):
    if created:
        recipients = get_subscriber_emails()
        send_notification_email(
            instance.title,
            'New Project',
            instance,
            recipients
        )
