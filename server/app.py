# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Root-level server entry point — delegates to the package server."""

from insurance_claim_validation.server.app import app, main  # noqa: F401


if __name__ == "__main__":
    main()
