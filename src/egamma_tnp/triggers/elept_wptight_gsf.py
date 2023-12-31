import dask_awkward as dak
from coffea.lumi_tools import LumiMask

from egamma_tnp.triggers.basesingleelectrontrigger import BaseSingleElectronTrigger


class _TnPImpl:
    def __call__(
        self,
        events,
        pt,
        avoid_ecal_transition_tags,
        avoid_ecal_transition_probes,
        goldenjson,
        extra_filter,
        extra_filter_args,
    ):
        if extra_filter is not None:
            events = extra_filter(events, **extra_filter_args)
        if goldenjson is not None:
            events = self.apply_lumimasking(events, goldenjson)
        good_events, good_locations = self.filter_events(events)
        ele_for_tnp = good_events.Electron[good_locations]
        zcands1 = dak.combinations(ele_for_tnp, 2, fields=["tag", "probe"])
        zcands2 = dak.combinations(ele_for_tnp, 2, fields=["probe", "tag"])

        if avoid_ecal_transition_tags:
            tags1 = zcands1.tag
            pass_eta_ebeegap_tags1 = (abs(tags1.eta) < 1.4442) | (
                abs(tags1.eta) > 1.566
            )
            zcands1 = zcands1[pass_eta_ebeegap_tags1]
            tags2 = zcands2.tag
            pass_eta_ebeegap_tags2 = (abs(tags2.eta) < 1.4442) | (
                abs(tags2.eta) > 1.566
            )
            zcands2 = zcands2[pass_eta_ebeegap_tags2]
        if avoid_ecal_transition_probes:
            probes1 = zcands1.probe
            pass_eta_ebeegap_probes1 = (abs(probes1.eta) < 1.4442) | (
                abs(probes1.eta) > 1.566
            )
            zcands1 = zcands1[pass_eta_ebeegap_probes1]
            probes2 = zcands2.probe
            pass_eta_ebeegap_probes2 = (abs(probes2.eta) < 1.4442) | (
                abs(probes2.eta) > 1.566
            )
            zcands2 = zcands2[pass_eta_ebeegap_probes2]

        p1, a1 = self.find_probes(zcands1, good_events.TrigObj, pt)
        p2, a2 = self.find_probes(zcands2, good_events.TrigObj, pt)

        return p1, a1, p2, a2

    def apply_lumimasking(self, events, goldenjson):
        lumimask = LumiMask(goldenjson)
        mask = lumimask(events.run, events.luminosityBlock)
        return events[mask]

    def filter_events(self, events):
        two_electrons = dak.num(events.Electron) == 2
        abs_eta = abs(events.Electron.eta)
        pass_tight_id = events.Electron.cutBased == 4
        pass_eta = abs_eta <= 2.5
        pass_selection = two_electrons & pass_eta & pass_tight_id
        n_of_tags = dak.sum(pass_selection, axis=1)
        good_events = events[n_of_tags == 2]
        good_locations = pass_selection[n_of_tags == 2]
        return good_events, good_locations

    def trigger_match_tag(self, electrons, trigobjs, pt):
        pass_pt = trigobjs.pt > pt
        pass_id = abs(trigobjs.id) == 11
        filterbit = 1
        pass_filterbit = trigobjs.filterBits & (0x1 << filterbit) > 0
        trigger_cands = trigobjs[pass_pt & pass_id & pass_filterbit]
        delta_r = electrons.metric_table(trigger_cands)
        pass_delta_r = delta_r < 0.1
        n_of_trigger_matches = dak.sum(pass_delta_r, axis=2)
        trig_matched_locs = n_of_trigger_matches >= 1
        return trig_matched_locs

    def trigger_match_probe(self, electrons, trigobjs, pt):
        pass_pt = trigobjs.pt > pt
        pass_id = abs(trigobjs.id) == 11
        filterbit = 1
        pass_filterbit = trigobjs.filterBits & (0x1 << filterbit) > 0
        trigger_cands = trigobjs[pass_pt & pass_id & pass_filterbit]
        delta_r = electrons.metric_table(trigger_cands)
        pass_delta_r = delta_r < 0.1
        n_of_trigger_matches = dak.sum(pass_delta_r, axis=2)
        trig_matched_locs = n_of_trigger_matches >= 1
        return trig_matched_locs

    def find_probes(self, zcands, trigobjs, pt):
        pt_cond_tags = zcands.tag.pt > 30
        pt_cond_probes = zcands.probe.pt > pt
        trig_matched_tag = self.trigger_match_tag(zcands.tag, trigobjs, 30)
        zcands = zcands[trig_matched_tag & pt_cond_tags & pt_cond_probes]
        events_with_tags = dak.num(zcands.tag, axis=1) >= 1
        zcands = zcands[events_with_tags]
        trigobjs = trigobjs[events_with_tags]
        tags = zcands.tag
        probes = zcands.probe
        dr = tags.delta_r(probes)
        mass = (tags + probes).mass
        in_mass_window = abs(mass - 91.1876) < 30
        opposite_charge = tags.charge * probes.charge == -1
        isZ = in_mass_window & opposite_charge
        dr_condition = dr > 0.0
        all_probes = probes[isZ & dr_condition]
        trig_matched_probe = self.trigger_match_probe(all_probes, trigobjs, pt)
        passing_probes = all_probes[trig_matched_probe]
        return passing_probes, all_probes


