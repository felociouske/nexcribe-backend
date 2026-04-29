from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.affiliates.models import AffiliateNode
from .models import User, Profile, AccountWallet, YieldsWallet, DepositWallet, CashbackWallet, VirtualCard


@receiver(post_save, sender=User)
def create_user_resources(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
        AccountWallet.objects.get_or_create(user=instance)
        YieldsWallet.objects.get_or_create(user=instance)
        DepositWallet.objects.get_or_create(user=instance)
        CashbackWallet.objects.get_or_create(user=instance)
        VirtualCard.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def create_affiliate_node(sender, instance, created, **kwargs):
    if created:
        parent = None

        # get referrer (if exists)
        if hasattr(instance, 'profile') and instance.profile.referred_by:
            try:
                parent = AffiliateNode.objects.get(user=instance.profile.referred_by)
            except AffiliateNode.DoesNotExist:
                parent = None

        AffiliateNode.objects.get_or_create(
            user=instance,
            defaults={
                'parent': parent,
                'depth': (parent.depth + 1) if parent else 0
            }
        )