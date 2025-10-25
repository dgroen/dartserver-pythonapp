"""
Checkout Advice Module for Darts Games
Provides optimal dart combinations to finish/checkout a game
"""

from typing import ClassVar


class CheckoutAdvice:
    """Provides checkout advice for darts games"""

    # Common checkout paths for scores 2-170
    # Format: score -> list of suggested dart combinations
    CHECKOUTS: ClassVar[dict[int, list[str]]] = {
        # Simple doubles (2-40)
        2: ["D1"],
        4: ["D2"],
        6: ["D3"],
        8: ["D4"],
        10: ["D5"],
        12: ["D6"],
        14: ["D7"],
        16: ["D8"],
        18: ["D9"],
        20: ["D10"],
        22: ["D11"],
        24: ["D12"],
        26: ["D13"],
        28: ["D14"],
        30: ["D15"],
        32: ["D16"],
        34: ["D17"],
        36: ["D18"],
        38: ["D19"],
        40: ["D20"],
        # Common 2-dart finishes (41-110)
        41: ["9, D16"],
        42: ["10, D16"],
        43: ["11, D16"],
        44: ["12, D16"],
        45: ["13, D16"],
        46: ["14, D16"],
        47: ["15, D16"],
        48: ["16, D16"],
        49: ["17, D16"],
        50: ["18, D16", "Bull"],
        51: ["19, D16"],
        52: ["20, D16"],
        53: ["13, D20"],
        54: ["14, D20"],
        55: ["15, D20"],
        56: ["16, D20"],
        57: ["17, D20"],
        58: ["18, D20"],
        59: ["19, D20"],
        60: ["20, D20"],
        61: ["T15, D8"],
        62: ["T10, D16"],
        63: ["T13, D12"],
        64: ["T16, D8"],
        65: ["T11, D16"],
        66: ["T10, D18"],
        67: ["T17, D8"],
        68: ["T20, D4"],
        69: ["T19, D6"],
        70: ["T18, D8"],
        71: ["T13, D16"],
        72: ["T16, D12"],
        73: ["T19, D8"],
        74: ["T14, D16"],
        75: ["T17, D12"],
        76: ["T20, D8"],
        77: ["T19, D10"],
        78: ["T18, D12"],
        79: ["T13, D20"],
        80: ["T20, D10"],
        81: ["T19, D12"],
        82: ["T14, D20", "Bull, D16"],
        83: ["T17, D16"],
        84: ["T20, D12"],
        85: ["T15, D20"],
        86: ["T18, D16"],
        87: ["T17, D18"],
        88: ["T20, D14"],
        89: ["T19, D16"],
        90: ["T20, D15"],
        91: ["T17, D20"],
        92: ["T20, D16"],
        93: ["T19, D18"],
        94: ["T18, D20"],
        95: ["T19, D19"],
        96: ["T20, D18"],
        97: ["T19, D20"],
        98: ["T20, D19"],
        99: ["T19, D21"],
        100: ["T20, D20"],
        101: ["T17, Bull"],
        102: ["T20, D21"],
        103: ["T19, D23"],
        104: ["T18, Bull"],
        105: ["T19, D24"],
        106: ["T20, D23"],
        107: ["T19, Bull"],
        108: ["T20, D24"],
        109: ["T20, D24.5"],
        110: ["T20, Bull"],
        # 3-dart finishes (111-170)
        111: ["T19, T14, D6"],
        112: ["T20, T12, D8"],
        113: ["T19, T16, D7"],
        114: ["T20, T14, D6"],
        115: ["T19, T18, D4"],
        116: ["T20, T16, D4"],
        117: ["T20, T17, D3"],
        118: ["T20, T18, D2"],
        119: ["T19, T12, D13"],
        120: ["T20, 20, D20"],
        121: ["T17, T10, D20"],
        122: ["T18, T18, D7"],
        123: ["T19, T16, D9"],
        124: ["T20, T14, D11"],
        125: ["T18, T11, D16"],
        126: ["T19, T19, D6"],
        127: ["T20, T17, D8"],
        128: ["T18, T14, D13"],
        129: ["T19, T16, D12"],
        130: ["T20, T20, D5"],
        131: ["T20, T13, D16"],
        132: ["T20, T16, D12"],
        133: ["T20, T19, D8"],
        134: ["T20, T14, D16"],
        135: ["T20, T17, D12"],
        136: ["T20, T20, D8"],
        137: ["T20, T19, D10"],
        138: ["T20, T18, D12"],
        139: ["T20, T13, D20"],
        140: ["T20, T20, D10"],
        141: ["T20, T19, D12"],
        142: ["T20, T14, D20"],
        143: ["T20, T17, D16"],
        144: ["T20, T20, D12"],
        145: ["T20, T15, D20"],
        146: ["T20, T18, D16"],
        147: ["T20, T17, D18"],
        148: ["T20, T20, D14"],
        149: ["T20, T19, D16"],
        150: ["T20, T20, D15"],
        151: ["T20, T17, D20"],
        152: ["T20, T20, D16"],
        153: ["T20, T19, D18"],
        154: ["T20, T18, D20"],
        155: ["T20, T19, D19"],
        156: ["T20, T20, D18"],
        157: ["T20, T19, D20"],
        158: ["T20, T20, D19"],
        159: ["T19, T20, D21"],
        160: ["T20, T20, D20"],
        161: ["T20, T17, Bull"],
        164: ["T20, T18, Bull"],
        167: ["T20, T19, Bull"],
        170: ["T20, T20, Bull"],
    }

    @classmethod
    def get_advice(cls, remaining_score, double_out_required=False):  # noqa: ARG003
        """
        Get checkout advice for a given score

        Args:
            remaining_score: The score remaining to finish
            double_out_required: Whether a double is required to finish (reserved for future use)

        Returns:
            Dictionary with advice information or None if no advice available
        """
        if remaining_score <= 0 or remaining_score > 170:
            return None

        # Score of 1 is impossible to finish
        if remaining_score == 1:
            return {
                "score": remaining_score,
                "possible": False,
                "advice": "Score of 1 cannot be finished",
            }

        # Check if we have a checkout path for this score
        if remaining_score in cls.CHECKOUTS:
            checkout_options = cls.CHECKOUTS[remaining_score]
            return {
                "score": remaining_score,
                "possible": True,
                "advice": checkout_options[0],  # Primary suggestion
                "alternatives": checkout_options[1:] if len(checkout_options) > 1 else [],
            }

        # For scores not in our checkout table
        if remaining_score <= 40 and remaining_score % 2 == 0:
            # Even scores up to 40 can be finished with a double
            double_target = remaining_score // 2
            return {
                "score": remaining_score,
                "possible": True,
                "advice": f"D{double_target}",
            }

        # Odd scores between 40-50
        if 40 < remaining_score < 50:
            # Suggest a single followed by a double
            single_score = remaining_score - 32  # Leave 32 for D16
            return {
                "score": remaining_score,
                "possible": True,
                "advice": f"{single_score}, D16",
            }

        # For other scores, suggest getting down to a known checkout
        if remaining_score > 170:
            target_score = 170
        else:
            # Find the nearest lower checkout score
            target_score = 60
            for score in sorted(cls.CHECKOUTS.keys(), reverse=True):
                if score < remaining_score:
                    target_score = score
                    break

        points_to_score = remaining_score - target_score
        return {
            "score": remaining_score,
            "possible": True,
            "advice": f"Score {points_to_score} to leave {target_score}",
        }

    @classmethod
    def format_advice(cls, advice_data):
        """
        Format advice data into a human-readable string

        Args:
            advice_data: Dictionary from get_advice()

        Returns:
            Formatted string for display
        """
        if not advice_data:
            return ""

        if not advice_data.get("possible", True):
            return advice_data.get("advice", "")

        advice = advice_data.get("advice", "")
        score = advice_data.get("score", 0)

        # Format the advice string
        if score <= 170:
            return f"Checkout {score}: {advice}"

        return advice
