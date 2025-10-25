"""
Unit tests for checkout advice module
"""


from checkout_advice import CheckoutAdvice


class TestCheckoutAdvice:
    """Test cases for CheckoutAdvice class"""

    def test_simple_double_checkouts(self):
        """Test simple double checkouts (2-40)"""
        # Test some basic doubles
        advice = CheckoutAdvice.get_advice(40)
        assert advice is not None
        assert advice["possible"] is True
        assert "D20" in advice["advice"]

        advice = CheckoutAdvice.get_advice(20)
        assert advice is not None
        assert advice["possible"] is True
        assert "D10" in advice["advice"]

    def test_impossible_score_one(self):
        """Test that score of 1 is marked as impossible"""
        advice = CheckoutAdvice.get_advice(1)
        assert advice is not None
        assert advice["possible"] is False
        assert "cannot be finished" in advice["advice"]

    def test_common_2dart_finishes(self):
        """Test common 2-dart finishes"""
        advice = CheckoutAdvice.get_advice(50)
        assert advice is not None
        assert advice["possible"] is True
        # Should suggest either "18, D16" or "Bull"
        assert "D16" in advice["advice"] or "Bull" in advice["advice"]

        advice = CheckoutAdvice.get_advice(100)
        assert advice is not None
        assert advice["possible"] is True
        assert "T20" in advice["advice"]
        assert "D20" in advice["advice"]

    def test_3dart_finishes(self):
        """Test 3-dart finishes"""
        advice = CheckoutAdvice.get_advice(170)
        assert advice is not None
        assert advice["possible"] is True
        assert "T20" in advice["advice"]
        assert "Bull" in advice["advice"]

        advice = CheckoutAdvice.get_advice(120)
        assert advice is not None
        assert advice["possible"] is True
        assert "T20" in advice["advice"]

    def test_score_too_high(self):
        """Test scores above 170"""
        advice = CheckoutAdvice.get_advice(200)
        # Scores above 170 return None
        assert advice is None

        advice = CheckoutAdvice.get_advice(171)
        assert advice is None

    def test_score_zero_or_negative(self):
        """Test edge cases with zero or negative scores"""
        advice = CheckoutAdvice.get_advice(0)
        assert advice is None

        advice = CheckoutAdvice.get_advice(-10)
        assert advice is None

    def test_mid_range_scores(self):
        """Test mid-range scores (60-110)"""
        advice = CheckoutAdvice.get_advice(60)
        assert advice is not None
        assert advice["possible"] is True

        advice = CheckoutAdvice.get_advice(81)
        assert advice is not None
        assert advice["possible"] is True

    def test_format_advice(self):
        """Test advice formatting"""
        advice_data = {
            "score": 100,
            "possible": True,
            "advice": "T20, D20",
        }
        formatted = CheckoutAdvice.format_advice(advice_data)
        assert "100" in formatted
        assert "T20, D20" in formatted

    def test_format_advice_impossible(self):
        """Test formatting for impossible checkouts"""
        advice_data = {
            "score": 1,
            "possible": False,
            "advice": "Score of 1 cannot be finished",
        }
        formatted = CheckoutAdvice.format_advice(advice_data)
        assert "cannot be finished" in formatted

    def test_format_advice_empty(self):
        """Test formatting with no advice data"""
        formatted = CheckoutAdvice.format_advice(None)
        assert formatted == ""

    def test_double_out_parameter(self):
        """Test that double_out parameter is accepted (even if not currently used)"""
        advice = CheckoutAdvice.get_advice(40, double_out_required=True)
        assert advice is not None

        advice = CheckoutAdvice.get_advice(40, double_out_required=False)
        assert advice is not None

    def test_all_checkout_scores_valid(self):
        """Test that all scores in CHECKOUTS dict return valid advice"""
        for score in CheckoutAdvice.CHECKOUTS:
            advice = CheckoutAdvice.get_advice(score)
            assert advice is not None
            assert advice["possible"] is True
            assert advice["advice"] is not None
            assert len(advice["advice"]) > 0
