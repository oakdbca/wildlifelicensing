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
    help = 'Migrate identification of EmailUser to temporary folder'

    def handle(self, *args, **options):

        errors=[]
        updates=[]
        TEMP_DIR ='/temp'

        import os
        from wildlifelicensing.settings import BASE_DIR
        save_dir =BASE_DIR + TEMP_DIR

        logger.info('Running command {}'.format(__name__))

        qs=EmailUser.objects.filter(identification__isnull=False)
        if not os.path.exists(save_dir):
                os.makedirs(save_dir, mode=0o777)
        if os.path.exists(save_dir):
            for user in qs:
                try:
                    if user.identification and user.identification.file and os.path.exists(user.identification.file.path): 
                        id_doc=user.identification
                        ext=os.path.splitext(id_doc.file.name)[1]
                        file_path = os.path.join(save_dir, '{}_{}{}'.format(user.id, 'identification', ext))
                        with open(file_path, 'wb+') as fp:
                            for chunk in id_doc.file.chunks():
                                fp.write(chunk)
                        updates.append(user.id)
                except Exception as e:
                    err_msg = 'Error copying Identification doc for EmailUser {}'.format(user.id)
                    logger.error('{}\n{}'.format(err_msg, str(e)))
                    errors.append(err_msg)
        
        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(errors)>0 else '<strong style="color: green;">Errors: 0</strong>'
        msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        logger.info(msg)
        print(msg) # will redirect to cron_tasks.log file, by the parent script




