import unittest
import pandas as pd
import numpy as np
from pylbmisc.dm import to_bool, to_integer, to_numeric, to_datetime, \
    to_date, to_categorical, to_noyes, to_sex, to_recist, to_other_specify, \
    to_string


class TestDMFunctions(unittest.TestCase):

    def test_to_bool(self):
        series = pd.Series([1., 0, 1., 0, np.nan])
        expected = pd.Series([True, False, True, False, pd.NA],
                             dtype="boolean[pyarrow]")
        result = to_bool(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_integer_float(self):
        series = pd.Series([1., 2., np.nan])
        expected = pd.Series([1, 2,  pd.NA], dtype="Int64")
        result = to_integer(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_integer_string(self):
        series = pd.Series(["2001", "2011", "1999", np.nan])
        expected = pd.Series([2001, 2011, 1999, pd.NA], dtype="Int64")
        result = to_integer(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_numeric_string(self):
        series = pd.Series(["2001", "2011", "1999", np.nan])
        expected = pd.Series([2001, 2011, 1999, pd.NA], dtype="int64[pyarrow]")
        result = to_numeric(series)
        pd.testing.assert_series_equal(result, expected)

    def test_to_numeric(self):
        series = pd.Series(["1.1", "2,1", "3.0", "4.5", ""])
        expected = pd.Series([1.1, 2.1, 3.0, 4.5, np.nan], dtype="float64[pyarrow]")
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
        series = pd.Series(["A", "B", "A", "C", "", np.nan])
        expected = pd.Categorical(["A", "B", "A", "C", pd.NA, pd.NA])
        result = to_categorical(series, levels=["A", "B", "C"])
        # categorical in pandas seems to be extension arrays
        # https://pandas.pydata.org/community/blog/extension-arrays.html
        pd.testing.assert_extension_array_equal(result, expected)

    def test_to_noyes(self):
        series = pd.Series(["","yes","no","boh", "si", np.nan])
        expected = pd.Categorical([pd.NA, "yes", "no", pd.NA, "yes", pd.NA], categories=["no", "yes"])
        result = to_noyes(series)
        pd.testing.assert_extension_array_equal(result, expected)

    def test_to_sex(self):
        series = pd.Series([""    ,"m","f"," m", "Fm", np.nan])
        expected = pd.Categorical([pd.NA , "male", "female", "male", "female", pd.NA],
                                  categories=["male", "female"])
        result = to_sex(series)
        pd.testing.assert_extension_array_equal(result, expected)

    def test_to_recist(self):
        series = pd.Series(["RC", "PD", "SD", "PR", "RP", "boh", np.nan])
        expected = pd.Categorical(["CR", "PD", "SD", "PR", "PR", pd.NA, pd.NA],
                                  categories=["CR", "PR", "SD", "PD"])
        result = to_recist(series)
        pd.testing.assert_extension_array_equal(result, expected)

    def test_to_other_specify(self):
        series = pd.Series(["foo", "bar", "foo", "baz", ""])
        expected = pd.Categorical(["foo", "bar", "foo", "baz", pd.NA],
                                  categories=["foo", "bar", "baz"])
        result = to_other_specify(series)
        pd.testing.assert_extension_array_equal(result, expected)

    def test_to_string(self):
        series = pd.Series([1, 2, 3, 4, np.nan]).astype("Int32")
        expected = pd.Series(["1", "2", "3", "4", pd.NA])
        result = to_string(series)
        pd.testing.assert_series_equal(result, expected)

if __name__ == "__main__":
    unittest.main()
