# Student ID: 650610818
import pytest
from inventory import InMemoryInventory, InventoryError

@pytest.mark.bottomup
def test_inventory_reserve_and_release():
    """Test basic reserve and release operations"""
    inv = InMemoryInventory()
    inv.add_stock("S", 5)
    inv.reserve("S", 3)
    assert inv.get_stock("S") == 2
    inv.release("S", 3)
    assert inv.get_stock("S") == 5

@pytest.mark.bottomup
def test_inventory_not_enough_stock():
    """Test that reserve fails when not enough stock"""
    inv = InMemoryInventory()
    inv.add_stock("S", 1)
    with pytest.raises(InventoryError):
        inv.reserve("S", 2)

@pytest.mark.bottomup
def test_reserve_exact_stock_amount():
    """Test reserving exactly all available stock"""
    inv = InMemoryInventory()
    inv.add_stock("PROD", 10)
    inv.reserve("PROD", 10)
    assert inv.get_stock("PROD") == 0

@pytest.mark.bottomup
def test_reserve_zero_quantity_fails():
    """Test that reserve fails with zero quantity"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM", 5)
    with pytest.raises(InventoryError, match="qty must be > 0"):
        inv.reserve("ITEM", 0)

@pytest.mark.bottomup
def test_reserve_negative_quantity_fails():
    """Test that reserve fails with negative quantity"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM", 5)
    with pytest.raises(InventoryError, match="qty must be > 0"):
        inv.reserve("ITEM", -1)

@pytest.mark.bottomup
def test_release_zero_quantity_fails():
    """Test that release fails with zero quantity"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM", 5)
    with pytest.raises(InventoryError, match="qty must be > 0"):
        inv.release("ITEM", 0)

@pytest.mark.bottomup
def test_release_negative_quantity_fails():
    """Test that release fails with negative quantity"""
    inv = InMemoryInventory()
    with pytest.raises(InventoryError, match="qty must be > 0"):
        inv.release("ITEM", -1)

@pytest.mark.bottomup
def test_reserve_nonexistent_sku():
    """Test that reserve fails for non-existent SKU"""
    inv = InMemoryInventory()
    with pytest.raises(InventoryError, match="not enough stock"):
        inv.reserve("NONEXISTENT", 1)

@pytest.mark.bottomup
def test_add_stock_negative_fails():
    """Test that add_stock fails with negative quantity"""
    inv = InMemoryInventory()
    with pytest.raises(InventoryError, match="qty must be >= 0"):
        inv.add_stock("ITEM", -5)

@pytest.mark.bottomup
def test_add_stock_zero_succeeds():
    """Test that add_stock with zero quantity is allowed"""
    inv = InMemoryInventory()
    inv.add_stock("ITEM", 0)
    assert inv.get_stock("ITEM") == 0

@pytest.mark.bottomup
def test_release_to_nonexistent_sku():
    """Test that release can add to non-existent SKU"""
    inv = InMemoryInventory()
    inv.release("NEW_SKU", 5)
    assert inv.get_stock("NEW_SKU") == 5

@pytest.mark.bottomup
def test_multiple_reserves_and_releases():
    """Test multiple reserve and release operations"""
    inv = InMemoryInventory()
    inv.add_stock("MULTI", 20)
    inv.reserve("MULTI", 5)
    assert inv.get_stock("MULTI") == 15
    inv.reserve("MULTI", 3)
    assert inv.get_stock("MULTI") == 12
    inv.release("MULTI", 2)
    assert inv.get_stock("MULTI") == 14
    inv.release("MULTI", 6)
    assert inv.get_stock("MULTI") == 20
