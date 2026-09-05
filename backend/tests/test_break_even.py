from app.finance.break_even import calculate_break_even_period


def test_calculate_break_even_basic():
    # project_cost = 200,000, monthly_profit = 20,000 -> 10.0 months
    months = calculate_break_even_period(project_cost=200000.0, monthly_profit=20000.0)
    assert months == 10.0


def test_calculate_break_even_with_subsidy():
    # project_cost = 200,000, subsidy = 50,000, net = 150,000, monthly_profit = 20,000 -> 7.5 months
    months = calculate_break_even_period(
        project_cost=200000.0, monthly_profit=20000.0, subsidy_amount=50000.0
    )
    assert months == 7.5


def test_calculate_break_even_with_emi_cash_surplus():
    # project_cost = 100,000, profit = 15,000, emi = 5,000 -> surplus = 10,000 -> 10.0 months
    months = calculate_break_even_period(
        project_cost=100000.0,
        monthly_profit=15000.0,
        monthly_emi=5000.0,
        use_cash_surplus=True,
    )
    assert months == 10.0


def test_calculate_break_even_zero_or_negative():
    assert calculate_break_even_period(project_cost=0, monthly_profit=10000) is None
    assert calculate_break_even_period(project_cost=10000, monthly_profit=0) is None
    assert calculate_break_even_period(project_cost=10000, monthly_profit=-500) is None
