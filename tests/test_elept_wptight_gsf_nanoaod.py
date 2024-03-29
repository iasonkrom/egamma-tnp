import os

import pytest
from coffea.dataset_tools import preprocess

from egamma_tnp.triggers import ElePt_WPTight_Gsf


@pytest.mark.parametrize("do_preprocess", [True, False])
@pytest.mark.parametrize("allow_read_errors_with_report", [True, False])
def test_without_compute(do_preprocess, allow_read_errors_with_report):
    if allow_read_errors_with_report:
        fileset = {
            "sample": {
                "files": {
                    os.path.abspath("tests/samples/DYto2E.root"): "Events",
                    os.path.abspath("tests/samples/not_a_file.root"): "Events",
                }
            }
        }
    else:
        fileset = {
            "sample": {
                "files": {os.path.abspath("tests/samples/DYto2E.root"): "Events"}
            }
        }

    if do_preprocess:
        if allow_read_errors_with_report:
            with pytest.raises(FileNotFoundError):
                preprocess(fileset)
            fileset_available, fileset_updated = preprocess(
                fileset, skip_bad_files=True
            )
            fileset = fileset_available

    tag_n_probe = ElePt_WPTight_Gsf(
        fileset,
        32,
        avoid_ecal_transition_tags=True,
        avoid_ecal_transition_probes=True,
        goldenjson=None,
    )

    res = tag_n_probe.get_tnp_histograms(
        uproot_options={"allow_read_errors_with_report": allow_read_errors_with_report},
        compute=False,
        scheduler=None,
        progress=False,
    )

    if allow_read_errors_with_report:
        histograms = res[0]["sample"]
    else:
        histograms = res["sample"]

    hpt_pass_barrel, hpt_all_barrel = histograms["pt"]["barrel"].values()
    hpt_pass_endcap, hpt_all_endcap = histograms["pt"]["endcap"].values()
    heta_pass, heta_all = histograms["eta"]["entire"].values()
    hphi_pass, hphi_all = histograms["phi"]["entire"].values()

    assert hpt_pass_barrel.sum(flow=True) + hpt_pass_endcap.sum(flow=True) == 0.0
    assert hpt_all_barrel.sum(flow=True) + hpt_all_endcap.sum(flow=True) == 0.0
    assert heta_pass.sum(flow=True) == 0.0
    assert heta_all.sum(flow=True) == 0.0
    assert hphi_pass.sum(flow=True) == 0.0
    assert hphi_all.sum(flow=True) == 0.0

    assert (
        hpt_pass_barrel.values(flow=True)[0] + hpt_pass_endcap.values(flow=True)[0]
        == 0.0
    )
    assert (
        hpt_all_barrel.values(flow=True)[0] + hpt_all_endcap.values(flow=True)[0] == 0.0
    )
    assert heta_pass.values(flow=True)[0] == 0.0
    assert heta_all.values(flow=True)[0] == 0.0
    assert hphi_pass.values(flow=True)[0] == 0.0
    assert hphi_all.values(flow=True)[0] == 0.0


