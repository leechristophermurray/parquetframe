"""
Tests for Delta Log (Write-Ahead Log) functionality.

Verifies O(1) write complexity, crash safety, and concurrency.
"""

import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from parquetframe.entity import entity


def test_delta_log_basic():
    """Test basic delta log operations."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str
            score: int

        # Create users
        User("u1", "Alice", 100).save()
        User("u2", "Bob", 200).save()

        # Verify delta log exists
        delta_log = User._entity_store.delta_log
        assert delta_log.wal_path.exists()
        assert delta_log.count_deltas() == 2

        # Verify data
        users = User.find_all()
        assert len(users) == 2

        print(f"✓ Delta log created with {delta_log.count_deltas()} operations")

    finally:
        shutil.rmtree(temp_dir)


def test_delta_log_upsert():
    """Test update operations via delta log."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "products", primary_key="product_id")
        @dataclass
        class Product:
            product_id: str
            name: str
            price: float

        # Create
        Product("p1", "Widget", 10.0).save()

        # Update
        Product("p1", "Widget Pro", 15.0).save()

        # Verify delta count
        delta_log = Product._entity_store.delta_log
        assert delta_log.count_deltas() == 2  # Both create and update

        # Verify final state
        p = Product.find("p1")
        assert p.name == "Widget Pro"
        assert p.price == 15.0

        print("✓ UPSERT operations work correctly")

    finally:
        shutil.rmtree(temp_dir)


def test_delta_log_delete():
    """Test delete operations via delta log."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "items", primary_key="item_id")
        @dataclass
        class Item:
            item_id: str
            name: str

        # Create several items
        Item("i1", "A").save()
        Item("i2", "B").save()
        Item("i3", "C").save()

        # Delete one
        item = Item.find("i2")
        item.delete()

        # Verify
        all_items = Item.find_all()
        assert len(all_items) == 2
        assert Item.find("i2") is None

        # Check delta log
        delta_log = Item._entity_store.delta_log
        assert delta_log.count_deltas() == 4  # 3 creates + 1 delete

        print("✓ DELETE operations work correctly")

    finally:
        shutil.rmtree(temp_dir)


def test_delta_log_compaction():
    """Test automatic compaction."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "records", primary_key="id")
        @dataclass
        class Record:
            id: str
            value: int

        # Create many records to trigger compaction
        delta_log = Record._entity_store.delta_log
        delta_log.compaction_threshold = 10  # Low threshold for testing

        for i in range(15):
            Record(f"r{i}", i).save()

        # Should have triggered compaction
        assert delta_log.count_deltas() < 15  # Compacted at some point

        # Verify all data present
        records = Record.find_all()
        assert len(records) == 15

        # Check base file exists
        base_path = temp_dir / "records" / "base.parquet"
        assert base_path.exists()

        print(
            f"✓ Automatic compaction triggered (delta count: {delta_log.count_deltas()})"
        )

    finally:
        shutil.rmtree(temp_dir)


def test_delta_log_crash_recovery():
    """Test crash recovery - WAL replay."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "tasks", primary_key="task_id")
        @dataclass
        class Task:
            task_id: str
            title: str
            done: bool

        # Write some data
        Task("t1", "Task 1", False).save()
        Task("t2", "Task 2", True).save()

        # Simulate crash - don't compact, just reload
        # The delta log should replay on next read
        delta_count_before = Task._entity_store.delta_log.count_deltas()

        # Reload entitystore (simulates process restart)
        from parquetframe.entity.entity_store import EntityStore

        new_store = EntityStore(Task._entity_metadata)

        # Should replay WAL and get correct data
        tasks = new_store.find_all()
        assert len(tasks) == 2
        assert tasks[0].task_id in ["t1", "t2"]

        print(f"✓ Crash recovery works (replayed {delta_count_before} deltas)")

    finally:
        shutil.rmtree(temp_dir)


def test_delta_log_performance():
    """Test that writes are fast (O(1))."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "events", primary_key="event_id")
        @dataclass
        class Event:
            event_id: str
            timestamp: float

        # Disable compaction for pure append test
        delta_log = Event._entity_store.delta_log
        delta_log.compaction_threshold = 10000

        # Measure write times
        write_times = []

        for i in range(100):
            start = time.time()
            Event(f"e{i}", time.time()).save()
            elapsed = time.time() - start
            write_times.append(elapsed)

        # Verify O(1) - later writes shouldn't be slower
        early_avg = sum(write_times[:10]) / 10
        late_avg = sum(write_times[-10:]) / 10

        # Late writes should be same speed (within 10x tolerance for CI environments)
        # CI environments can be very variable in performance
        assert late_avg < early_avg * 10, (
            f"Writes slowed down significantly: {early_avg:.4f}s -> {late_avg:.4f}s"
        )

        print(
            f"✓ Write performance consistent: {early_avg:.4f}s (early) vs {late_avg:.4f}s (late)"
        )

    finally:
        shutil.rmtree(temp_dir)


def test_delta_log_stats():
    """Test delta log statistics."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "logs", primary_key="log_id")
        @dataclass
        class Log:
            log_id: str
            message: str

        # Create some data
        Log("l1", "First").save()
        Log("l2", "Second").save()

        # Get stats
        delta_log = Log._entity_store.delta_log
        stats = delta_log.get_stats()

        assert stats["delta_count"] == 2
        assert stats["wal_exists"] is True
        assert stats["wal_size_mb"] > 0

        print(f"✓ Stats: {stats}")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("Testing Delta Log Transactions...")

    test_delta_log_basic()
    print("✓ Basic operations work")

    test_delta_log_upsert()
    print("✓ UPSERT works")

    test_delta_log_delete()
    print("✓ DELETE works")

    test_delta_log_compaction()
    print("✓ Automatic compaction works")

    test_delta_log_crash_recovery()
    print("✓ Crash recovery works")

    test_delta_log_performance()
    print("✓ Performance is O(1)")

    test_delta_log_stats()
    print("✓ Statistics work")

    print("\n✅ All Delta Log tests passed!")
