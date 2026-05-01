from django.core.management.base import BaseCommand
from apps.payments.models import MpesaPaymentDetails

class Command(BaseCommand):
    help = 'Create initial M-Pesa payment details'

    def handle(self, *args, **options):
        if not MpesaPaymentDetails.objects.filter(is_active=True).exists():
            MpesaPaymentDetails.objects.create(
                phone_number='0712345678',
                account_name='NEXSCRIBE LTD',
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully created initial M-Pesa payment details')
            )
        else:
            self.stdout.write(
                self.style.WARNING('M-Pesa payment details already exist')
            )