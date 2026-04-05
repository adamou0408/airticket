"""Tests for Task 1.3: Outstation ticket combination algorithm."""

from app.tickets.outstation import (
    get_outstation_cities,
    build_outstation_legs,
    generate_combinations,
)


def test_get_outstation_cities_excludes_origin_and_dest():
    cities = get_outstation_cities("TPE", "NRT")
    codes = [c["code"] for c in cities]
    assert "TPE" not in codes
    assert "NRT" not in codes
    assert "HKG" in codes  # should include other cities


def test_get_outstation_cities_region_filter():
    cities = get_outstation_cities("TPE", "CDG", region_filter="southeast_asia")
    codes = [c["code"] for c in cities]
    assert "BKK" in codes
    assert "SIN" in codes
    # northeast_asia cities should NOT appear
    assert "HKG" not in codes
    assert "ICN" not in codes


def test_get_outstation_cities_no_duplicates():
    cities = get_outstation_cities("TPE", "NRT")
    codes = [c["code"] for c in cities]
    assert len(codes) == len(set(codes))


def test_build_outstation_legs_returns_4_legs():
    legs = build_outstation_legs("TPE", "CDG", "HKG")
    assert len(legs) == 4


def test_build_outstation_legs_correct_route():
    legs = build_outstation_legs("TPE", "CDG", "HKG")
    # Leg 1: HKG → TPE
    assert legs[0] == {"origin": "HKG", "destination": "TPE"}
    # Leg 2: TPE → CDG
    assert legs[1] == {"origin": "TPE", "destination": "CDG"}
    # Leg 3: CDG → TPE
    assert legs[2] == {"origin": "CDG", "destination": "TPE"}
    # Leg 4: TPE → HKG
    assert legs[3] == {"origin": "TPE", "destination": "HKG"}


def test_generate_combinations_produces_results():
    combos = generate_combinations("TPE", "CDG")
    assert len(combos) > 0
    for combo in combos:
        assert "outstation_code" in combo
        assert "outstation_name" in combo
        assert len(combo["legs"]) == 4


def test_generate_combinations_with_region_filter():
    all_combos = generate_combinations("TPE", "CDG")
    filtered = generate_combinations("TPE", "CDG", region_filter="southeast_asia")
    assert len(filtered) < len(all_combos)
    for combo in filtered:
        assert combo["outstation_code"] in ["BKK", "SIN", "KUL", "MNL", "SGN", "HAN"]


def test_generate_combinations_excludes_origin():
    combos = generate_combinations("HKG", "CDG")
    codes = [c["outstation_code"] for c in combos]
    assert "HKG" not in codes
