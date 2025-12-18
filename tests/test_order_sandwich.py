# Student ID: 650610818
import pytest
from inventory import InMemoryInventory
from payment import SimplePayment, PaymentDeclinedError
from shipping import ShippingService
from order import OrderService
from emailer import EmailService

class SpyEmail(EmailService):
    """Spy that counts email sends"""
    def __init__(self): 
        self.calls = 0
        self.emails = []
    def send(self, to, subject, body): 
        self.calls += 1
        self.emails.append((to, subject, body))

@pytest.mark.sandwich
def test_order_success_with_real_payment():
    """Test successful order with real payment gateway"""
    inv = InMemoryInventory()
    inv.add_stock("A", 2)
    svc = OrderService(inv, SimplePayment(), ShippingService(), SpyEmail())
    items = [{"sku":"A","qty":1,"price":900.0,"weight":2.0}]
    res = svc.place_order("x@y.com", items, region="TH")
    assert inv.get_stock("A") == 1

@pytest.mark.sandwich
def test_order_with_us_region():
    """Test order with US region shipping"""
    inv = InMemoryInventory()
    inv.add_stock("LAPTOP", 5)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"LAPTOP","qty":1,"price":500.0,"weight":3.0}]
    res = svc.place_order("customer@us.com", items, region="US")
    
    assert res["shipping"] == 300.0
    assert res["total"] == 800.0
    assert inv.get_stock("LAPTOP") == 4
    assert spy_email.calls == 1

@pytest.mark.sandwich
def test_order_with_eu_region():
    """Test order with EU region (default non-TH/US)"""
    inv = InMemoryInventory()
    inv.add_stock("PHONE", 10)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"PHONE","qty":2,"price":200.0,"weight":1.0}]
    res = svc.place_order("customer@eu.com", items, region="EU")
    
    assert res["shipping"] == 300.0
    assert res["total"] == 700.0
    assert inv.get_stock("PHONE") == 8
    assert spy_email.calls == 1

@pytest.mark.sandwich
def test_real_payment_amount_too_high():
    """Test that real payment gateway rejects amounts over 1000"""
    inv = InMemoryInventory()
    inv.add_stock("EXPENSIVE", 2)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"EXPENSIVE","qty":1,"price":900.0,"weight":2.0}]
    
    with pytest.raises(PaymentDeclinedError, match="amount too high"):
        svc.place_order("customer@example.com", items, region="US")
    
    # Stock should be released
    assert inv.get_stock("EXPENSIVE") == 2
    # Email should not be sent
    assert spy_email.calls == 0

@pytest.mark.sandwich
def test_order_with_th_region_lightweight():
    """Test TH region with lightweight shipping (<=5kg)"""
    inv = InMemoryInventory()
    inv.add_stock("BOOK", 10)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"BOOK","qty":2,"price":100.0,"weight":2.0}]
    res = svc.place_order("thai@customer.com", items, region="TH")
    
    assert res["shipping"] == 50.0
    assert res["total"] == 250.0
    assert inv.get_stock("BOOK") == 8
    assert spy_email.calls == 1

@pytest.mark.sandwich
def test_order_with_th_region_heavy():
    """Test TH region with heavy shipping (>5kg)"""
    inv = InMemoryInventory()
    inv.add_stock("FURNITURE", 3)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"FURNITURE","qty":1,"price":400.0,"weight":10.0}]
    res = svc.place_order("thai@customer.com", items, region="TH")
    
    assert res["shipping"] == 120.0
    assert res["total"] == 520.0
    assert inv.get_stock("FURNITURE") == 2
    assert spy_email.calls == 1

@pytest.mark.sandwich
def test_multiple_items_order():
    """Test order with multiple different items"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM_A", 10)
    inv.add_stock("ITEM_B", 15)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [
        {"sku":"ITEM_A","qty":2,"price":100.0,"weight":1.0},
        {"sku":"ITEM_B","qty":3,"price":50.0,"weight":0.5}
    ]
    res = svc.place_order("multi@customer.com", items, region="TH")
    
    # 2*100 + 3*50 = 350, weight = 2*1 + 3*0.5 = 3.5 (<=5, so 50 shipping)
    assert res["total"] == 400.0
    assert inv.get_stock("ITEM_A") == 8
    assert inv.get_stock("ITEM_B") == 12
    assert spy_email.calls == 1

@pytest.mark.sandwich
def test_email_spy_captures_transaction_details():
    """Test that email spy captures correct transaction details"""
    inv = InMemoryInventory()
    inv.add_stock("GADGET", 5)
    spy_email = SpyEmail()
    svc = OrderService(inv, SimplePayment(), ShippingService(), spy_email)
    items = [{"sku":"GADGET","qty":1,"price":250.0,"weight":1.5}]
    res = svc.place_order("buyer@test.com", items, region="TH")
    
    assert len(spy_email.emails) == 1
    to, subject, body = spy_email.emails[0]
    assert to == "buyer@test.com"
    assert subject == "Order confirmed"
    assert str(res["total"]) in body
    assert res["transaction_id"] in body