class ElePt_WPTight_Gsf(BaseSingleElectronTrigger):
    def __init__(
        self,
        names,
        trigger_pt,
        *,
        avoid_ecal_transition_tags=True,
        avoid_ecal_transition_probes=False,
        goldenjson=None,
        toquery=False,
        redirector=None,
        preprocess=False,
        preprocess_args=None,
        extra_filter=None,
        extra_filter_args=None,
    ):
        """Tag and Probe efficiency for HLT_ElePt_WPTight_Gsf trigger from NanoAOD.

        Parameters
        ----------
            names : str or list of str
                The dataset names to query that can contain wildcards or a list of file paths.
            trigger_pt : int or float
                The Pt threshold of the trigger.
            avoid_ecal_transition_tags : bool, optional
                Whether to avoid the ECAL transition region for the tags with an eta cut. The default is True.
            avoid_ecal_transition_probes : bool, optional
                Whether to avoid the ECAL transition region for the probes with an eta cut. The default is False.
            goldenjson : str, optional
                The golden json to use for luminosity masking. The default is None.
            toquery : bool, optional
                Whether to query DAS for the dataset names. The default is False.
            redirect : bool, optional
                Whether to add an xrootd redirector to the files. The default is False.
            redirector : str, optional
                A custom xrootd redirector to add to the files. The default is None.
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
        if preprocess_args is None:
            preprocess_args = {}
        if extra_filter_args is None:
            extra_filter_args = {}

        super().__init__(
            names=names,
            perform_tnp=_TnPImpl(),
            pt=trigger_pt - 1,
            avoid_ecal_transition_tags=avoid_ecal_transition_tags,
            avoid_ecal_transition_probes=avoid_ecal_transition_probes,
            goldenjson=goldenjson,
            toquery=toquery,
            redirector=redirector,
            preprocess=preprocess,
            preprocess_args=preprocess_args,
            extra_filter=extra_filter,
            extra_filter_args=extra_filter_args,
        )

    def __repr__(self):
        if self.events is None:
            return f"HLT_Ele{self.pt + 1}_WPTight_Gsf(Events: not loaded, Number of files: {len(self.file)}, Golden JSON: {self.goldenjson})"
        else:
            return f"HLT_Ele{self.pt + 1}_WPTight_Gsf(Events: {self.events}, Number of files: {len(self.file)}, Golden JSON: {self.goldenjson})"
