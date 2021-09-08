#!/usr/bin/env python

"""
Base classes for reproduction.

ReproductionBase -> NonWrightFisher -> BryophyteBase
                    WrightFisher       PteridophyteBase
                                       etc.
"""

from dataclasses import dataclass
import pyslim
from shadie.reproduction.scripts import (
    EARLY,
    SUBSTITUTION,
    SUB_MUTS,
)


@dataclass
class ReproductionBase:
    """Reproduction code block generation BaseClass.

    All Reproduction subclasses will store the Model, lineage,
    mode, and a set of scripts stored as a dictionary. Users will
    only interact with subclasses of ReproductionBase, generated by
    using the ReproductionApi accessible from the Model object.

    The NonWFBase is a superclass used for organism models. The
    WFBase superclass is used mainly for testing or comparison to
    standard WF model simulations.

    Example
    -------
    with shadie.Model() as model:
        model.initialize(...)
        model.early(...)
        model.reproduction.bryophyte(...)
    """
    model: 'shadie.Model'

    def _write_trees_file(self):
        """adds late() call to save and write .trees file.

        All shadie reproduction classes write a .trees file in a late()
        call, but the time at which to write it varies depending on
        whether the start point was loaded from a previous file.
        """
        # get time AFTER the last even generation.
        endtime = int(self.model.sim_time + 1)

        # calculate end based on this sim AND the loaded parent sim.
        if self.model.metadata['file_in']:
            ts_start = pyslim.load(self.model.metadata['file_in'])
            sim_start = ts_start.max_root_time
            resched_end = int(endtime + sim_start)
            self.model.late(
                time=resched_end,
                scripts=[
                    "sim.treeSeqRememberIndividuals(sim.subpopulations.individuals)",
                    f"sim.treeSeqOutput('{self.model.metadata['file_out']}')"],
                comment="end of sim; save .trees file",
            )
        # write output at last generation of this simulation.
        else:
            self.model.late(
                time=endtime,
                scripts=[
                    "sim.treeSeqRememberIndividuals(sim.subpopulations.individuals)",
                    f"sim.treeSeqOutput('{self.model.metadata['file_out']}')"],
                comment="end of sim; save .trees file",
            )


@dataclass
class NonWrightFisher(ReproductionBase):
    """Reproduction mode based on NON Wright-Fisher model.

    This is a subclass that is extended for organism specific
    reproduction models in shadie.reproduction. All NonWF models
    include alternation of generations (p0 and p1 subpops). The
    alternative is to implement a WF model.
    """
    def _define_subpopulations(self):
        """add haploid and diploid life stages as subpopulations."""
        if self.model.metadata['file_in']:
            self.model._read_from_file(tag_scripts =[ "p1.individuals.tag=0"])
        else:
            self.model.early(
                time=1,
                scripts=[
                    "sim.addSubpop('p1', spo_pop_size)",
                    "sim.addSubpop('p0', 0)",
                    "p1.individuals.tag = 0",],
                comment="define subpops: p1=diploid sporophytes, p0=haploid gametophytes",
            )

    def _add_initialize_constants(self):
        """Add defineConstant calls to init variables.

        When this is called by different superclasses that have
        different attributes unique to each it stores only their
        unique set of attributes. Excludes parent attrs like model.
        """
        # exclude parent class attributes
        exclude = ["lineage", "mode", "model", "_substitution_str"]
        asdict = {
            i: j for (i, j) in self.__dict__.items()
            if i not in exclude
        }
        self.model.map["initialize"][0]['constants'].update(asdict)

    def _add_alternation_of_generations(self):
        """Alternation of generations scripts.

        This writes fitness, early, and late functions that activate
        or deactivate fitness effects of mutations in alternating
        generations.
        """
        # add fitness callback for gametophytes based on MutationTypes
        # in the model.chromosome.
        # this will map to sx-sy survival callbacks.
        idx = 4
        activate_scripts = []
        deactivate_scripts = []
        substitutions = []

        # iterate over MutationTypes
        for mut in self.model.chromosome.mutations:

            # refer to mutations by s{idx}
            idx += 1
            sidx = str("s" + str(idx))

            # add fitness callback function (e.g., s5 fitness(m1) {...})
            # for each MutationType. This callback will be activated or
            # deactivated (below) by early scripts based on whether
            # it is the haploid or diploid subpopulation's generation.
            self.model.fitness(
                idx=sidx,
                mutation=mut.name,
                scripts="return 1 + mut.selectionCoeff",
                comment="gametophytes have no dominance effects",
            )

            # store script to activate or deactivate this mutationtype
            activate_scripts.append(f"{sidx}.active = 1;")
            deactivate_scripts.append(f"{sidx}.active = 0;")

            # add reference to this mutation to be added to a late call
            # for checking whether a mutation has become a substitution.
            sub_muts = SUB_MUTS.format(idx=sidx, mut=mut.name).lstrip()
            substitutions.append(sub_muts)

        # insert references to fitness callbacks into an early script
        # that will alternately activate or deactivate them on
        # alternating generations to only apply to gameto or sporo.
        activate_str = "\n        ".join(activate_scripts)
        deactivate_str = "\n        ".join(deactivate_scripts)
        early_script = (
            EARLY.format(activate=activate_str, deactivate=deactivate_str)
        )
        self.model.early(
            time=None,
            scripts=early_script,
            comment="alternation of generations",
        )

        # insert the substitution-checking scripts into larger context
        substitution_str = "\n    ".join(substitutions)
        #save subsitutions for late call in model-specific scripts
        self._substitution_str = substitution_str

@dataclass
class WrightFisher(ReproductionBase):
    """Reproduction mode based on Wright-Fisher model."""
    pop_size: int
    sexes: bool = False  # not yet used?

    def run(self):
        """
        Updates self.model.map with new component scripts for running
        life history and reproduction based on input args.
        """
        self._define_subpopulations()
        self._add_initialize_constants()
        self._add_scripts()
        self._write_trees_file()

    def _define_subpopulations(self):
        """Add a single diploid population. See NonWrightFisher for comparison."""
        if self.model.metadata['file_in']:
            self.model.read_from_file()
        else:
            self.model.early(
                time=1,
                scripts="sim.addSubpop('p1', K);",
                comment="define starting diploid population.",
            )

    def _add_scripts(self):
        """fitness and mating of diploid population."""
        self.model.early(
            time=None,
            scripts="p1.fitnessScaling = K / p1.individualCount;",
            comment="calculate relative fitness.",
        )
        self.model.repro(
            population="p1",
            scripts="subpop.addCrossed(individual,subpop.sampleIndividuals(1));",
            comment="hermaphroditic random mating."
        )

    def _add_initialize_constants(self):
        """Add defineConstant calls to init for new variables."""
        self.model.map["initialize"][0]['constants']["K"] = self.pop_size



if __name__ == "__main__":

    import shadie

    # define mutation types
    m0 = shadie.mtype(0.5, 'n', 0, 0.4)
    m1 = shadie.mtype(0.5, 'g', 0.8, 0.75)

    # define elements types
    e0 = shadie.etype([m0, m1], [1, 2])
    e1 = shadie.etype([m1], [1])

    # design chromosome of elements
    chrom = shadie.chromosome.random(
        genome_size=20000,
        noncds=e0,
        intron=e0,
        exon=e1,
    )

    with shadie.Model() as mod:
        mod.initialize(chromosome=chrom, sim_time=1000)
        mod.reproduction.wright_fisher(pop_size=1000)

    mod.write("/tmp/slim.slim")
    mod.run(binary="/usr/local/bin/slim")
