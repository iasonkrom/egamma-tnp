import dask_awkward as dak
from coffea.lumi_tools import LumiMask

from egamma_tnp.triggers.basetrigger import BaseTrigger


class _TnPImpl:
    def __call__(
        self, events, pt, goldenjson=None, extra_filter=None, extra_filter_args={}
    ):
        if extra_filter is not None:
            events = extra_filter(events, **extra_filter_args)
        if goldenjson is not None:
            events = self.apply_lumimasking(events, goldenjson)
        good_events, good_locations = self.filter_events(events, pt)
        ele_for_tnp = good_events.Electron[good_locations]
        zcands1 = dak.combinations(ele_for_tnp, 2, fields=["tag", "probe"])
        zcands2 = dak.combinations(ele_for_tnp, 2, fields=["probe", "tag"])
        p1, a1 = self.find_probes(zcands1.tag, zcands1.probe, good_events.TrigObj, pt)
        p2, a2 = self.find_probes(zcands2.tag, zcands2.probe, good_events.TrigObj, pt)
        return p1, a1, p2, a2

    def apply_lumimasking(self, events, goldenjson):
        lumimask = LumiMask(goldenjson)
        mask = lumimask(events.run, events.luminosityBlock)
        return events[mask]

    def filter_events(self, events, pt):
        events = events[dak.num(events.Electron) >= 2]
        abs_eta = abs(events.Electron.eta)
        pass_eta_ebeegap = (abs_eta < 1.4442) | (abs_eta > 1.566)
        pass_tight_id = events.Electron.cutBased == 4
        pass_pt = events.Electron.pt > pt
        pass_eta = abs_eta <= 2.5
        pass_selection = pass_pt & pass_eta & pass_eta_ebeegap & pass_tight_id
        n_of_tags = dak.sum(pass_selection, axis=1)
        good_events = events[n_of_tags >= 2]
        good_locations = pass_selection[n_of_tags >= 2]
        return good_events, good_locations

    def trigger_match(self, electrons, trigobjs, pt):
        pass_pt = trigobjs.pt > pt
        pass_id = abs(trigobjs.id) == 11
        filterbit = 11
        pass_filterbit = trigobjs.filterBits & (0x1 << filterbit) == 2**filterbit
        trigger_cands = trigobjs[pass_pt & pass_id & pass_filterbit]
        delta_r = electrons.metric_table(trigger_cands)
        pass_delta_r = delta_r < 0.1
        n_of_trigger_matches = dak.sum(dak.sum(pass_delta_r, axis=1), axis=1)
        trig_matched_locs = n_of_trigger_matches >= 1
        return trig_matched_locs

    def find_probes(self, tags, probes, trigobjs, pt):
        trig_matched_tag = self.trigger_match(tags, trigobjs, pt)
        tags = tags[trig_matched_tag]
        probes = probes[trig_matched_tag]
        trigobjs = trigobjs[trig_matched_tag]
        dr = tags.delta_r(probes)
        mass = (tags + probes).mass
        in_mass_window = abs(mass - 91.1876) < 30
        opposite_charge = tags.charge * probes.charge == -1
        isZ = in_mass_window & opposite_charge
        dr_condition = dr > 0.0
        all_probes = probes[isZ & dr_condition]
        trig_matched_probe = self.trigger_match(all_probes, trigobjs, pt)
        passing_probes = all_probes[trig_matched_probe]
        return passing_probes, all_probes


_bins = {
    "ptbins": [
        5,
        10,
        15,
        20,
        22,
        26,
        28,
        30,
        32,
        34,
        36,
        38,
        40,
        45,
        50,
        60,
        80,
        100,
        110,
        120,
        130,
        140,
        150,
        250,
        400,
    ],
    "etabins": [
        -2.5,
        -2.4,
        -2.3,
        -2.2,
        -2.1,
        -2.0,
        -1.9,
        -1.8,
        -1.7,
        -1.566,
        -1.4442,
        -1.3,
        -1.2,
        -1.1,
        -1.0,
        -0.9,
        -0.8,
        -0.7,
        -0.6,
        -0.5,
        -0.4,
        -0.3,
        -0.2,
        -0.1,
        0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1,
        1.1,
        1.2,
        1.3,
        1.4442,
        1.566,
        1.7,
        1.8,
        1.9,
        2.0,
        2.1,
        2.2,
        2.3,
        2.4,
        2.5,
    ],
    "phibins": [
        -3.32,
        -2.97,
        -2.62,
        -2.27,
        -1.92,
        -1.57,
        -1.22,
        -0.87,
        -0.52,
        -0.18,
        0.18,
        0.52,
        0.87,
        1.22,
        1.57,
        1.92,
        2.27,
        2.62,
        2.97,
        3.32,
    ],
}


class ElePt_CaloIdVT_GsfTrkIdT(BaseTrigger):
    def __init__(
        self,
        names,
        trigger_pt,
        *,
        goldenjson=None,
        toquery=False,
        redirect=False,
        custom_redirector="root://cmsxrootd.fnal.gov/",
        invalid=False,
        preprocess=False,
        preprocess_args={},
        extra_filter=None,
        extra_filter_args={},
    ):
        """Tag and Probe efficiency for HLT_ElePt_CaloIdVT_GsfTrkIdT trigger from NanoAOD.

        Parameters
        ----------
            names : str or list of str
                The dataset names to query that can contain wildcards or a list of file paths.
            trigger_pt : int or float
                The Pt threshold of the trigger.
            goldenjson : str, optional
                The golden json to use for luminosity masking. The default is None.
            toquery : bool, optional
                Whether to query DAS for the dataset names. The default is False.
            redirect : bool, optional
                Whether to add an xrootd redirector to the files. The default is False.
            custom_redirector : str, optional
                The xrootd redirector to add to the files. The default is "root://cmsxrootd.fnal.gov/".
                Only used if redirect is True.
            invalid : bool, optional
                Whether to include invalid files. The default is False.
                Only used if toquery is True.
            preprocess : bool, optional
                Whether to preprocess the files using coffea.dataset_tools.preprocess().
                The default is False.
            preprocess_args : dict, optional
                Extra arguments to pass to coffea.dataset_tools.preprocess(). The default is {}.
            extra_filter : Callable, optional
                An extra function to filter the events. The default is None.
                Must take in a coffea NanoEventsArray and return a filtered NanoEventsArray of the events you want to keep.
            extra_filter_args : dict, optional
                Extra arguments to pass to extra_filter. The default is {}.
        """
        self.pt = trigger_pt - 10
        super().__init__(
            names=names,
            perform_tnp=_TnPImpl(),
            goldenjson=goldenjson,
            toquery=toquery,
            redirect=redirect,
            custom_redirector=custom_redirector,
            invalid=invalid,
            preprocess=preprocess,
            preprocess_args=preprocess_args,
            extra_filter=extra_filter,
            extra_filter_args=extra_filter_args,
            bins=_bins,
        )

    def __repr__(self):
        if self.events is None:
            return f"HLT_Ele{self.pt + 1}_CaloIdVT_GsfTrkIdT(Events: not loaded, Number of files: {len(self.file)}, Golden JSON: {self.goldenjson})"
        else:
            return f"HLT_Ele{self.pt + 1}_CaloIdVT_GsfTrkIdT(Events: {self.events}, Number of files: {len(self.file)}, Golden JSON: {self.goldenjson})"