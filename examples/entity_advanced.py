import os
import shutil
from dataclasses import dataclass

from parquetframe.entity import entity, rel


def run_entity_test():
    print("Running Entity Advanced Examples Smoke Test...")

    # Cleanup
    for path in ["data/users", "data/groups", "data/memberships"]:
        if os.path.exists(path):
            shutil.rmtree(path)

    @entity(storage_path="data/users", primary_key="id")
    @dataclass
    class User:
        id: str
        name: str

    @entity(storage_path="data/groups", primary_key="id")
    @dataclass
    class Group:
        id: str
        name: str

    @entity(storage_path="data/memberships", primary_key="id")
    @dataclass
    class Membership:
        id: str
        user_id: str = rel("User", "id")
        group_id: str = rel("Group", "id")
        role: str = "member"

    # Create data
    u = User("u1", "Alice")
    g = Group("g1", "Devs")
    m = Membership("m1", user_id="u1", group_id="g1", role="admin")

    u.save()
    g.save()
    m.save()

    # Query
    all_memberships = Membership.find_all()
    user_memberships = [m for m in all_memberships if m.user_id == "u1"]

    assert len(user_memberships) == 1
    assert user_memberships[0].group_id == "g1"

    print("Entity Advanced Examples Smoke Test Passed!")

    # Cleanup
    for path in ["data/users", "data/groups", "data/memberships"]:
        if os.path.exists(path):
            shutil.rmtree(path)


if __name__ == "__main__":
    run_entity_test()
