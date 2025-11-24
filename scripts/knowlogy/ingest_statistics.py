#!/usr/bin/env python3
"""
Knowlogy Statistics Library Ingestion Script.

Loads curated statistical concepts and formulas into the Knowlogy graph.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from parquetframe.knowlogy import KnowlogyEngine


def load_statistics_library():
    """Load the statistics knowledge library."""
    # Load JSON data
    data_path = Path(__file__).parent / "data" / "statistics.json"
    with open(data_path) as f:
        data = json.load(f)

    engine = KnowlogyEngine()

    print(f"Loading {data['library']} library v{data['version']}")
    print(f"Description: {data['description']}\n")

    # Ingest concepts
    print(f"Ingesting {len(data['concepts'])} concepts...")
    for concept in data["concepts"]:
        engine.add_concept(
            id=concept["id"],
            name=concept["name"],
            description=concept["description"],
            domain=concept["domain"],
            aliases=concept.get("aliases", []),
        )
        print(f"  ✓ {concept['name']}")

    # Ingest formulas
    print(f"\nIngesting {len(data['formulas'])} formulas...")
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

    # Ingest applications
    print(f"\nIngesting {len(data['applications'])} applications...")
    for app in data["applications"]:
        from parquetframe.knowlogy.storage import Application

        application = Application(
            id=app["id"],
            name=app["name"],
            description=app["description"],
            concept_id=app["concept_id"],
        )
        application.save()
        print(f"  ✓ {app['name']}")

    print(f"\n✅ Successfully loaded {data['library']} library!")
    print(
        f"   Total: {len(data['concepts'])} concepts, {len(data['formulas'])} formulas"
    )


if __name__ == "__main__":
    load_statistics_library()
