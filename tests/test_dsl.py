"""Fenced DSL: compilation, safety, negative-shift detection, PIT re-execution."""
from __future__ import annotations

import pandas as pd
import pytest
from generator.market import build_market

from signalgate.dsl import DslError, as_written_and_pit, compile_program, execute


@pytest.fixture(scope="module")
def market():
    return build_market(20260828, n_assets=30, n_days=320, n_distressed=4)


def test_compile_and_execute(market):
    prog = compile_program("score = rank(pct_change(close, 63))")
    out = execute(prog, market.as_fields(), pit=False)
    assert out.shape == market.close.shape
    assert out.notna().any().any()


def test_requires_score(market):
    with pytest.raises(DslError):
        compile_program("x = rank(close)")


def test_forbidden_attribute(market):
    with pytest.raises(DslError):
        compile_program("score = close.to_csv('/tmp/x')")


def test_forbidden_lambda(market):
    with pytest.raises(DslError):
        compile_program("f = lambda x: x\nscore = rank(close)")


def test_max_negative_shift_detection():
    assert compile_program("score = rank(shift(close, -3))").max_negative_shift == 3
    assert compile_program("score = rank(lead(close, 2))").max_negative_shift == 2
    assert compile_program("score = rank(pct_change(close, -1))").max_negative_shift == 1
    assert compile_program("score = rank(delay(close, 4))").max_negative_shift == 0


def test_pit_lags_alt_fields(market):
    fields = market.as_fields()
    prog = compile_program("score = rank(mgmt_tone_quarter)")
    as_written = execute(prog, fields, pit=False)
    pit = execute(prog, fields, pit=True, lags=market.field_lags)
    # the peeking field must differ under leak-proof execution
    assert not as_written.equals(pit)


def test_pit_price_lag_only_when_negative_shift(market):
    fields = market.as_fields()
    prog = compile_program("score = rank(pct_change(close, 63))")
    plain = execute(prog, fields, pit=False)
    pit = execute(prog, fields, pit=True, lags=market.field_lags)
    # no negative shift, no alt fields used -> identical execution
    pd.testing.assert_frame_equal(plain, pit)


def test_survivors_mask(market):
    import numpy as np
    fields = market.as_fields()
    prog = compile_program("score = rank(pct_change(close, 63))")
    mask = pd.DataFrame(np.tile(market.survivors, (len(market.dates), 1)),
                        index=market.dates, columns=market.close.columns)
    out = execute(prog, fields, pit=False, universe_mask=mask)
    assert out.loc[:, ~mask.iloc[-1].astype(bool)].isna().all().all()


def test_written_and_pit_pair(market):
    prog = compile_program("mom = pct_change(close, 126)\nscore = rank(mom)")
    w, p = as_written_and_pit(prog, market.as_fields(), market.field_lags,
                              None, market.listed)
    assert w.shape == p.shape == market.close.shape
