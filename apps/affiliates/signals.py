from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.users.models import User, Profile
from .models import AffiliateNode
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Profile)
def create_affiliate_node_on_profile_save(sender, instance, created, **kwargs):
    """
    Create AffiliateNode when Profile is saved.
    This fires AFTER referred_by is set, fixing the race condition
    where the User post_save fired before referred_by was populated.
    """
    user = instance.user

    # Only create if node doesn't exist yet
    if AffiliateNode.objects.filter(user=user).exists():
        # Node exists — update parent if referred_by was just set
        if instance.referred_by:
            try:
                node = AffiliateNode.objects.get(user=user)
                if node.parent is None:
                    try:
                        parent_node = AffiliateNode.objects.get(user=instance.referred_by)
                        node.parent = parent_node
                        node.depth = parent_node.depth + 1
                        node.save()
                        logger.info(
                            f'Updated affiliate node parent: {user.email} -> {instance.referred_by.email}'
                        )
                        # Update referrer's total_referrals count
                        Profile.objects.filter(user=instance.referred_by).update(
                            total_referrals=Profile.objects.get(
                                user=instance.referred_by
                            ).total_referrals + 1
                        )
                    except AffiliateNode.DoesNotExist:
                        logger.warning(
                            f'No affiliate node found for referrer {instance.referred_by.email}'
                        )
            except AffiliateNode.DoesNotExist:
                pass
        return

    # Create new node
    parent_node = None
    if instance.referred_by:
        try:
            parent_node = AffiliateNode.objects.get(user=instance.referred_by)
        except AffiliateNode.DoesNotExist:
            logger.warning(
                f'Referrer {instance.referred_by.email} has no affiliate node yet'
            )

    depth = (parent_node.depth + 1) if parent_node else 0

    AffiliateNode.objects.create(
        user=user,
        parent=parent_node,
        depth=depth,
        is_active=True,
    )

    logger.info(
        f'Created affiliate node for {user.email}, depth={depth}, '
        f'parent={parent_node.user.email if parent_node else "none"}'
    )