# Configuration dictionary for intent extraction using regex patterns

PATTERN_CONFIG = {
    "TEST_SUITE": {
        "label": "Test_suite",
        # Improved pattern: stops at space, comma, 'and', or punctuation
        "patterns": [
            r"(?:test[_\s]?suite(?: is| equals| equal to)?|suite)\s*['\"]?([^\s,'\"?]+)['\"]?",
            r"['\"]?([^\s,'\"?]+)['\"]?\s*(?:test[_\s]?suite|suite)",
        ],
        "quote": True,
    },
    "PLATFORM": {
        "label": "Platform",
        # Improved pattern: handles both quoted and unquoted inputs
        "patterns": [
            r"(?:platform(?: is| equals| equal to)?)\s*['\"]?([^\s,'\"?]+)['\"]?",
            r"['\"]?([^\s,'\"?]+)['\"]?\s*(?:platform)",
        ],
        "quote": True,
    },
    "RELEASE_VERSION": {
        "label": "Release version",
        # Improved pattern: stops before common boundaries
        "patterns": [
            r"(?:release(?:[_\s]?version)?(?: is| equals| equal to)?)\s*['\"]?([^\s,'\"?]+)['\"]?",
            r"['\"]?([^\s,'\"?]+)['\"]?\s*(?:release(?:[_\s]?version)?)",
        ],
        "quote": False,
    },
    "TESTCASES_EXECUTED": {
        "label": "Metric",
        "metric_name": "testcases executed",
        "patterns": [r"(?:test[\s]?cases? executed|executed test[\s]?cases?)"],
        "is_metric": True,
    },
    "TESTCASES_PASSED": {
        "label": "Metric",
        "metric_name": "testcases passed",
        "patterns": [r"(?:test[\s]?cases? passed|passed test[\s]?cases?)"],
        "is_metric": True,
    },
}

