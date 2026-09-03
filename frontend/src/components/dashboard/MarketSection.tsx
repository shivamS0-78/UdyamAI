'use client';

import React from 'react';

interface MarketSectionProps {
  data?: any;
}

interface MarketStatProps {
  label: string;
  value: string;
  description?: string;
}

function MarketStat({ label, value, description }: MarketStatProps) {
  return (
    <div className="rounded-xl border border-gray-200 p-5 bg-white">
      <p className="text-sm font-medium text-gray-500">
        {label}
      </p>

      <p className="text-2xl font-bold text-gray-900 mt-2">
        {value}
      </p>

      {description && (
        <p className="text-sm text-gray-500 mt-1">
          {description}
        </p>
      )}
    </div>
  );
}

function getScoreBarColor(score: number) {
  if (score >= 75) return 'bg-green-500';
  if (score >= 50) return 'bg-amber-500';
  return 'bg-red-500';
}

function getScoreTextColor(score: number) {
  if (score >= 75) return 'text-green-600';
  if (score >= 50) return 'text-amber-600';
  return 'text-red-600';
}

export default function MarketSection({ data }: MarketSectionProps) {
  const mkt = data?.market || {};
  const feas = data?.feasibility || {};
  const aiAdvice = data?.ai_advice || {};
  const marketAdviceList: string[] = aiAdvice.market_advice || [];

  // Use only real API data; no hardcoded fallback scores
  const rawMarketScore = feas.market_score ?? mkt.market_score;
  const marketScore = rawMarketScore != null ? Math.round(rawMarketScore) : null;

  // Derive demand level from demand_indicators if not directly available
  const demandIndicators = mkt.demand_indicators || {};
  const demandLevel = mkt.demand_level
    || demandIndicators.demand_level
    || demandIndicators.level
    || null;

  // Population & household data from Census-based analysis
  const populationEstimate = mkt.population_estimate ?? null;
  const householdEstimate = mkt.household_estimate ?? null;

  // Target customers from market reach estimate
  const targetCustomersRaw = mkt.target_customers ?? null;
  const targetCustomers = targetCustomersRaw != null
    ? `${Number(targetCustomersRaw).toLocaleString('en-IN')}+ people`
    : (populationEstimate != null ? `${Number(populationEstimate).toLocaleString('en-IN')}+ (Census Catchment)` : null);

  // Pricing indicators from AGMARKNET/commodity data
  const pricingIndicators = mkt.pricing_indicators || {};
  const hasPricingData = Object.keys(pricingIndicators).length > 0;

  // Demand indicators breakdown
  const hasDemandData = Object.keys(demandIndicators).length > 0;

  return (
    <div className="flex flex-col gap-6">
      {/* Market statistics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MarketStat
          label="Market Sub-Score"
          value={marketScore != null ? `${marketScore} / 100` : '—'}
          description="Demographic & price score"
        />

        <MarketStat
          label="Local Demand Level"
          value={demandLevel || '—'}
          description="Assessed from commodity demand"
        />

        <MarketStat
          label="Catchment Population"
          value={populationEstimate != null ? `${Number(populationEstimate).toLocaleString('en-IN')}+` : '—'}
          description="Within survey radius"
        />

        <MarketStat
          label="Target Customers"
          value={targetCustomers || '—'}
          description="Estimated market reach"
        />
      </div>

      {/* Secondary market metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {householdEstimate != null && (
          <MarketStat
            label="Household Estimate"
            value={Number(householdEstimate).toLocaleString('en-IN')}
            description="Census-based household count"
          />
        )}
        {mkt.radius_km != null && (
          <MarketStat
            label="Analysis Radius"
            value={`${mkt.radius_km} km`}
            description="Survey coverage area"
          />
        )}
        {mkt.data_confidence && (
          <MarketStat
            label="Data Confidence"
            value={mkt.data_confidence}
            description="Market data reliability"
          />
        )}
      </div>

      {/* AI Market Guidance (when data is sparse) */}
      {(marketScore == null && populationEstimate == null && marketAdviceList.length > 0) && (
        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-5">
          <p className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-2">
            AI Market Guidance
          </p>
          <ul className="space-y-1.5">
            {marketAdviceList.map((advice: string, i: number) => (
              <li key={i} className="text-sm text-blue-900 flex items-start gap-1.5">
                <span className="text-blue-500 font-bold mt-0.5">•</span>
                <span>{advice}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Market opportunity */}
      <div className="rounded-xl border border-gray-200 p-6 bg-white">
        <h3 className="text-lg font-semibold text-gray-900">
          Market Opportunity Assessment
        </h3>

        <p className="text-sm text-gray-500 mt-1">
          Real-time market evaluation from AGMARKNET & Census database
        </p>

        <div className="mt-6">
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Opportunity Score
            </span>

            <span className={`text-sm font-semibold ${marketScore != null ? getScoreTextColor(marketScore) : 'text-gray-400'}`}>
              {marketScore != null ? `${marketScore} / 100` : '— / 100'}
            </span>
          </div>

          <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
            {marketScore != null ? (
              <div
                className={`h-full ${getScoreBarColor(marketScore)} rounded-full transition-all duration-500`}
                style={{ width: `${marketScore}%` }}
              />
            ) : (
              <div
                className="h-full bg-gray-300 rounded-full"
                style={{ width: '0%' }}
              />
            )}
          </div>
        </div>
      </div>

      {/* Demand & Pricing Indicators (if data is available) */}
      {(hasDemandData || hasPricingData) && (
        <div className="rounded-xl border border-gray-200 p-6 bg-white">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Market Indicators Detail
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {hasDemandData && (
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                  Demand Indicators
                </p>
                <div className="space-y-1.5">
                  {Object.entries(demandIndicators).map(([key, val]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-medium text-gray-900">{String(val)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {hasPricingData && (
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                  Pricing Indicators
                </p>
                <div className="space-y-1.5">
                  {Object.entries(pricingIndicators).map(([key, val]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-medium text-gray-900">{String(val)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}