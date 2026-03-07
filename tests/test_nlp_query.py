import pytest
from ml.nlp_query import process_query

def test_nlp_intent_trade_value():
    query = "Total trade value this month"
    result = process_query(query, None)
    assert result["intent"] == "TOTAL_VALUE"
    assert "DATE" in result["entities"] or "month" in query.lower()

def test_nlp_intent_customers():
    query = "Show me top 5 customers"
    result = process_query(query, None)
    assert result["intent"] == "TOP_N_CUSTOMERS"

def test_nlp_intent_compliance():
    query = "Any compliance alerts?"
    result = process_query(query, None)
    assert result["intent"] == "COMPLIANCE_ALERTS"

def test_nlp_intent_pending_shipments():
    query = "How many pending shipments?"
    result = process_query(query, None)
    assert result["intent"] == "COUNT_PENDING"

