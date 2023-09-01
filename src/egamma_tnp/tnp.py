import os

from ._tnpmodules import (
    get_and_compute_pt_and_eta_arrays,
    get_and_compute_tnp_histograms,
    get_pt_and_eta_arrays,
    get_tnp_histograms,
)
from .utils import get_nanoevents_file


class TagNProbe:
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
    ):
        """Tag and Probe for HLT Trigger efficiency from NanoAOD.

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
        """
        self.names = names
        self.pt = trigger_pt - 1
        self.goldenjson = goldenjson
        self.toquery = toquery
        self.redirect = redirect
        self.custom_redirector = custom_redirector
        self.invalid = invalid
        self.events = None
        self.preprocess = preprocess
        self.preprocess_args = preprocess_args
        self.file = get_nanoevents_file(
            self.names,
            toquery=self.toquery,
            redirect=self.redirect,
            custom_redirector=self.custom_redirector,
            invalid=self.invalid,
            preprocess=self.preprocess,
            preprocess_args=self.preprocess_args,
        )
        if goldenjson is not None and not os.path.isfile(goldenjson):
            raise ValueError(f"Golden JSON {goldenjson} does not exist.")

    def __repr__(self):
        if self.events is None:
            return f"TagNProbe(Events: not loaded, Number of files: {len(self.file)}, Golden JSON: {self.goldenjson})"
        else:
            return f"TagNProbe(Events: {self.events}, Number of files: {len(self.file)}, Golden JSON: {self.goldenjson})"

    def remove_bad_xrootd_files(self, keys):
        """Remove bad xrootd files from self.file.

        Parameters
        ----------
            keys : str or list of str
                The keys of self.file to remove.
        """
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            try:
                self.file.pop(key)
            except KeyError:
                pass

    def redirect_files(self, keys, redirectors="root://cmsxrootd.fnal.gov/"):
        """Redirect the files in self.file.

        Parameters
        ----------
            keys : str or list of str
                The keys of self.file to redirect.
            redirectors : str or list of str, optional
                The redirectors to use. The default is "root://cmsxrootd.fnal.gov/".
                If multiple keys are given, then either one redirector or the same number of redirectors as keys must be given.
        """
        from .utils import redirect_files

        if isinstance(keys, str):
            keys = [keys]
        if isinstance(redirectors, str) or (
            isinstance(redirectors, list) and len(redirectors) == 1
        ):
            redirectors = (
                [redirectors] * len(keys)
                if isinstance(redirectors, str)
                else redirectors * len(keys)
            )
        if (len(keys) > 1 and (len(redirectors) != 1)) and (
            len(keys) != len(redirectors)
        ):
            raise ValueError(
                f"If multiple keys are given, then either one redirector or the same number of redirectors as keys must be given."
                f"Got {len(keys)} keys and {len(redirectors)} redirectors."
            )
        for key, redirector in zip(keys, redirectors):
            isrucio = True if key[:7] == "root://" else False
            newkey = redirect_files(key, redirector=redirector, isrucio=isrucio).pop()
            self.file[newkey] = self.file.pop(key)

    def load_events(self, from_root_args={}):
        """Load the events from the names.

        Parameters
        ----------
            from_root_args : dict, optional
                Extra arguments to pass to coffea.nanoevents.NanoEventsFactory.from_root().
                The default is {}.
        """
        from coffea.nanoevents import NanoEventsFactory

        self.events = NanoEventsFactory.from_root(
            self.file,
            permit_dask=True,
            **from_root_args,
        ).events()

    def get_pt_and_eta_arrays(self, compute=False, scheduler=None, progress=True):
        """Get the Pt and Eta arrays of the passing and all probes.
        WARNING: Not recommended to be used for large datasets as the arrays can be very large.

        Parameters
        ----------
            compute : bool, optional
                Whether to return the computed arrays or the delayed arrays.
                The default is False.
            scheduler : str, optional
                The dask scheduler to use. The default is None.
                Only used if compute is True.
            progress : bool, optional
                Whether to show a progress bar if `compute` is True. The default is True.
                Only used if compute is True and no distributed Client is used.

        Returns
        -------
            pt_pass1: numpy.ndarray or dask_awkward.Array
                The Pt array of the passing probes when the firsts electrons are the tags.
            pt_pass2: numpy.ndarray or dask_awkward.Array
                The Pt array of the passing probes when the seconds electrons are the tags.
            pt_all1: numpy.ndarray or dask_awkward.Array
                The Pt array of all probes when the firsts electrons are the tags.
            pt_all2: numpy.ndarray or dask_awkward.Array
                The Pt array of all probes when the seconds electrons are the tags.
            eta_pass1: numpy.ndarray or dask_awkward.Array
                The Eta array of the passing probes when the firsts electrons are the tags.
            eta_pass2: numpy.ndarray or dask_awkward.Array
                The Eta array of the passing probes when the seconds electrons are the tags.
            eta_all1: numpy.ndarray or dask_awkward.Array
                The Eta array of all probes when the firsts electrons are the tags.
            eta_all2: numpy.ndarray or dask_awkward.Array
                The Eta array of all probes when the seconds electrons are the tags.
        """
        if compute:
            return get_and_compute_pt_and_eta_arrays(
                events=self.events,
                pt=self.pt,
                goldenjson=self.goldenjson,
                scheduler=scheduler,
                progress=progress,
            )
        else:
            return get_pt_and_eta_arrays(
                events=self.events, pt=self.pt, goldenjson=self.goldenjson
            )

    def get_tnp_histograms(self, compute=False, scheduler=None, progress=True):
        """Get the Pt and Eta histograms of the passing and all probes.

        Parameters
        ----------
            compute : bool, optional
                Whether to return the computed hist.Hist histograms or the delayed hist.dask.Hist histograms.
                The default is False.
            scheduler : str, optional
                The dask scheduler to use. The default is None.
                Only used if compute is True.
            progress : bool, optional
                Whether to show a progress bar if `compute` is True. The default is True.
                Only used if compute is True and no distributed Client is used.

        Returns
        -------
            hpt_pass: hist.Hist or hist.dask.Hist
                The Pt histogram of the passing probes.
            hpt_all: hist.Hist or hist.dask.Hist
                The Pt histogram of all probes.
            heta_pass: hist.Hist or hist.dask.Hist
                The Eta histogram of the passing probes.
            heta_all: hist.Hist or hist.dask.Hist
                The Eta histogram of all probes.
        """
        if compute:
            return get_and_compute_tnp_histograms(
                events=self.events,
                pt=self.pt,
                goldenjson=self.goldenjson,
                scheduler=scheduler,
                progress=progress,
            )
        else:
            return get_tnp_histograms(
                events=self.events, pt=self.pt, goldenjson=self.goldenjson
            )
