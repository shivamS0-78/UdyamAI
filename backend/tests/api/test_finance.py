def test_calculate_finance_valid(client):
    """Test finance calculation with valid parameters."""
    payload = {
        "desired_project_cost": 100000.0,
        "available_capital": 25000.0,
        "loan_percent": 75.0,
        "beneficiary_contribution_percent": 25.0,
        "interest_rate": 12.0,
        "tenure_months": 12,
        "moratorium_months": 0,
    }
    response = client.post("/finance/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["desired_project_cost"] == 100000.0
    assert data["available_capital"] == 25000.0
    assert data["potential_loan"] == 75000.0
    assert data["monthly_emi"] > 0

    assert len(data["repayment_schedule"]) == 12


def test_calculate_finance_moratorium(client):
    """Test finance calculation with moratorium period."""
    payload = {
        "desired_project_cost": 100000.0,
        "available_capital": 25000.0,
        "loan_percent": 75.0,
        "beneficiary_contribution_percent": 25.0,
        "interest_rate": 12.0,
        "tenure_months": 12,
        "moratorium_months": 3,
    }
    response = client.post("/finance/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    schedule = data["repayment_schedule"]
    assert len(schedule) == 12
    # Verify first 3 months are marked as moratorium
    for item in schedule[:3]:
        assert item["is_moratorium"] is True
        assert item["principal_amount"] == 0
    # Verify subsequent months are not moratorium
    for item in schedule[3:]:
        assert item["is_moratorium"] is False


def test_calculate_finance_shortfall(client):
    """Test finance calculation returning structured shortfall when capital < required contribution."""
    payload = {
        "available_capital": 50000.0,
        "desired_project_cost": 1000000.0,
        "scheme_rule_override": {
            "beneficiary_contribution_percent": 10.0,
            "loan_percent": 90.0,
            "interest_rate": 8.5,
            "tenure_months": 84,
            "moratorium_months": 6,
        },
    }
    response = client.post("/finance/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "insufficient_margin"
    assert data["available_capital"] == 50000.0
    assert data["required_contribution"] == 100000.0
    assert data["shortfall"] == 50000.0


def test_calculate_finance_dynamic_rule_no_hardcoding(client):
    """Test raw project cost calculation based on available capital and dynamic scheme rules."""
    payload = {
        "available_capital": 100000.0,
        "scheme_rule_override": {
            "beneficiary_contribution_percent": 10.0,
            "loan_percent": 90.0,
            "interest_rate": 8.5,
            "tenure_months": 84,
            "moratorium_months": 6,
            "working_capital_percent": 20.0,
        },
        "monthly_revenue": 100000.0,
        "monthly_operating_cost": 60000.0,
    }
    response = client.post("/finance/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["feasible_project_cost"] == 1000000.0
    assert data["potential_loan"] == 900000.0
    assert data["required_contribution"] == 100000.0
    assert data["shortfall"] == 0.0
    assert data["working_capital"] == 200000.0
    assert len(data["financial_scenarios"]) == 3
    exp_case = data["financial_scenarios"][1]
    assert exp_case["scenario_type"] == "expected_case"
    assert exp_case["revenue"] == 100000.0
    assert exp_case["operating_costs"] == 60000.0
    assert exp_case["surplus"] == 40000.0
    assert exp_case["loan_repayment"] == data["monthly_emi"]
    assert exp_case["cash_surplus"] == 40000.0 - data["monthly_emi"]
    assert exp_case["marked_assumptions"]["local_revenue_invented"] is False


def test_calculate_finance_scenarios_no_revenue_invention(client):
    """Test API endpoint response when no revenue is provided (sufficient_assumptions_exist=False, no local revenue invented)."""
    payload = {
        "available_capital": 100000.0,
        "scheme_rule_override": {
            "beneficiary_contribution_percent": 10.0,
            "loan_percent": 90.0,
            "interest_rate": 8.5,
            "tenure_months": 84,
        },
    }
    response = client.post("/finance/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    scenarios = data["financial_scenarios"]
    assert len(scenarios) == 3
    for s in scenarios:
        assert s["sufficient_assumptions_exist"] is False
        assert s["revenue"] is None
        assert s["operating_costs"] is None
        assert s["surplus"] is None
        assert s["cash_surplus"] is None
        assert s["marked_assumptions"]["local_revenue_invented"] is False


def test_calculate_finance_project_caps(client):
    """Test application of max_project_cost and max_loan_amount limits."""
    payload = {
        "available_capital": 200000.0,  # Could support 20 Lakh raw cost at 10%
        "scheme_rule_override": {
            "beneficiary_contribution_percent": 10.0,
            "loan_percent": 90.0,
            "max_project_cost": 1000000.0,  # Capped at 10 Lakh
            "max_loan_amount": 800000.0,  # Capped loan at 8 Lakh
            "interest_rate": 9.0,
            "tenure_months": 60,
        },
    }
    response = client.post("/finance/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["project_cost_cap_applied"] is True
    assert data["loan_cap_applied"] is True
    assert data["feasible_project_cost"] == 1000000.0
    assert data["potential_loan"] == 800000.0


def test_calculate_finance_invalid_cost(client):
    """Test finance calculation with invalid project cost (negative)."""
    payload = {
        "desired_project_cost": -50.0,
        "available_capital": 25000.0,
        "interest_rate": 12.0,
        "tenure_months": 12,
    }
    response = client.post("/finance/calculate", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "errors" in data
    assert data["error_code"] == "VALIDATION_ERROR"
