# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import random

import pytest

from iceberg.schema import Schema
from iceberg.utils.bin_packing import PackingIterator


@pytest.mark.parametrize(
    "splits, lookback, split_size, open_cost",
    [
        ([random.randint(0, 64) for x in range(200)], 20, 128, 4),  # random splits
        ([], 20, 128, 4),  # no splits
        (
            [0] * 100 + [random.randint(0, 64) in range(10)] + [0] * 100,
            20,
            128,
            4,
        ),  # sparse
    ],
)
def test_bin_packing(splits, lookback, split_size, open_cost):
    def weight_func(x):
        return max(x, open_cost)

    item_list_sums = [sum(item) for item in PackingIterator(splits, split_size, lookback, weight_func)]
    assert all([split_size >= item_sum >= 0 for item_sum in item_list_sums])


@pytest.mark.parametrize(
    "splits, target_weight, lookback, largest_bin_first, expected_lists",
    [
        (
            [36, 36, 36, 36, 73, 110, 128],
            128,
            2,
            True,
            [[110], [128], [36, 73], [36, 36, 36]],
        ),
        (
            [36, 36, 36, 36, 73, 110, 128],
            128,
            2,
            False,
            [[36, 36, 36], [36, 73], [110], [128]],
        ),
        (
            [64, 64, 128, 32, 32, 32, 32],
            128,
            1,
            True,
            [[64, 64], [128], [32, 32, 32, 32]],
        ),
        (
            [64, 64, 128, 32, 32, 32, 32],
            128,
            1,
            False,
            [[64, 64], [128], [32, 32, 32, 32]],
        ),
    ],
)
def test_bin_packing_lookback(splits, target_weight, lookback, largest_bin_first, expected_lists):
    def weight_func(x):
        return x

    assert list(PackingIterator(splits, target_weight, lookback, weight_func, largest_bin_first)) == expected_lists


def test_serialize_schema(table_schema_simple: Schema):
    actual = table_schema_simple.json()
    expected = """{"fields": [{"id": 1, "name": "foo", "type": "string", "required": false}, {"id": 2, "name": "bar", "type": "int", "required": true}, {"id": 3, "name": "baz", "type": "boolean", "required": false}], "schema-id": 1, "identifier-field-ids": [1]}"""
    assert actual == expected


def test_deserialize_schema(table_schema_simple: Schema):
    actual = Schema.parse_raw(
        """{"fields": [{"id": 1, "name": "foo", "type": "string", "required": false}, {"id": 2, "name": "bar", "type": "int", "required": true}, {"id": 3, "name": "baz", "type": "boolean", "required": false}], "schema-id": 1, "identifier-field-ids": [1]}"""
    )
    expected = table_schema_simple
    assert actual == expected
