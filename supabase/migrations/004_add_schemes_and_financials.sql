-- Create documents table (RAG documents metadata)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    source_name TEXT,
    source_url TEXT,
    document_type TEXT,
    language TEXT,
    file_path TEXT,
    published_date DATE,
    effective_from DATE,
    effective_until DATE,
    last_verified_at TIMESTAMPTZ,
    content_hash TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create schemes table
CREATE TABLE schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    agency_name TEXT,
    state TEXT,
    active BOOLEAN DEFAULT TRUE,
    official_url TEXT,
    source TEXT,
    last_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create scheme_rules table
CREATE TABLE scheme_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    min_project_cost NUMERIC(14,2),
    max_project_cost NUMERIC(14,2),
    beneficiary_contribution_percent NUMERIC(5,2),
    loan_percent NUMERIC(5,2),
    max_loan_amount NUMERIC(14,2),
    interest_rate NUMERIC(6,3),
    tenure_months INTEGER,
    moratorium_months INTEGER,
    min_age INTEGER,
    max_age INTEGER,
    income_limit NUMERIC(14,2),
    eligible_business_categories JSONB,
    eligible_locations JSONB,
    eligible_beneficiary_categories JSONB,
    other_conditions JSONB,
    effective_from DATE,
    effective_until DATE,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create scheme_eligibility_rules table
CREATE TABLE scheme_eligibility_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    rule_type TEXT,
    field_name TEXT,
    operator TEXT,
    expected_value JSONB,
    description TEXT,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create scheme_matches table
CREATE TABLE scheme_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    match_status TEXT NOT NULL CHECK (match_status IN ('potential_match', 'not_match', 'missing_information', 'verification_required')),
    match_score NUMERIC,
    matched_conditions JSONB,
    failed_conditions JSONB,
    missing_information JSONB,
    estimated_loan_amount NUMERIC(14,2),
    estimated_project_cost NUMERIC(14,2),
    verification_required BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create financial_analyses table
CREATE TABLE financial_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    scheme_id UUID REFERENCES schemes(id) ON DELETE SET NULL,
    available_capital NUMERIC(14,2),
    required_contribution NUMERIC(14,2),
    desired_project_cost NUMERIC(14,2),
    feasible_project_cost NUMERIC(14,2),
    margin_gap NUMERIC(14,2),
    calculated_loan NUMERIC(14,2),
    interest_rate NUMERIC(6,3),
    tenure_months INTEGER,
    moratorium_months INTEGER,
    monthly_emi NUMERIC(14,2),
    total_interest NUMERIC(14,2),
    total_repayment NUMERIC(14,2),
    working_capital NUMERIC(14,2),
    monthly_revenue NUMERIC(14,2),
    monthly_operating_cost NUMERIC(14,2),
    monthly_profit NUMERIC(14,2),
    break_even_months NUMERIC(10,2),
    repayment_capacity NUMERIC(14,2),
    calculation_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create repayment_schedules table
CREATE TABLE repayment_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    financial_analysis_id UUID NOT NULL REFERENCES financial_analyses(id) ON DELETE CASCADE,
    period_number INTEGER NOT NULL,
    period_start DATE,
    period_end DATE,
    principal_amount NUMERIC(14,2),
    interest_amount NUMERIC(14,2),
    payment_amount NUMERIC(14,2),
    remaining_principal NUMERIC(14,2),
    is_moratorium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create financial_scenarios table
CREATE TABLE financial_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    financial_analysis_id UUID NOT NULL REFERENCES financial_analyses(id) ON DELETE CASCADE,
    scenario_type TEXT NOT NULL CHECK (scenario_type IN ('worst_case', 'expected_case', 'best_case')),
    monthly_revenue NUMERIC(14,2),
    monthly_expenses NUMERIC(14,2),
    monthly_profit NUMERIC(14,2),
    cash_flow JSONB,
    repayment_coverage NUMERIC(14,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