@pytest.mark.parametrize("do_preprocess", [True, False])
@pytest.mark.parametrize("allow_read_errors_with_report", [True, False])
def test_local_compute(do_preprocess, allow_read_errors_with_report):
    if allow_read_errors_with_report:
        fileset = {
            "sample": {
                "files": {
                    os.path.abspath("tests/samples/DYto2E.root"): "Events",
                    os.path.abspath("tests/samples/not_a_file.root"): "Events",
                }
            }
        }
    else:
        fileset = {
            "sample": {
                "files": {os.path.abspath("tests/samples/DYto2E.root"): "Events"}
            }
        }

    if do_preprocess:
        if allow_read_errors_with_report:
            with pytest.raises(FileNotFoundError):
                preprocess(fileset)
            fileset_available, fileset_updated = preprocess(
                fileset, skip_bad_files=True
            )
            fileset = fileset_available

    tag_n_probe = ElePt_WPTight_Gsf(
        fileset,
        32,
        avoid_ecal_transition_tags=True,
        avoid_ecal_transition_probes=True,
        goldenjson=None,
    )

    res = tag_n_probe.get_tnp_histograms(
        uproot_options={"allow_read_errors_with_report": allow_read_errors_with_report},
        compute=True,
        scheduler=None,
        progress=True,
    )

    if allow_read_errors_with_report:
        histograms = res[0]["sample"]
        report = res[1]["sample"]
        if not do_preprocess:
            assert report.exception[1] == "FileNotFoundError"
    else:
        histograms = res["sample"]

    hpt_pass_barrel, hpt_all_barrel = histograms["pt"]["barrel"].values()
    hpt_pass_endcap, hpt_all_endcap = histograms["pt"]["endcap"].values()
    heta_pass, heta_all = histograms["eta"]["entire"].values()
    hphi_pass, hphi_all = histograms["phi"]["entire"].values()

    assert hpt_pass_barrel.sum(flow=True) + hpt_pass_endcap.sum(flow=True) == 954.0
    assert hpt_all_barrel.sum(flow=True) + hpt_all_endcap.sum(flow=True) == 1153.0
    assert heta_pass.sum(flow=True) == 954.0
    assert heta_all.sum(flow=True) == 1153.0
    assert hphi_pass.sum(flow=True) == 954.0
    assert hphi_all.sum(flow=True) == 1153.0

    assert (
        hpt_pass_barrel.values(flow=True)[0] + hpt_pass_endcap.values(flow=True)[0]
        == 0.0
    )
    assert (
        hpt_all_barrel.values(flow=True)[0] + hpt_all_endcap.values(flow=True)[0] == 0.0
    )
    assert heta_pass.values(flow=True)[0] == 0.0
    assert heta_all.values(flow=True)[0] == 0.0
    assert hphi_pass.values(flow=True)[0] == 0.0
    assert hphi_all.values(flow=True)[0] == 0.0


@pytest.mark.parametrize("do_preprocess", [True, False])
@pytest.mark.parametrize("allow_read_errors_with_report", [True, False])
def test_distributed_compute(do_preprocess, allow_read_errors_with_report):
    from distributed import Client

    if allow_read_errors_with_report:
        fileset = {
            "sample": {
                "files": {
                    os.path.abspath("tests/samples/DYto2E.root"): "Events",
                    os.path.abspath("tests/samples/not_a_file.root"): "Events",
                }
            }
        }
    else:
        fileset = {
            "sample": {
                "files": {os.path.abspath("tests/samples/DYto2E.root"): "Events"}
            }
        }

    if do_preprocess:
        if allow_read_errors_with_report:
            with pytest.raises(FileNotFoundError):
                preprocess(fileset)
            fileset_available, fileset_updated = preprocess(
                fileset, skip_bad_files=True
            )
            fileset = fileset_available

    tag_n_probe = ElePt_WPTight_Gsf(
        fileset,
        32,
        avoid_ecal_transition_tags=True,
        avoid_ecal_transition_probes=True,
        goldenjson=None,
    )

    with Client():
        res = tag_n_probe.get_tnp_histograms(
            uproot_options={
                "allow_read_errors_with_report": allow_read_errors_with_report
            },
            compute=True,
            scheduler=None,
            progress=True,
        )

        if allow_read_errors_with_report:
            histograms = res[0]["sample"]
            report = res[1]["sample"]
            if not do_preprocess:
                assert report.exception[1] == "FileNotFoundError"
        else:
            histograms = res["sample"]

        hpt_pass_barrel, hpt_all_barrel = histograms["pt"]["barrel"].values()
        hpt_pass_endcap, hpt_all_endcap = histograms["pt"]["endcap"].values()
        heta_pass, heta_all = histograms["eta"]["entire"].values()
        hphi_pass, hphi_all = histograms["phi"]["entire"].values()

        assert hpt_pass_barrel.sum(flow=True) + hpt_pass_endcap.sum(flow=True) == 954.0
        assert hpt_all_barrel.sum(flow=True) + hpt_all_endcap.sum(flow=True) == 1153.0
        assert heta_pass.sum(flow=True) == 954.0
        assert heta_all.sum(flow=True) == 1153.0
        assert hphi_pass.sum(flow=True) == 954.0
        assert hphi_all.sum(flow=True) == 1153.0

        assert (
            hpt_pass_barrel.values(flow=True)[0] + hpt_pass_endcap.values(flow=True)[0]
            == 0.0
        )
        assert (
            hpt_all_barrel.values(flow=True)[0] + hpt_all_endcap.values(flow=True)[0]
            == 0.0
        )
        assert heta_pass.values(flow=True)[0] == 0.0
        assert heta_all.values(flow=True)[0] == 0.0
        assert hphi_pass.values(flow=True)[0] == 0.0
        assert hphi_all.values(flow=True)[0] == 0.0
