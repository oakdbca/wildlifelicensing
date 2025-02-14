from django.conf import settings
from django.core.cache import cache
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from ledger_api_client.managed_models import SystemGroup


def superuser_ids_list() -> list:
    cache_key = settings.CACHE_KEY_SUPERUSER_IDS
    superuser_ids = cache.get(cache_key)
    if superuser_ids is None:
        superuser_ids = list(
            EmailUser.objects.filter(is_superuser=True).values_list("id", flat=True)
        )
        cache.set(cache_key, superuser_ids, settings.CACHE_TIMEOUT_5_SECONDS)
    return superuser_ids


def belongs_to_by_user_id(user_id: int, group_name: str) -> bool:
    superuser_ids = superuser_ids_list()
    if superuser_ids and user_id in superuser_ids:
        return True
    cache_key = settings.CACHE_KEY_USER_BELONGS_TO_GROUP.format(
        **{"user_id": user_id, "group_name": group_name}
    )
    belongs_to = cache.get(cache_key)
    if belongs_to is None:
        system_group = SystemGroup.objects.filter(name=group_name).first()
        belongs_to = (
            system_group and user_id in system_group.get_system_group_member_ids()
        )
        cache.set(cache_key, belongs_to, settings.CACHE_TIMEOUT_5_SECONDS)
    return belongs_to


# TODO: Change to Ledger api client System Groups
def belongs_to(user: EmailUser, group_name: str) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    return belongs_to_by_user_id(user.id, group_name)


def is_customer(user):
    """
    Test if the user is a customer
    Rules:
        Not an officer
    :param user:
    :return:
    """
    return user.is_authenticated and not is_officer(user) and not is_assessor(user)


def is_officer(user):
    """
    Test if user is an WL Officer
    Rules:
        Must belongs to group Officers
    :param user:
    :return:
    """
    return belongs_to(user, settings.GROUP_NAME_OFFICERS)


def is_assessor(user):
    """
    Test if user is an WL Assessors
    Rules:
        Must belongs to group Assessors
    :param user:
    :return:
    """
    return belongs_to(user, settings.GROUP_NAME_OFFICERS)


def get_all_officers():
    return EmailUser.objects.filter(groups__name=settings.GROUP_NAME_OFFICERS)


def get_all_assessors():
    return EmailUser.objects.filter(groups__name=settings.GROUP_NAME_ASSESSORS)


def get_user_assessor_groups(user):
    return user.assessorgroup_set.all()


def render_user_name(user, first_name_first=True):
    """
    Last name, Given name(s) or Last name, Given name(s) or just email if there are no given or last name
    :param first_name_first:
    :param user:
    :return:
    """
    result = ""
    if user is not None:
        if user.last_name or user.first_name:
            format_ = "{first} {last}" if first_name_first else "{last}, {first}"
            result = format_.format(first=user.first_name, last=user.last_name)
        else:
            result = f"{user.email}"
    return result
