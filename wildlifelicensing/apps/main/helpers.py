import logging

from django import apps
from django.conf import settings
from django.core.cache import cache
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from ledger_api_client.managed_models import SystemGroup, SystemGroupPermission

logger = logging.getLogger(__name__)


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


def belongs_to(user: EmailUser, group_name: str) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    return belongs_to_by_user_id(user.id, group_name)


def belongs_to_groups(request, group_names: list) -> bool:
    if not request.user.is_authenticated:
        return False
    if request.user.is_superuser:
        return True

    for group_name in group_names:
        if belongs_to_by_user_id(request.user.id, group_name):
            return True

    return False


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
    return belongs_to(user, settings.GROUP_NAME_ASSESSORS)


def get_all_officers():
    system_group_permissions = SystemGroupPermission.objects.filter(
        system_group__name=settings.GROUP_NAME_OFFICERS
    )
    email_user_ids = list(
        system_group_permissions.values_list("emailuser_id", flat=True)
    )
    return EmailUser.objects.filter(id__in=email_user_ids)


def get_all_assessors():
    system_group_permissions = SystemGroupPermission.objects.filter(
        system_group__name=settings.GROUP_NAME_ASSESSORS
    )
    email_user_ids = list(
        system_group_permissions.values_list("emailuser_id", flat=True)
    )
    return EmailUser.objects.filter(id__in=email_user_ids)


def get_user_assessor_groups(user):
    from wildlifelicensing.apps.main.models import AssessorGroup

    return AssessorGroup.objects.filter(members__in=[user])


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


def retrieve_email_user(email_user_id):
    if not email_user_id:
        logger.error("Needs an email_user_id to retrieve an EmailUser object")
        return None

    cache_key = settings.CACHE_KEY_LEDGER_EMAIL_USER.format(email_user_id)
    cache_timeout = settings.CACHE_TIMEOUT_10_SECONDS
    email_user = cache.get(cache_key)

    if email_user is None:
        try:
            email_user = EmailUser.objects.get(id=email_user_id)
        except EmailUser.DoesNotExist:
            logger.error(f"EmailUser with id {email_user_id} does not exist")
            # Cache an empty EmailUser object to prevent repeated queries
            cache.set(cache_key, EmailUser(), cache_timeout)
            return None
        else:
            cache.set(cache_key, email_user, cache_timeout)
            return email_user
    elif not email_user.email:
        return None
    else:
        return email_user


def retrieve_group_members(group_object, app_label="wl_main"):
    """Retrieves m2m-field members that belong to a group-object
    (single object or queryset),using the associated through model"""

    if hasattr(group_object, "_meta"):
        # group_object is a model object
        try:
            # The group object's model name
            model_name = group_object._meta.model_name
        except AttributeError:
            raise ValueError("The model object does not have a model name attribute")
        # Get the group object's Members through-model
        class_name = f"{model_name.lower()}members"
        InstanceClass = apps.get_model(app_label=app_label, model_name=f"{class_name}")

        return InstanceClass.objects.filter(
            **{f"{model_name.lower()}_id": group_object.id}
        ).values_list("emailuser_id", flat=True)
    else:
        # group_object is a QuerySet
        class_name = group_object.model.__name__
        return group_object.values_list(
            f"{class_name.lower()}_members__emailuser__id", flat=True
        )


def email_in_dbca_domain(email: str) -> bool:
    return email.split("@")[1] in settings.DEPT_DOMAINS


def in_dbca_domain(request):
    user = request.user
    if not email_in_dbca_domain(user.email):
        return False

    if not user.is_staff:
        # hack to reset department user to is_staff==True, if the user logged in externally
        # (external departmentUser login defaults to is_staff=False)
        user.is_staff = True
        user.save()

    return True


def is_departmentUser(request):
    return request.user.is_authenticated and in_dbca_domain(request)


def is_internal(request):
    return is_departmentUser(request) and (
        belongs_to_groups(request, settings.INTERNAL_GROUPS)
    )
