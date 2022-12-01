from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import datetime
from zipfile import ZipFile
import os
from ledger.accounts.models import Document, EmailUser, PrivateDocument
import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate Senior card of EmailUser to temporary folder'

    def handle(self, *args, **options):

        errors=[]
        updates=[]
        TEMP_DIR ='/temp'

        import os
        from wildlifelicensing.settings import MEDIA_ROOT
        save_dir =MEDIA_ROOT + TEMP_DIR

        logger.info('Running command {}'.format(__name__))

        qs=EmailUser.objects.filter(senior_card__isnull=False)
        if not os.path.exists(save_dir):
                os.makedirs(save_dir, mode=0o777)
        if os.path.exists(save_dir):
            for user in qs:
                try:
                    if user.senior_card and user.senior_card.file and os.path.exists(user.senior_card.file.path): 
                        sen_card=user.senior_card
                        ext=os.path.splitext(sen_card.file.name)[1]
                        file_path = os.path.join(save_dir, '{}_{}{}'.format(user.id, 'seniorcard', ext))
                        with open(file_path, 'wb+') as fp:
                            for chunk in sen_card.file.chunks():
                                fp.write(chunk)
                        updates.append(user.id)
                except Exception as e:
                    err_msg = 'Error copying Senior card doc for EmailUser {}'.format(user.id)
                    logger.error('{}\n{}'.format(err_msg, str(e)))
                    errors.append(err_msg)
        
        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(errors)>0 else '<strong style="color: green;">Errors: 0</strong>'
        msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        logger.info(msg)
        print(msg) # will redirect to cron_tasks.log file, by the parent script




