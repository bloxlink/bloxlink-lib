from bloxlink_lib import CoerciveSet, SnowflakeSet
import pytest


class TestCoerciveSets:
    """Tests related to coercive sets."""

    @pytest.mark.parametrize("input_set, expected_length", [
        ([1, 2, 3, 4, 5], 5),
    ])
    def test_coercive_set_length(self, input_set, expected_length):
        """Test that the coercive set has the correct length"""
        test_set = CoerciveSet[int](input_set)
        assert len(test_set) == expected_length, f"CoerciveSet should have {
            expected_length} items."

    @pytest.mark.parametrize("input_set, item_to_add, expected_length", [
        ([1, 2, 3, 4, 5], 6, 6),
    ])
    def test_coercive_set_add(self, input_set, item_to_add, expected_length):
        """Test that the coercive set adds an item correctly"""
        test_set = CoerciveSet[int](input_set)
        test_set.add(item_to_add)
        assert len(test_set) == expected_length, f"CoerciveSet should have {
            expected_length} items."

    @pytest.mark.parametrize("input_set, expected_str", [
        ([1, 2, 3, 4, 5], "1, 2, 3, 4, 5"),
    ])
    def test_coercive_set_str(self, input_set, expected_str):
        """Test that the coercive set returns a string correctly"""
        test_set = CoerciveSet[int](input_set)
        assert str(
            test_set) == expected_str, f"CoerciveSet should return a string of the items."

    @pytest.mark.parametrize("input_set, item_to_check", [
        ([1, 2, 3, 4, 5], 3),
    ])
    def test_coercive_set_contains(self, input_set, item_to_check):
        """Test that the coercive set contains an item correctly"""
        test_set = CoerciveSet[int](input_set)
        assert item_to_check in test_set, f"CoerciveSet should contain {
            item_to_check}."

    @pytest.mark.parametrize("input_set, item_to_remove, expected_length", [
        ([1, 2, 3, 4, 5], 3, 4),
    ])
    def test_coercive_set_remove(self, input_set, item_to_remove, expected_length):
        """Test that the coercive set removes an item correctly"""
        test_set = CoerciveSet[int](input_set)
        test_set.remove(item_to_remove)
        assert len(test_set) == expected_length, f"CoerciveSet should have {
            expected_length} items."

    @pytest.mark.parametrize("input_set, item_to_discard, expected_length", [
        ([1, 2, 3, 4, 5], 3, 4),
    ])
    def test_coercive_set_discard(self, input_set, item_to_discard, expected_length):
        """Test that the coercive set discards an item correctly"""
        test_set = CoerciveSet[int](input_set)
        test_set.discard(item_to_discard)
        assert len(test_set) == expected_length, f"CoerciveSet should have {
            expected_length} items."

    @pytest.mark.parametrize("input_set, items_to_update, expected_length", [
        ([1, 2, 3, 4, 5], [6, 7], 7),
    ])
    def test_coercive_set_update(self, input_set, items_to_update, expected_length):
        """Test that the coercive set updates correctly"""
        test_set = CoerciveSet[int](input_set)
        test_set.update(items_to_update)
        assert len(test_set) == expected_length, f"CoerciveSet should have {
            expected_length} items."

    @pytest.mark.parametrize("set1, set2, expected_length", [
        ([1, 2, 3, 4, 5], [4, 5, 6, 7, 8], 2),
    ])
    def test_coercive_set_intersection(self, set1, set2, expected_length):
        """Test that the coercive set intersects correctly"""
        test_set_1 = CoerciveSet[int](set1)
        test_set_2 = CoerciveSet[int](set2)
        intersection = test_set_1.intersection(test_set_2)
        assert len(intersection) == expected_length, f"Intersection should have {
            expected_length} items."

    @pytest.mark.parametrize("set1, set2, expected_length", [
        ([1, 2, 3, 4, 5], [4, 5, 6, 7, 8], 3),
    ])
    def test_coercive_set_difference(self, set1, set2, expected_length):
        """Test that the coercive set differences correctly"""
        test_set_1 = CoerciveSet[int](set1)
        test_set_2 = CoerciveSet[int](set2)
        difference = test_set_1.difference(test_set_2)
        assert len(difference) == expected_length, f"Difference should have {
            expected_length} items."

    @pytest.mark.parametrize("set1, set2, expected_length", [
        ([1, 2, 3, 4, 5], [4, 5, 6, 7, 8], 6),
    ])
    def test_coercive_set_symmetric_difference(self, set1, set2, expected_length):
        """Test that the coercive set symmetric differences correctly"""
        test_set_1 = CoerciveSet[int](set1)
        test_set_2 = CoerciveSet[int](set2)
        symmetric_difference = test_set_1.symmetric_difference(test_set_2)
        assert len(symmetric_difference) == expected_length, f"Symmetric difference should have {
            expected_length} items."

    @pytest.mark.parametrize("set1, set2, expected_length", [
        ([1, 2, 3, 4, 5], [4, 5, 6, 7, 8], 8),
    ])
    def test_coercive_set_union(self, set1, set2, expected_length):
        """Test that the coercive set unions correctly"""
        test_set_1 = CoerciveSet[int](set1)
        test_set_2 = CoerciveSet[int](set2)
        union = test_set_1.union(test_set_2)
        assert len(union) == expected_length, f"Union should have {
            expected_length} items."

    @pytest.mark.parametrize("input_set, expected_list", [
        ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]),
    ])
    def test_coercive_set_iter(self, input_set, expected_list):
        """Test that the coercive set iterates correctly"""
        test_set = CoerciveSet[int](input_set)
        assert list(
            test_set) == expected_list, "CoerciveSet should iterate correctly."

    @pytest.mark.parametrize("input_set, expected_list", [
        (["1", "2", "3", "4", "5"], [1, 2, 3, 4, 5]),
    ])
    def test_coercive_set_coerce(self, input_set, expected_list):
        """Test that the coercive set coerces correctly"""
        test_set = CoerciveSet[int](input_set)
        assert list(
            test_set) == expected_list, "CoerciveSet should coerce correctly."

    @pytest.mark.parametrize("input_set", [
        (["a", "b", "c", "d", "e"]),
        (["1", "2", "3", "4", "5", "a"]),
    ])
    def test_coercive_set_coerce_error(self, input_set):
        """Test that the coercive set coerces an error correctly"""
        with pytest.raises(TypeError):
            CoerciveSet[int](input_set)

    @pytest.mark.parametrize("input_set, expected_list", [
        ([1, 2, 3, 4, 5], ["1", "2", "3", "4", "5"]),
    ])
    def test_coercive_set_coerce_str(self, input_set, expected_list):
        """Test that the coercive set coerces a string correctly"""
        test_set = CoerciveSet[str](input_set)
        expected_set = CoerciveSet[str](expected_list)
        assert test_set == expected_set, "CoerciveSet should coerce to the expected list of strings."


