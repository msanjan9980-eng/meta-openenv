# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Package-facing aliases for the insurance claim validation environment."""

from environment.schemas import ClaimAction, ClaimObservation

MyEnv2Action = ClaimAction
MyEnv2Observation = ClaimObservation

__all__ = [
    "ClaimAction",
    "ClaimObservation",
    "MyEnv2Action",
    "MyEnv2Observation",
]
