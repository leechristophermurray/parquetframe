from parquetframe.permissions import (
    RelationTuple,
    TupleStore,
    check,
    list_objects,
    list_subjects,
)


def run_tutorial():
    print("Running Permissions Tutorial Smoke Test...")

    # Initialize store
    store = TupleStore()

    # Grant permissions
    store.add_tuple(RelationTuple("folder", "finance", "owner", "user", "alice"))
    store.add_tuple(RelationTuple("folder", "finance", "viewer", "user", "bob"))
    store.add_tuple(RelationTuple("doc", "budget_2024", "parent", "folder", "finance"))
    store.add_tuple(RelationTuple("doc", "budget_2024", "editor", "user", "charlie"))

    # Check permissions (direct)
    assert check(store, "user", "alice", "owner", "folder", "finance") == True
    assert check(store, "user", "bob", "owner", "folder", "finance") == False

    # Inheritance logic check
    def check_access(user, obj_ns, obj_id, relation):
        if check(store, "user", user, relation, obj_ns, obj_id):
            return True
        parents = list_subjects(store, "parent", obj_ns, obj_id)
        for parent_ns, parent_id in parents:
            if check_access(user, parent_ns, parent_id, relation):
                return True
        return False

    assert check_access("alice", "doc", "budget_2024", "owner") == True

    # List objects
    folders = list_objects(store, "viewer", "folder")
    assert ("folder", "finance") in folders

    # List subjects
    owners = list_subjects(store, "owner", "folder", "finance")
    assert ("user", "alice") in owners

    print("Permissions Tutorial Smoke Test Passed!")


if __name__ == "__main__":
    run_tutorial()
