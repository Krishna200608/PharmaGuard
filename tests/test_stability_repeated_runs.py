from pharmaguard.tools.pubmed_tool import PubMedTool
"""
Unit tests for Repeated-Run Stability Analysis (Experiment 1).
Tests summary statistics, Wilson CI, Spearman rank correlation, and mocked repeated-run pipeline execution.
"""

import json
import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.research.stability_repeated_runs import (
    calc_summary_stats,
    calc_mode_and_agreement,
    calc_wilson_interval,
    rankdata,
    calc_spearman_rank_correlation,
    run_repeated_stability_experiment,
)


def test_calc_summary_stats_zero_variance():
    vals = [1.0, 1.0, 1.0, 1.0, 1.0]
    res = calc_summary_stats(vals)
    assert res["n"] == 5
    assert res["mean"] == 1.0
    assert res["std"] == 0.0
    assert res["min"] == 1.0
    assert res["max"] == 1.0
    assert res["cv"] == 0.0


def test_calc_summary_stats_hand_calculated():
    # vals: [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    # N=8, sum=40, mean=5.0
    # squared diffs: (2-5)^2=9, (4-5)^2=1 * 3 = 3, (5-5)^2=0, (7-5)^2=4, (9-5)^2=16 -> sum = 32
    # sample variance = 32 / 7 = 4.57142857
    # sample std = sqrt(32/7) = 2.138089935
    # cv = 2.138089935 / 5.0 = 0.427617987
    vals = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    res = calc_summary_stats(vals)
    assert res["n"] == 8
    assert res["mean"] == 5.0
    assert math.isclose(res["std"], 2.1381, abs_tol=1e-4)
    assert res["min"] == 2.0
    assert res["max"] == 9.0
    assert math.isclose(res["cv"], 0.427618, abs_tol=1e-4)


def test_calc_wilson_interval():
    # 10 successes out of 10
    lower_10, upper_10 = calc_wilson_interval(10, 10)
    assert math.isclose(upper_10, 1.0, abs_tol=1e-3)
    assert 0.70 <= lower_10 <= 0.75

    # 8 successes out of 10
    lower_8, upper_8 = calc_wilson_interval(8, 10)
    assert 0.48 <= lower_8 <= 0.55
    assert 0.90 <= upper_8 <= 0.96


def test_calc_mode_and_agreement():
    stable_cats = ["ESCALATE"] * 10
    res_stable = calc_mode_and_agreement(stable_cats)
    assert res_stable["mode"] == "ESCALATE"
    assert res_stable["mode_count"] == 10
    assert res_stable["percent_agreement"] == 100.0
    assert res_stable["is_100_percent_stable"] is True

    unstable_cats = ["ESCALATE"] * 7 + ["MONITOR"] * 3
    res_unstable = calc_mode_and_agreement(unstable_cats)
    assert res_unstable["mode"] == "ESCALATE"
    assert res_unstable["mode_count"] == 7
    assert res_unstable["percent_agreement"] == 70.0
    assert res_unstable["is_100_percent_stable"] is False


def test_rankdata_with_ties():
    arr = [10.0, 20.0, 20.0, 30.0]
    ranks = rankdata(arr)
    assert ranks == [1.0, 2.5, 2.5, 4.0]


def test_calc_spearman_rank_correlation():
    # Perfect positive correlation
    v1 = [10.0, 20.0, 30.0, 40.0]
    v2 = [100.0, 200.0, 300.0, 400.0]
    assert math.isclose(calc_spearman_rank_correlation(v1, v2), 1.0, abs_tol=1e-5)

    # Perfect negative correlation
    v3 = [400.0, 300.0, 200.0, 100.0]
    assert math.isclose(calc_spearman_rank_correlation(v1, v3), -1.0, abs_tol=1e-5)


def test_repeated_stability_experiment_mocked(tmp_path):
    scratch_dir = tmp_path / "scratch_cache"
    out_file = tmp_path / "repeated_run_variance.json"
    dummy_gt = tmp_path / "dummy_ground_truth.json"

    dummy_gt_data = {
        "pairs": [
            {"drug_canonical": "testdrug1", "event_meddra_pt": "testevent1"},
            {"drug_canonical": "testdrug2", "event_meddra_pt": "testevent2"},
        ]
    }
    dummy_gt.write_text(json.dumps(dummy_gt_data), encoding="utf-8")

    # Mock ChatGoogleGenerativeAI
    with patch("scripts.research.stability_repeated_runs.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm_instance = MagicMock()
        mock_llm_cls.return_value = mock_llm_instance
        
        # Mock structured LLM
        mock_structured = MagicMock()
        # Alternate grades: A then B
        mock_structured.invoke.side_effect = [
            MagicMock(grade="A", explanation="Good evidence"),
            MagicMock(grade="B", explanation="Moderate evidence"),
            MagicMock(grade="A", explanation="Good evidence"),
            MagicMock(grade="A", explanation="Good evidence"),
        ]
        mock_llm_instance.with_structured_output.return_value = mock_structured

        # Mock PubMedTool search/fetch
        with patch.object(PubMedTool, "_esearch", return_value=["123", "456"]), \
             patch.object(PubMedTool, "_efetch_abstracts", return_value=["abstract 1", "abstract 2"]):

            res = run_repeated_stability_experiment(
                repeats=2,
                pairs_limit=2,
                inter_call_delay=0.0,
                scratch_dir=scratch_dir,
                output_file=out_file,
                gt_file=dummy_gt,
            )

            assert out_file.exists()
            assert res["cross_pair_summary"]["total_pairs_evaluated"] == 2
            assert "testdrug1::testevent1" in res["per_pair_summary_statistics"]
            assert "testdrug2::testevent2" in res["per_pair_summary_statistics"]
            assert res["cross_run_rank_stability"]["num_run_pairs_compared"] == 1