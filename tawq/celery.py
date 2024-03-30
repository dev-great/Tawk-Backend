from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
# from post.tasks import publish_scheduled_posts


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tawq.settings')
app = Celery('tawq')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-scheduled-posts-every-minute': {
        'task': 'post.tasks.publish_scheduled_posts',
        'schedule': crontab(),
    },
}


# app.tasks.register(publish_scheduled_posts)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
