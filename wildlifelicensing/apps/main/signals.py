import django.dispatch
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from wildlifelicensing.apps.main.models import (
    Address,
    Country,
    EmailIdentity,
    Profile,
    UserAddress,
)

identification_uploaded = django.dispatch.Signal()

licence_issued = django.dispatch.Signal()


@receiver(post_delete, sender=Profile)
def profile_post_delete(sender, instance, **kwargs):
    # delete from email identity, and social auth
    if instance.user.email == instance.email:
        # profile's email is user's email, return
        return

    # delete the profile's email from email identity and social auth
    EmailIdentity.objects.filter(email=instance.email, user=instance.user).delete()


@receiver(pre_save, sender=Profile)
def profile_pre_save(sender, instance, **kwargs):
    if not hasattr(instance, "auth_identity"):
        # not triggered by user.
        return

    if instance.pk:
        original_instance = Profile.objects.get(pk=instance.pk)
        setattr(instance, "_original_instance", original_instance)
    elif hasattr(instance, "_original_instance"):
        delattr(instance, "_original_instance")


@receiver(post_save, sender=Profile)
def profile_post_save(sender, instance, **kwargs):
    print(" --- > profile_post_save")
    if not hasattr(instance, "auth_identity"):
        # not triggered by user.
        return

    original_instance = (
        getattr(instance, "_original_instance")
        if hasattr(instance, "_original_instance")
        else None
    )
    auth_identity = getattr(instance, "auth_identity")
    if auth_identity:
        # add email to email identity and social auth if not exist
        EmailIdentity.objects.get_or_create(email=instance.email, user=instance.user)

    if original_instance and (
        original_instance.email != instance.email or not auth_identity
    ):
        # delete the profile's email from email identity and social auth
        EmailIdentity.objects.filter(
            email=original_instance.email, user=original_instance.user
        ).delete()

    if not original_instance:
        address = instance.postal_address
        try:
            # Check if the user has the same profile address
            # Check if there is a user address
            oscar_add = UserAddress.objects.get(
                line1=address.line1,
                line2=address.line2,
                line3=address.line3,
                line4=address.locality,
                state=address.state,
                postcode=address.postcode,
                country=Country.objects.get(iso_3166_1_a2=address.country),
                user=instance.user,
            )
            if not address.oscar_address:
                address.oscar_address = oscar_add
                address.save()
            elif address.oscar_address.id != oscar_add.id:
                address.oscar_address = oscar_add
                address.save()
        except UserAddress.DoesNotExist:
            oscar_address = UserAddress.objects.create(
                line1=address.line1,
                line2=address.line2,
                line3=address.line3,
                line4=address.locality,
                state=address.state,
                postcode=address.postcode,
                country=Country.objects.get(iso_3166_1_a2=address.country),
                user=instance.user,
            )
            address.oscar_address = oscar_address
            address.save()
    # Clear out unused addresses
    # EmailUser can have address that is not linked with profile, hence the exclude
    """ This functionality no longer in use due to more than just
    profile objects using the UserAddresses
    user = instance.user
    user_addr = Address.objects.filter(user=user)
    for u in user_addr:
        if not u.profiles.all() \
            and not u in (user.postal_address, user.residential_address, user.billing_address):
            u.oscar_address.delete()
            u.delete()"""


@receiver(pre_save, sender=Address)
def address_pre_save(sender, instance, **kwargs):
    check_address = UserAddress(
        line1=instance.line1,
        line2=instance.line2,
        line3=instance.line3,
        line4=instance.locality,
        state=instance.state,
        postcode=instance.postcode,
        country=Country.objects.get(iso_3166_1_a2=instance.country),
        user=instance.user,
    )
    if instance.pk:
        original_instance = Address.objects.get(pk=instance.pk)
        setattr(instance, "_original_instance", original_instance)
        if original_instance.oscar_address is None:
            try:
                check_address = UserAddress.objects.get(
                    hash=check_address.generate_hash(), user=check_address.user
                )
            except UserAddress.DoesNotExist:
                check_address.save()
            instance.oscar_address = check_address
    elif hasattr(instance, "_original_instance"):
        delattr(instance, "_original_instance")
    else:
        try:
            check_address = UserAddress.objects.get(
                hash=check_address.generate_hash(), user=check_address.user
            )
        except UserAddress.DoesNotExist:
            check_address.save()
        instance.oscar_address = check_address


@receiver(post_save, sender=Address)
def address__post_save(sender, instance, **kwargs):
    original_instance = (
        getattr(instance, "_original_instance")
        if hasattr(instance, "_original_instance")
        else None
    )
    if original_instance:
        oscar_address = original_instance.oscar_address
        try:
            if oscar_address is not None:
                oscar_address.line1 = instance.line1
                oscar_address.line2 = instance.line2
                oscar_address.line3 = instance.line3
                oscar_address.line4 = instance.locality
                oscar_address.state = instance.state
                oscar_address.postcode = instance.postcode
                oscar_address.country = Country.objects.get(
                    iso_3166_1_a2=instance.country
                )
                oscar_address.save()
        except IntegrityError as e:
            if "unique constraint" in e.message:
                raise ValidationError("Multiple profiles cannot have the same address.")
            else:
                raise
