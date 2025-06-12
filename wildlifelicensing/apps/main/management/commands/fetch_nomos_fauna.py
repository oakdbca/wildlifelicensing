
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import requests
import json

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch nomos data'

    def handle(self, *args, **options):
        #logger.info('Running command {}')
        logger.info('Running command {}'.format(__name__))

        errors = []
        updates = []
        
        my_url = settings.NOMOS_BLOB_URL
        
        # TODO replace with the fauna kingdom_id list
        kingdom_id=settings.KINGDOM
        fauna_taxon=[]

        try:
            logger.info("{}".format("Requesting NOMOS BLOB URL"))    
            total_count = 0
            count = 0
            res=requests.get(url=my_url)
            if res.status_code==200:
                logger.info("{}".format("Done Fetching NOMOS data"))
                taxon=res.json()
                try:
                    for t in taxon:
                        if t['kingdom_id'] in kingdom_id:
                            vernaculars = ' ('+', '.join(v['name'] for v in t['vernaculars'])+')' if 'vernaculars' in t and t['vernaculars']!=None else ''
                            fauna_taxon.append(t['canonical_name']+vernaculars)
                            updates.append(t['taxon_name_id'])

                            count += 1
                            if count == 1000:
                                total_count += count
                                logger.info(
                                    "{} Taxon Records fetched. Continuing...".format(total_count)
                                )
                                count = 0
                    logger.info(
                        "{} Taxon Records fetched.".format(total_count)
                    )
                    
                    with open('nomos_fauna.json', 'w', encoding="utf-8") as json_file:
                        json.dump(fauna_taxon, json_file)

                except Exception as e:
                    err_msg = 'Taxon fetch failed'
                    logger.error('{}\n{}'.format(err_msg, str(e)))
                    errors.append(err_msg)
            else:
                err_msg = 'Login failed with status code {}'.format(res.status_code)
                #logger.error('{}\n{}'.format(err_msg, str(e)))
                logger.error('{}'.format(err_msg))
                errors.append(err_msg)
        except Exception as e:
            err_msg = 'Error at the end'
            logger.error('{}\n{}'.format(err_msg, str(e)))
            errors.append(err_msg)


        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        err_str = 'Errors: {}'.format(len(errors)) if len(errors)>0 else 'Errors: 0'
        msg = 'Command {} completed. {}. IDs fetched: {}.'.format(cmd_name, err_str, updates)
        logger.info(msg)
