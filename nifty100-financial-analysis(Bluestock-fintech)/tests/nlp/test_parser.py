import pytest
from src.nlp.parser import AnalysisTextParser, ParsedRecord, ParseFailure


class TestAnalysisTextParser:
    """Test suite for the AnalysisTextParser class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.parser = AnalysisTextParser()

    def test_standard_pattern_basic(self):
        """Test standard pattern: '10 Years: 21%'"""
        records = self.parser.parse_cell("10 Years: 21%", "TEST", "compounded_sales_growth", 1)
        assert len(records) == 1
        assert records[0].company_id == "TEST"
        assert records[0].metric_type == "compounded_sales_growth"
        assert records[0].period_years == 10.0
        assert records[0].value_pct == 21.0

    def test_standard_pattern_decimal_years(self):
        """Test standard pattern with decimal years: '5.5 Years: 15.5%'"""
        records = self.parser.parse_cell("5.5 Years: 15.5%", "TEST", "compounded_profit_growth", 1)
        assert len(records) == 1
        assert records[0].period_years == 5.5
        assert records[0].value_pct == 15.5

    def test_standard_pattern_decimal_value(self):
        """Test standard pattern with decimal value: '5 Years: 15.5%'"""
        records = self.parser.parse_cell("5 Years: 15.5%", "TEST", "compounded_profit_growth", 1)
        assert len(records) == 1
        assert records[0].period_years == 5.0
        assert records[0].value_pct == 15.5

    def test_standard_pattern_negative(self):
        """Test standard pattern with negative: '3 Years: -1%'"""
        records = self.parser.parse_cell("3 Years: -1%", "TEST", "stock_price_cagr", 1)
        assert len(records) == 1
        assert records[0].period_years == 3.0
        assert records[0].value_pct == -1.0

    def test_standard_pattern_positive_sign(self):
        """Test standard pattern with explicit positive sign: '3 Years: +1%'"""
        records = self.parser.parse_cell("3 Years: +1%", "TEST", "roe", 1)
        assert len(records) == 1
        assert records[0].period_years == 3.0
        assert records[0].value_pct == 1.0

    def test_standard_pattern_optional_colon(self):
        """Test standard pattern with optional colon: '10 Years 21%'"""
        records = self.parser.parse_cell("10 Years 21%", "TEST", "compounded_sales_growth", 1)
        assert len(records) == 1
        assert records[0].period_years == 10.0
        assert records[0].value_pct == 21.0

    def test_standard_pattern_singular(self):
        """Test standard pattern with singular: '1 Year: 39%'"""
        records = self.parser.parse_cell("1 Year: 39%", "TEST", "compounded_profit_growth", 1)
        assert len(records) == 1
        assert records[0].period_years == 1.0
        assert records[0].value_pct == 39.0

    def test_standard_pattern_whitespace_variations(self):
        """Test standard pattern with various whitespace"""
        test_cases = [
            "10 Years: 21%",
            "10Years:21%",
            "10  Years :  21  %",
            "\t10 Years:\t 21%\t",
            "  10   Years   :   21   %  "
        ]
        for case in test_cases:
            records = self.parser.parse_cell(case, "TEST", "compounded_sales_growth", 1)
            assert len(records) == 1
            assert records[0].period_years == 10.0
            assert records[0].value_pct == 21.0

    def test_ttm_pattern(self):
        """Test TTM pattern: 'TTM: 5%'"""
        records = self.parser.parse_cell("TTM: 5%", "TEST", "compounded_sales_growth", 1)
        assert len(records) == 1
        assert records[0].period_years == 0.0  # TTM maps to 0 years
        assert records[0].value_pct == 5.0

    def test_ttm_pattern_variations(self):
        """Test TTM pattern variations"""
        test_cases = [
            "TTM: 5%",
            "TTM 5%",
            "TTM:5%",
            "ttm: 5%",  # case insensitive
            "TtM: 5.5%",
            "TTM: -3.2%"
        ]
        for case in test_cases:
            records = self.parser.parse_cell(case, "TEST", "compounded_sales_growth", 1)
            assert len(records) == 1
            assert records[0].period_years == 0.0
            if case == "TtM: 5.5%":
                assert records[0].value_pct == 5.5
            elif case == "TTM: -3.2%":
                assert records[0].value_pct == -3.2
            else:
                assert records[0].value_pct == 5.0

    def test_last_year_pattern(self):
        """Test Last Year pattern: 'Last Year: 4%'"""
        records = self.parser.parse_cell("Last Year: 4%", "TEST", "stock_price_cagr", 1)
        assert len(records) == 1
        assert records[0].period_years == 1.0  # Last Year maps to 1 year
        assert records[0].value_pct == 4.0

    def test_last_year_pattern_variations(self):
        """Test Last Year pattern variations"""
        test_cases = [
            "Last Year: 4%",
            "Last Year 4%",
            "LastYear: 4%",
            "last year: 4%",  # case insensitive
            "LAST YEAR: 3.5%",
            "LaSt YeAr: -2.0%"
        ]
        for case in test_cases:
            records = self.parser.parse_cell(case, "TEST", "stock_price_cagr", 1)
            assert len(records) == 1
            assert records[0].period_years == 1.0
            if case == "LAST YEAR: 3.5%":
                assert records[0].value_pct == 3.5
            elif case == "LaSt YeAr: -2.0%":
                assert records[0].value_pct == -2.0
            else:
                assert records[0].value_pct == 4.0

    def test_ly_abbreviated_pattern(self):
        """Test LY abbreviated pattern: 'LY: 5%'"""
        records = self.parser.parse_cell("LY: 5%", "TEST", "compounded_sales_growth", 1)
        assert len(records) == 1
        assert records[0].period_years == 1.0  # LY maps to 1 year
        assert records[0].value_pct == 5.0

    def test_ly_abbreviated_pattern_variations(self):
        """Test LY abbreviated pattern variations"""
        test_cases = [
            "LY: 5%",
            "LY 5%",
            "LY:5%",
            "ly: 5%",  # case insensitive
            "lY: 3.5%",
            "LY: -1.0%"
        ]
        for case in test_cases:
            records = self.parser.parse_cell(case, "TEST", "stock_price_cagr", 1)
            assert len(records) == 1
            assert records[0].period_years == 1.0
            if case == "lY: 3.5%":
                assert records[0].value_pct == 3.5
            elif case == "LY: -1.0%":
                assert records[0].value_pct == -1.0
            else:
                assert records[0].value_pct == 5.0

    def test_multiple_expressions_in_one_cell(self):
        """Test multiple period expressions in one cell"""
        text = "10 Years: 21%\n5 Years: 15.5%\nTTM: 8%\nLast Year: 12%\nLY: 3.5%"
        records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)
        assert len(records) == 5

        # Check all records are present
        period_values = sorted([r.period_years for r in records])
        value_values = sorted([r.value_pct for r in records])
        assert period_values == [0.0, 1.0, 1.0, 5.0, 10.0]  # Note: two 1.0 from Last Year and LY
        assert value_values == [3.5, 8.0, 12.0, 15.5, 21.0]

    def test_multiple_metrics(self):
        """Test that different metrics are handled correctly"""
        text = "10 Years: 21%"
        metrics = [
            'compounded_sales_growth',
            'compounded_profit_growth',
            'stock_price_cagr',
            'roe'
        ]
        for metric in metrics:
            records = self.parser.parse_cell(text, "TEST_COMPANY", metric, 1)
            assert len(records) == 1
            assert records[0].company_id == "TEST_COMPANY"
            assert records[0].metric_type == metric
            assert records[0].period_years == 10.0
            assert records[0].value_pct == 21.0

    def test_correct_company_id(self):
        """Test that company_id is correctly preserved"""
        records = self.parser.parse_cell("10 Years: 21%", "HDFCBANK", "compounded_sales_growth", 42)
        assert len(records) == 1
        assert records[0].company_id == "HDFCBANK"
        assert records[0].metric_type == "compounded_sales_growth"
        assert records[0].period_years == 10.0
        assert records[0].value_pct == 21.0

    def test_output_columns(self):
        """Test that output has correct columns via to_dataframes"""
        self.parser.parse_cell("10 Years: 21%", "TEST", "compounded_sales_growth", 1)
        self.parser.parse_cell("TTM: 5%", "TEST", "compounded_profit_growth", 2)
        self.parser.parse_cell("Last Year: 3%", "TEST", "stock_price_cagr", 3)
        self.parser.parse_cell("LY: 4%", "TEST", "roe", 4)
        parsed_df, failures_df = self.parser.to_dataframes()

        # Check parsed dataframe columns
        expected_parsed_columns = ['company_id', 'metric_type', 'period_years', 'value_pct']
        assert list(parsed_df.columns) == expected_parsed_columns
        assert len(parsed_df) == 4

        # Check failures dataframe columns (should be empty)
        expected_failure_columns = ['id', 'company_id', 'metric_type', 'raw_text', 'reason']
        assert list(failures_df.columns) == expected_failure_columns
        assert len(failures_df) == 0

    def test_invalid_unmatched_text(self):
        """Test invalid/unmatched text generates parse failures"""
        text = "Some random text that doesn't match any pattern"
        records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)
        assert len(records) == 0  # No records parsed

        # Check that a failure was recorded
        assert len(self.parser.parse_failures) == 1
        failure = self.parser.parse_failures[0]
        assert failure.company_id == "TEST"
        assert failure.metric_type == "compounded_sales_growth"
        assert failure.raw_text == text
        assert failure.reason == 'No matching pattern found'
        assert failure.id == 1

    def test_blank_nan_handling(self):
        """Test blank/NaN handling"""
        # Test empty string
        records = self.parser.parse_cell("", "TEST", "compounded_sales_growth", 1)
        assert len(records) == 0
        assert len(self.parser.parse_failures) == 1
        assert self.parser.parse_failures[0].reason == 'Blank or NaN value'

        # Reset for next test
        self.parser.parse_failures.clear()

        # Test None/nan-like string
        records = self.parser.parse_cell("   ", "TEST", "compounded_sales_growth", 2)
        assert len(records) == 0
        assert len(self.parser.parse_failures) == 1
        assert self.parser.parse_failures[0].reason == 'Blank or NaN value'

        # Reset for next test
        self.parser.parse_failures.clear()

        # Test actual None
        records = self.parser.parse_cell(None, "TEST", "compounded_sales_growth", 3)
        assert len(records) == 0
        assert len(self.parser.parse_failures) == 1
        assert self.parser.parse_failures[0].reason == 'Blank or NaN value'

    def test_parse_failures_generation(self):
        """Test that parse_failures are properly generated"""
        # Mix of valid and invalid text
        text = "10 Years: 21%\nInvalid text here\nTTM: 5%\nAlso invalid\nLast Year: 3%"
        records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)

        # Should get 3 valid records
        assert len(records) == 3
        period_values = sorted([r.period_years for r in records])
        assert period_values == [0.0, 1.0, 10.0]

        # Should get 2 failures for the invalid text
        assert len(self.parser.parse_failures) == 2
        failure_texts = [f.raw_text for f in self.parser.parse_failures]
        assert "Invalid text here" in failure_texts
        assert "Also invalid" in failure_texts
        for failure in self.parser.parse_failures:
            assert failure.reason == 'No matching pattern found'

    def test_no_duplicate_records_from_same_input(self):
        """Test that duplicate records are not over-created from same input"""
        # Same expression multiple times - each should produce a record
        text = "10 Years: 21%\n10 Years: 21%"
        records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)
        # We SHOULD get 2 records here since there are 2 expressions
        assert len(records) == 2
        assert all(r.period_years == 10.0 and r.value_pct == 21.0 for r in records)

    def test_source_output_reconciliation_basic(self):
        """Test basic source/output reconciliation"""
        # This test verifies that what goes in comes out correctly
        test_cases = [
            ("10 Years: 21%", 10.0, 21.0),
            ("5.5 Years: 15.5%", 5.5, 15.5),
            ("TTM: 8%", 0.0, 8.0),
            ("Last Year: 12%", 1.0, 12.0),
            ("LY: 7%", 1.0, 7.0),
            ("3 Years: -5%", 3.0, -5.0),
            ("1 Year: 0%", 1.0, 0.0),
            ("2 Years: +3.5%", 2.0, 3.5)
        ]

        for text, expected_period, expected_value in test_cases:
            # Clear previous results
            self.parser.parsed_records.clear()
            self.parser.parse_failures.clear()

            records = self.parser.parse_cell(text, "TESTCOMPANY", "compounded_sales_growth", 1)
            assert len(records) == 1
            assert records[0].period_years == expected_period
            assert records[0].value_pct == expected_value
            assert records[0].company_id == "TESTCOMPANY"
            assert records[0].metric_type == "compounded_sales_growth"

    def test_roe_not_treated_as_cagr(self):
        """Test that ROE is not treated as a CAGR metric (handled elsewhere)"""
        # This is more of a conceptual test - the parser itself doesn't distinguish
        # between CAGR and non-CAGR metrics, but we can verify it parses ROE correctly
        records = self.parser.parse_cell("5 Years: 15.5%", "TEST", "roe", 1)
        assert len(records) == 1
        assert records[0].period_years == 5.0
        assert records[0].value_pct == 15.5
        assert records[0].metric_type == "roe"

    def test_standard_pattern_space_before_percent(self):
        """Test standard pattern with space before percent sign"""
        test_cases = [
            ("10 Years: 21 %", 10.0, 21.0),
            ("5 Years: 15.5 %", 5.0, 15.5),
            ("3 Years: -1 %", 3.0, -1.0),
            ("3 Years: +1 %", 3.0, 1.0)
        ]
        for text, expected_period, expected_value in test_cases:
            records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)
            assert len(records) == 1
            assert records[0].period_years == expected_period
            assert records[0].value_pct == expected_value

    def test_ttm_pattern_space_before_percent(self):
        """Test TTM pattern with space before percent sign"""
        test_cases = [
            ("TTM: 5 %", 0.0, 5.0),
            ("TTM: -3.2 %", 0.0, -3.2),
            ("TTM: 0 %", 0.0, 0.0)
        ]
        for text, expected_period, expected_value in test_cases:
            records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)
            assert len(records) == 1
            assert records[0].period_years == expected_period
            assert records[0].value_pct == expected_value

    def test_last_year_pattern_space_before_percent(self):
        """Test Last Year pattern with space before percent sign"""
        test_cases = [
            ("Last Year: 4 %", 1.0, 4.0),
            ("Last Year: -2.5 %", 1.0, -2.5),
            ("Last Year: 0 %", 1.0, 0.0)
        ]
        for text, expected_period, expected_value in test_cases:
            records = self.parser.parse_cell(text, "TEST", "stock_price_cagr", 1)
            assert len(records) == 1
            assert records[0].period_years == expected_period
            assert records[0].value_pct == expected_value

    def test_ly_pattern_space_before_percent(self):
        """Test LY pattern with space before percent sign"""
        test_cases = [
            ("LY: 5 %", 1.0, 5.0),
            ("LY: -1.0 %", 1.0, -1.0),
            ("LY: 3.5 %", 1.0, 3.5)
        ]
        for text, expected_period, expected_value in test_cases:
            records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)
            assert len(records) == 1
            assert records[0].period_years == expected_period
            assert records[0].value_pct == expected_value

    def test_regression_space_before_percent(self):
        """Test regression cases for space before percent sign"""
        # Standard pattern cases
        standard_cases = [
            ("10 Years: 21%", 10.0, 21.0),
            ("10 Years: 21 %", 10.0, 21.0),
            ("5 Years: 15.5%", 5.0, 15.5),
            ("5 Years: 15.5 %", 5.0, 15.5),
            ("3 Years: -1%", 3.0, -1.0),
            ("3 Years: -1 %", 3.0, -1.0)
        ]

        for text, expected_period, expected_value in standard_cases:
            records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)
            assert len(records) == 1, f"Failed to parse: {text}"
            assert records[0].period_years == expected_period, f"Wrong period for: {text}"
            assert records[0].value_pct == expected_value, f"Wrong value for: {text}"

        # TTM pattern cases
        ttm_cases = [
            ("TTM: 21%", 0.0, 21.0),
            ("TTM: 21 %", 0.0, 21.0),
            ("TTM: 15.5%", 0.0, 15.5),
            ("TTM: 15.5 %", 0.0, 15.5),
            ("TTM: -1%", 0.0, -1.0),
            ("TTM: -1 %", 0.0, -1.0)
        ]

        for text, expected_period, expected_value in ttm_cases:
            records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)
            assert len(records) == 1, f"Failed to parse: {text}"
            assert records[0].period_years == expected_period, f"Wrong period for: {text}"
            assert records[0].value_pct == expected_value, f"Wrong value for: {text}"

        # Last Year pattern cases
        ly_cases = [
            ("Last Year: 21%", 1.0, 21.0),
            ("Last Year: 21 %", 1.0, 21.0),
            ("Last Year: 15.5%", 1.0, 15.5),
            ("Last Year: 15.5 %", 1.0, 15.5),
            ("Last Year: -1%", 1.0, -1.0),
            ("Last Year: -1 %", 1.0, -1.0)
        ]

        for text, expected_period, expected_value in ly_cases:
            records = self.parser.parse_cell(text, "TEST", "stock_price_cagr", 1)
            assert len(records) == 1, f"Failed to parse: {text}"
            assert records[0].period_years == expected_period, f"Wrong period for: {text}"
            assert records[0].value_pct == expected_value, f"Wrong value for: {text}"

        # LY pattern cases
        ly_abbr_cases = [
            ("LY: 21%", 1.0, 21.0),
            ("LY: 21 %", 1.0, 21.0),
            ("LY: 15.5%", 1.0, 15.5),
            ("LY: 15.5 %", 1.0, 15.5),
            ("LY: -1%", 1.0, -1.0),
            ("LY: -1 %", 1.0, -1.0)
        ]

        for text, expected_period, expected_value in ly_abbr_cases:
            records = self.parser.parse_cell(text, "TEST", "compounded_sales_growth", 1)
            assert len(records) == 1, f"Failed to parse: {text}"
            assert records[0].period_years == expected_period, f"Wrong period for: {text}"
            assert records[0].value_pct == expected_value, f"Wrong value for: {text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])