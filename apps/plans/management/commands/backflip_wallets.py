"""
Run once after adding DepositWallet and CashbackWallet models
to create missing wallet rows for all existing users.

Usage:
    python manage.py backfill_wallets
"""
from django.core.management.base import BaseCommand
from apps.users.models import (
    User, AccountWallet, YieldsWallet, DepositWallet, CashbackWallet, Profile
)


class Command(BaseCommand):
    help = 'Create missing wallet and profile rows for all existing users.'

    def handle(self, *args, **options):
        users = User.objects.all()
        total = users.count()
        self.stdout.write(f'Backfilling wallets for {total} users...')

        account_created = 0
        yields_created = 0
        deposit_created = 0
        cashback_created = 0
        profile_created = 0

        for user in users:
            _, c = AccountWallet.objects.get_or_create(user=user)
            if c:
                account_created += 1

            _, c = YieldsWallet.objects.get_or_create(user=user)
            if c:
                yields_created += 1

            _, c = DepositWallet.objects.get_or_create(user=user)
            if c:
                deposit_created += 1

            _, c = CashbackWallet.objects.get_or_create(user=user)
            if c:
                cashback_created += 1

            _, c = Profile.objects.get_or_create(user=user)
            if c:
                profile_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done.\n'
            f'  AccountWallet created:  {account_created}\n'
            f'  YieldsWallet created:   {yields_created}\n'
            f'  DepositWallet created:  {deposit_created}\n'
            f'  CashbackWallet created: {cashback_created}\n'
            f'  Profile created:        {profile_created}\n'
            f'  Total users processed:  {total}'
        ))