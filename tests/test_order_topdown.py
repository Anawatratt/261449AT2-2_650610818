# Student ID: 650610818
import pytest
from inventory import InMemoryInventory
from shipping import ShippingService
from order import OrderService
from payment import PaymentDeclinedError
from emailer import EmailService

# Stubs for Payment Gateway
class StubFailPayment:
    """Stub that always fails payment"""
    def charge(self, amount: float, currency: str) -> str:
        raise PaymentDeclinedError("simulated decline")
    def refund(self, transaction_id: str) -> None:
        return

class StubFailPaymentInvalidAmount:
    """Stub that fails with invalid amount error"""
    def charge(self, amount: float, currency: str) -> str:
        raise PaymentDeclinedError("invalid amount")
    def refund(self, transaction_id: str) -> None:
        return

class StubFailPaymentAmountTooHigh:
    """Stub that fails with amount too high error"""
    def charge(self, amount: float, currency: str) -> str:
        raise PaymentDeclinedError("amount too high")
    def refund(self, transaction_id: str) -> None:
        return

class StubSuccessPayment:
    """Stub that always succeeds payment"""
    def charge(self, amount: float, currency: str) -> str:
        return f"tx-{int(amount * 100)}"
    def refund(self, transaction_id: str) -> None:
        return

# Spy for Email Service
class SpyEmail(EmailService):
    """Spy that records all sent emails"""
    def __init__(self):
        self.sent = []
    def send(self, to, subject, body):
        self.sent.append((to, subject, body))

@pytest.mark.topdown
def test_payment_decline_releases_stock():
    """Test that payment decline releases reserved inventory"""
    inv = InMemoryInventory()
    inv.add_stock("SKU1", 10)
    svc = OrderService(inv, StubFailPayment(), ShippingService(), SpyEmail())
    items = [{"sku":"SKU1","qty":3,"price":100.0,"weight":1.0}]
    with pytest.raises(PaymentDeclinedError):
        svc.place_order("a@b.com", items, region="TH")
    assert inv.get_stock("SKU1") == 10

@pytest.mark.topdown
def test_payment_fail_invalid_amount_releases_stock():
    """Test payment failure with invalid amount releases inventory"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM1", 5)
    svc = OrderService(inv, StubFailPaymentInvalidAmount(), ShippingService(), SpyEmail())
    items = [{"sku":"ITEM1","qty":2,"price":50.0,"weight":1.5}]
    with pytest.raises(PaymentDeclinedError, match="invalid amount"):
        svc.place_order("test@example.com", items, region="TH")
    assert inv.get_stock("ITEM1") == 5

@pytest.mark.topdown
def test_payment_fail_amount_too_high_releases_stock():
    """Test payment failure with amount too high releases inventory"""
    inv = InMemoryInventory()
    inv.add_stock("EXPENSIVE", 3)
    svc = OrderService(inv, StubFailPaymentAmountTooHigh(), ShippingService(), SpyEmail())
    items = [{"sku":"EXPENSIVE","qty":1,"price":1500.0,"weight":2.0}]
    with pytest.raises(PaymentDeclinedError, match="amount too high"):
        svc.place_order("user@example.com", items, region="TH")
    assert inv.get_stock("EXPENSIVE") == 3

@pytest.mark.topdown
def test_email_spy_captures_subject():
    """Test that SpyEmail captures correct email subject"""
    inv = InMemoryInventory()
    inv.add_stock("PROD", 10)
    spy_email = SpyEmail()
    svc = OrderService(inv, StubSuccessPayment(), ShippingService(), spy_email)
    items = [{"sku":"PROD","qty":1,"price":100.0,"weight":1.0}]
    svc.place_order("customer@example.com", items, region="TH")
    assert len(spy_email.sent) == 1
    assert spy_email.sent[0][1] == "Order confirmed"

@pytest.mark.topdown
def test_email_spy_captures_body_content():
    """Test that SpyEmail captures correct email body with total and transaction ID"""
    inv = InMemoryInventory()
    inv.add_stock("WIDGET", 5)
    spy_email = SpyEmail()
    svc = OrderService(inv, StubSuccessPayment(), ShippingService(), spy_email)
    items = [{"sku":"WIDGET","qty":2,"price":150.0,"weight":3.0}]
    result = svc.place_order("buyer@example.com", items, region="TH")
    
    assert len(spy_email.sent) == 1
    to, subject, body = spy_email.sent[0]
    assert to == "buyer@example.com"
    assert "Total amount" in body
    assert str(result["total"]) in body
    assert result["transaction_id"] in body

@pytest.mark.topdown
def test_email_spy_multiple_orders():
    """Test that SpyEmail captures multiple orders correctly"""
    inv = InMemoryInventory()
    inv.add_stock("SKU_A", 10)
    inv.add_stock("SKU_B", 10)
    spy_email = SpyEmail()
    svc = OrderService(inv, StubSuccessPayment(), ShippingService(), spy_email)
    
    items1 = [{"sku":"SKU_A","qty":1,"price":50.0,"weight":1.0}]
    svc.place_order("user1@example.com", items1, region="TH")
    
    items2 = [{"sku":"SKU_B","qty":2,"price":75.0,"weight":2.0}]
    svc.place_order("user2@example.com", items2, region="TH")
    
    assert len(spy_email.sent) == 2
    assert spy_email.sent[0][0] == "user1@example.com"
    assert spy_email.sent[1][0] == "user2@example.com"
