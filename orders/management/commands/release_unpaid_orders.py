from django.core.management.base import BaseCommand

from orders import stock


class Command(BaseCommand):
    help = "Cancel online orders still unpaid after the hold time and return their stock (run hourly from cron)."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=float, default=None,
                            help="Release orders older than this many hours (default: UNPAID_ORDER_HOLD_HOURS, 24).")
        parser.add_argument("--dry-run", action="store_true", help="List the orders without changing anything.")

    def handle(self, *args, **options):
        orders = list(stock.expired_unpaid_orders(options["hours"]).prefetch_related("items__product"))
        released = 0
        for order in orders:
            items = ", ".join("%d x %s" % (i.quantity, i.product.name if i.product else "deleted product") for i in order.items.all())
            if options["dry_run"]:
                self.stdout.write("would release %s (%s): %s" % (
                    order.formatted_id, order.created_at.strftime("%Y-%m-%d %H:%M"), items))
            elif stock.release(order):
                released += 1
                self.stdout.write("released %s: %s" % (order.formatted_id, items))
        if options["dry_run"]:
            self.stdout.write("%d unpaid order(s) would be released." % len(orders))
        else:
            self.stdout.write("%d unpaid order(s) released." % released)