class TestSnowflakeSets:
    """Tests for SnowflakeSets"""

    @pytest.mark.parametrize("input_set, expected_length", [
        ([1, 2, 3, 4, 5], 5),
    ])
    def test_snowflake_set_length(self, input_set, expected_length):
        """Test that the snowflake set has the correct length"""
        test_set = SnowflakeSet(input_set)
        assert len(test_set) == expected_length, f"SnowflakeSet should have {
            expected_length} items."

    @pytest.mark.parametrize("input_set, item_to_add, expected_length", [
        ([1, 2, 3, 4, 5], 6, 6),
    ])
    def test_snowflake_set_add(self, input_set, item_to_add, expected_length):
        """Test that the snowflake set adds an item correctly"""
        test_set = SnowflakeSet(input_set)
        test_set.add(item_to_add)
        assert len(test_set) == expected_length, f"SnowflakeSet should have {
            expected_length} items."

    @pytest.mark.parametrize("input_set, expected_str", [
        ([1, 2, 3, 4, 5], "1, 2, 3, 4, 5"),
    ])
    def test_snowflake_set_str(self, input_set, expected_str):
        """Test that the snowflake set returns a string correctly"""
        test_set = SnowflakeSet(input_set)
        assert str(
            test_set) == expected_str, f"SnowflakeSet should return a string of the items."

    @pytest.mark.parametrize("input_set, item_to_check", [
        ([1, 2, 3, 4, 5], 3),
    ])
    def test_snowflake_set_contains(self, input_set, item_to_check):
        """Test that the snowflake set contains an item correctly"""
        test_set = SnowflakeSet(input_set)
        assert item_to_check in test_set, f"SnowflakeSet should contain {
            item_to_check}."

    @pytest.mark.parametrize("input_set, expected_set",
                             [
                                 (["1", "2", "3", "4", "5"], [1, 2, 3, 4, 5]),
                             ])
    def test_snowflake_set_coerce(self, input_set, expected_set):
        """Test that the snowflake set coerces correctly"""
        test_set = SnowflakeSet(input_set)
        assert list(
            test_set) == expected_set, "SnowflakeSet should coerce correctly."

    def test_snowflake_set_empty_set(self):
        """Test that the snowflake set is empty"""

        test_set = SnowflakeSet()
        assert len(test_set) == 0, "SnowflakeSet should be empty."
