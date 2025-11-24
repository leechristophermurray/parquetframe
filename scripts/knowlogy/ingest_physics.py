#!/usr/bin/env python3
"""
Knowlogy Physics Library Ingestion Script.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from parquetframe.knowlogy import KnowlogyEngine


def load_physics_library():
    """Load the physics knowledge library."""
    data_path = Path(__file__).parent / "data" / "physics.json"
    with open(data_path, "r") as f:
        data = json.load(f)

    engine = KnowlogyEngine()

    print(f"Loading {data['library']} library v{data['version']}")

    for concept in data["concepts"]:
        engine.add_concept(
            id=concept["id"],
            name=concept["name"],
            description=concept["description"],
            domain=concept["domain"],
            aliases=concept.get("aliases", []),
        )
        print(f"  ✓ {concept['name']}")

    for formula in data["formulas"]:
        engine.add_formula(
            id=formula["id"],
            name=formula["name"],
            latex=formula["latex"],
            symbolic=formula["symbolic"],
            concept_id=formula["concept_id"],
            variables=formula.get("variables", []),
        )
        print(f"  ✓ {formula['name']}")

    print(f"\n✅ Physics library loaded!")


if __name__ == "__main__":
    load_physics_library()
