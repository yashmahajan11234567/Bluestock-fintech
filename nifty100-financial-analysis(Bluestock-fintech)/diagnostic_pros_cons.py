#!/usr/bin/env python3
"""
Diagnostic script to evaluate pros/cons rules for 4 companies: SBIN, BRITANNIA, BEL, HINDUNILVR
"""

import sys
import os
sys.path.append('.')

from src.nlp.pros_cons_generator import (
    load_company_data,
    PRO_RULES,
    CON_RULES,
    ProsConsSignal,
    PRO_RULES,
    CON_RULES
)

def diagnose_company(company_id: str):
    """Diagnose all rules for a single company."""
    print(f"\n{'='*60}")
    print(f"DIAGNOSING COMPANY: {company_id}")
    print(f"{'='*60}")

    # Load company data
    try:
        data = load_company_data(company_id)
        print(f"Loaded data for {company_id}")
        print(f"  - Financial ratios: {len(data.financial_ratios)} years")
        print(f"  - P&L data: {len(data.pl_data)} years")
        print(f"  - Balance sheet: {len(data.bs_data)} years")
        print(f"  - Market cap: {len(data.market_cap)} years")
        print(f"  - Sector: {data.sector}")
    except Exception as e:
        print(f"ERROR loading data for {company_id}: {e}")
        return

    # Evaluate all PRO rules
    print(f"\n--- PRO RULES (12 rules) ---")
    pro_results = []
    for i, rule_fn in enumerate(PRO_RULES, 1):
        rule_id = f"PRO_{i}"
        try:
            signal = rule_fn(data)
            if signal is None:
                # Determine if it's FALSE or INSUFFICIENT DATA
                # We need to check if the rule returned None due to condition failure vs missing data
                # For now, we'll classify as FALSE if we can determine the condition wasn't met
                # This is a simplification - in reality we'd need to inspect each rule's logic
                pro_results.append({
                    'rule_id': rule_id,
                    'status': 'FALSE',  # Default assumption
                    'signal': None,
                    'confidence': None,
                    'metric': 'N/A',
                    'reason': 'Condition not met'
                })
            else:
                pro_results.append({
                    'rule_id': rule_id,
                    'status': 'TRUE' if signal.confidence_pct > 60 else 'TRUE_FILTERED',
                    'signal': signal,
                    'confidence': signal.confidence_pct,
                    'metric': 'N/A',  # Would need to extract from rule logic
                    'reason': 'N/A'
                })
        except Exception as e:
            pro_results.append({
                'rule_id': rule_id,
                'status': 'ERROR',
                'signal': None,
                'confidence': None,
                'metric': 'N/A',
                'reason': f'Rule evaluation error: {e}'
            })

    # Evaluate all CON rules
    print(f"\n--- CON RULES (12 rules) ---")
    con_results = []
    for i, rule_fn in enumerate(CON_RULES, 1):
        rule_id = f"CON_{i}"
        try:
            signal = rule_fn(data)
            if signal is None:
                con_results.append({
                    'rule_id': rule_id,
                    'status': 'FALSE',  # Default assumption
                    'signal': None,
                    'confidence': None,
                    'metric': 'N/A',
                    'reason': 'Condition not met'
                })
            else:
                con_results.append({
                    'rule_id': rule_id,
                    'status': 'TRUE' if signal.confidence_pct > 60 else 'TRUE_FILTERED',
                    'signal': signal,
                    'confidence': signal.confidence_pct,
                    'metric': 'N/A',
                    'reason': 'N/A'
                })
        except Exception as e:
            con_results.append({
                'rule_id': rule_id,
                'status': 'ERROR',
                'signal': None,
                'confidence': None,
                'metric': 'N/A',
                'reason': f'Rule evaluation error: {e}'
            })

    # Print PRO results
    print("\nPRO RULES RESULTS:")
    print("-" * 80)
    for result in pro_results:
        status = result['status']
        if status == 'TRUE':
            print(f"{result['rule_id']:8} | {status:15} | Confidence: {result['confidence']:6.2f}% | {result['signal'].text if result['signal'] else 'N/A'}")
        elif status == 'TRUE_FILTERED':
            print(f"{result['rule_id']:8} | {status:15} | Confidence: {result['confidence']:6.2f}% | {result['signal'].text if result['signal'] else 'N/A'} <- FILTERED (<=60%)")
        else:
            print(f"{result['rule_id']:8} | {status:15} | {result['reason']}")

    # Print CON results
    print("\nCON RULES RESULTS:")
    print("-" * 80)
    for result in con_results:
        status = result['status']
        if status == 'TRUE':
            print(f"{result['rule_id']:8} | {status:15} | Confidence: {result['confidence']:6.2f}% | {result['signal'].text if result['signal'] else 'N/A'}")
        elif status == 'TRUE_FILTERED':
            print(f"{result['rule_id']:8} | {status:15} | Confidence: {result['confidence']:6.2f}% | {result['signal'].text if result['signal'] else 'N/A'} <- FILTERED (<=60%)")
        else:
            print(f"{result['rule_id']:8} | {status:15} | {result['reason']}")

    # Summary
    pro_true = sum(1 for r in pro_results if r['status'] == 'TRUE')
    pro_filtered = sum(1 for r in pro_results if r['status'] == 'TRUE_FILTERED')
    pro_false = sum(1 for r in pro_results if r['status'] == 'FALSE')
    pro_error = sum(1 for r in pro_results if r['status'] == 'ERROR')

    con_true = sum(1 for r in con_results if r['status'] == 'TRUE')
    con_filtered = sum(1 for r in con_results if r['status'] == 'TRUE_FILTERED')
    con_false = sum(1 for r in con_results if r['status'] == 'FALSE')
    con_error = sum(1 for r in con_results if r['status'] == 'ERROR')

    print(f"\nSUMMARY FOR {company_id}:")
    print(f"  PRO Rules:  {pro_true} TRUE, {pro_filtered} TRUE_FILTERED, {pro_false} FALSE, {pro_error} ERROR")
    print(f"  CON Rules:  {con_true} TRUE, {con_filtered} TRUE_FILTERED, {con_false} FALSE, {con_error} ERROR")

def main():
    companies = ['SBIN', 'BRITANNIA', 'BEL', 'HINDUNILVR']

    print("Starting Pros/Cons Diagnostic Analysis")
    print("Companies to analyze:", ', '.join(companies))

    for company_id in companies:
        diagnose_company(company_id)

    print(f"\n{'='*60}")
    print("DIAGNOSTIC COMPLETE")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()