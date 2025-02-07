import unittest
import pandas as pd
import numpy as np
from pylbmisc.dm import to_bool, to_integer, to_numeric, to_datetime, to_date, to_categorical, to_noyes, to_sex, to_recist, to_other_specify, to_string

class TestDMFunctions(unittest.TestCase):

    def test_to_bool(self):
        series = pd.Series([1, 0, 1, 0, np.nan])
        expected = pd.Series([True, False, True, False, pd.NA], dtype="boolean")
        result = to_bool(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_integer(self):
        series = pd.Series([1.0, 2.0, 3.0, 4.0, np.nan])
        expected = pd.Series([1, 2, 3, 4, pd.NA], dtype="Int64")
        result = to_integer(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_numeric(self):
        series = pd.Series(["1.1", "2,1", "3.0", "4.5", ""])
        expected = pd.Series([1.1, 2.1, 3.0, 4.5, np.nan], dtype="Float64")
        result = to_numeric(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_datetime(self):
        series = pd.Series(["2020-01-01", "2021-01-01", "2022-01-01", "", np.nan])
        expected = pd.to_datetime(pd.Series(["2020-01-01", "2021-01-01", "2022-01-01", pd.NaT, pd.NaT]))
        result = to_datetime(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_date(self):
        series = pd.Series(["2020-01-01 12:34:56", "2021-01-01 00:00:00", "2022-01-01 23:59:59", "", np.nan])
        expected = pd.to_datetime(pd.Series(["2020-01-01", "2021-01-01", "2022-01-01", pd.NaT, pd.NaT])).dt.floor("D")
        result = to_date(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_categorical(self):
        series = pd.Series(["A", "B", "A", "C", ""])
        expected = pd.Categorical(["A", "B", "A", "C", pd.NA])
        result = to_categorical(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_noyes(self):
        series = pd.Series(["yes", "no", "yes", "no", ""])
        expected = pd.Categorical(["yes", "no", "yes", "no", pd.NA], categories=["no", "yes"])
        result = to_noyes(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_sex(self):
        series = pd.Series(["M", "F", "m", "f", ""])
        expected = pd.Categorical(["male", "female", "male", "female", pd.NA], categories=["male", "female"])
        result = to_sex(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_recist(self):
        series = pd.Series(["CR", "PR", "SD", "PD", ""])
        expected = pd.Categorical(["CR", "PR", "SD", "PD", pd.NA], categories=["CR", "PR", "SD", "PD"])
        result = to_recist(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_other_specify(self):
        series = pd.Series(["foo", "bar", "foo", "baz", ""])
        expected = pd.Categorical(["foo", "bar", "foo", "baz", pd.NA], categories=["foo", "bar", "baz"])
        result = to_other_specify(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_string(self):
        series = pd.Series([1, 2, 3, 4, np.nan])
        expected = pd.Series(["1", "2", "3", "4", "nan"])
        result = to_string(series)
        pd.testing.assert_series_equal(result, expected)

if __name__ == '__main__':
    unittest.main()
