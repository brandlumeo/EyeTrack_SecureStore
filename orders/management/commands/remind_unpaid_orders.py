from django.core.management.base import BaseCommand
from django.utils import timezone

from orders import stock
from orders.emails import send_payment_reminder_email


class Command(BaseCommand):
    help = "Email a 'Pay now' reminder for unpaid online orders (once per order; run hourly from cron)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="List the orders without sending anything.")

    def handle(self, *args, **options):
        orders = list(stock.orders_due_reminder())
        sent = 0
        for order in orders:
            if options["dry_run"]:
                self.stdout.write("would remind %s (%s)" % (order.formatted_id, order.email))
                continue
            if send_payment_reminder_email(order.pk):
                type(order).objects.filter(pk=order.pk).update(payment_reminder_sent_at=timezone.now())
                sent += 1
                self.stdout.write("reminded %s" % order.formatted_id)
            else:
                self.stdout.write("could not email %s; will retry next run" % order.formatted_id)
        if options["dry_run"]:
            self.stdout.write("%d order(s) would get a payment reminder." % len(orders))
        else:
            self.stdout.write("%d payment reminder(s) sent." % sent)
