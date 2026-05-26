import re

def update_views():
    with open('store/views.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Part 1: Product loop
    part1_search = r'''    products = \[\]\s*subtotal_total = Decimal\("0\.00"\)\s*unavailable_items = \[\]\s*for product_id, quantity in product_quantities\.items\(\):\s*try:\s*product = Product\.objects\.get\(id=product_id, is_available=True\)\s*subtotal = product\.price \* quantity\s*subtotal_total \+= subtotal\s*products\.append\(\{"product": product, "quantity": quantity, "subtotal": subtotal\}\)\s*except Product\.DoesNotExist:\s*unavailable_items\.append\(product_id\)'''

    part1_replace = '''    products = []
    subtotal_total = Decimal("0.00")
    unavailable_items = []
    has_installation = False
    
    for product_id, quantity in product_quantities.items():
        try:
            product = Product.objects.select_related("category").get(id=product_id, is_available=True)
            subtotal = product.price * quantity
            subtotal_total += subtotal
            products.append({"product": product, "quantity": quantity, "subtotal": subtotal})
            if product.category and product.category.slug == "cctv-installations":
                has_installation = True
        except Product.DoesNotExist:
            unavailable_items.append(product_id)

    installation_product = None
    if not has_installation:
        installation_product = Product.objects.filter(category__slug="cctv-installations", is_available=True).first()'''

    text = re.sub(part1_search, part1_replace, text, 1)

    # Part 2: POST form validation
    part2_search = r'''        if not all\(\[full_name, email, phone, address\]\):\s*messages\.error\(request, "Please fill in all required checkout fields\."\)\s*else:\s*with transaction\.atomic\(\):'''

    part2_replace = '''        if not all([full_name, email, phone, address]):
            messages.error(request, "Please fill in all required checkout fields.")
        else:
            installation_date = request.POST.get("installation_date")
            installation_time = request.POST.get("installation_time")
            
            if has_installation and (not installation_date or not installation_time):
                messages.error(request, "Please select your preferred installation date and time slot.")
                return redirect("checkout")

            with transaction.atomic():'''

    text = re.sub(part2_search, part2_replace, text, 1)

    # Part 3: Order save logic
    part3_search = r'''                # Increment coupon usage if applied\s*if active_coupon:\s*active_coupon\.current_uses \+= 1\s*active_coupon\.save\(update_fields=\["current_uses"\]\)\s*# Remove from session after order creation\s*del request\.session\["coupon_id"\]\s*if order\.payment_method == Order\.PaymentMethod\.COD:'''

    part3_replace = '''                # Increment coupon usage if applied
                if active_coupon:
                    active_coupon.current_uses += 1
                    active_coupon.save(update_fields=["current_uses"])
                    # Remove from session after order creation
                    del request.session["coupon_id"]

                if has_installation:
                    from orders.models import InstallationBooking
                    InstallationBooking.objects.create(
                        order=order,
                        preferred_date=installation_date,
                        preferred_time_slot=installation_time,
                    )

                if order.payment_method == Order.PaymentMethod.COD:'''

    text = re.sub(part3_search, part3_replace, text, 1)

    # Part 4: Context build
    part4_search = r'''    context = \{\s*"products": products,\s*"total": subtotal_total,\s*"discount_amount": discount_amount,'''

    part4_replace = '''    context = {
        "products": products,
        "has_installation": has_installation,
        "installation_product": installation_product,
        "total": subtotal_total,
        "discount_amount": discount_amount,'''

    text = re.sub(part4_search, part4_replace, text, 1)

    with open('store/views.py', 'w', encoding='utf-8') as f:
        f.write(text)
    
    print("store/views.py updated successfully.")

if __name__ == '__main__':
    update_views()
