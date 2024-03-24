#!/usr/bin/env python

"""Base classes for reproduction.

ReproductionBase -> NonWrightFisher -> BryophyteBase
                    WrightFisher       PteridophyteBase
                                       etc.
"""

from typing import TypeVar
from dataclasses import dataclass, field
import pyslim
import tskit
from loguru import logger
# from shadie.reproduction.scripts import ITER_CHECK_MUT_IS_SUB
from shadie.reproduction.scripts import (
    P0_FITNESS_SCALE_DEFAULT,
    P1_FITNESS_SCALE_DEFAULT,
    FIRST,
    EARLY,
    WF_REPRO_SOFT,
    WF_REPRO_HARD,
    HAP_MUT_FITNESS,
    DIP_MUT_FITNESS
)

logger = logger.bind(name="shadie")
Model = TypeVar("shadie.Model")


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
    >>> with shadie.Model() as model:
    >>>     model.initialize(...)
    >>>     model.early(...)
    >>>     model.reproduction.bryophyte(...)
    """
    model: Model

    def _write_trees_file(self) -> None:
        """adds late() call to save and write .trees file.

        All shadie reproduction classes write a .trees file in a late()
        call, but the time at which to write it varies depending on
        whether the start point was loaded from a previous file.
        """
        # get time AFTER the last even generation.

        gens = self._gens_per_lifecycle
        endtime = int((self.model.sim_time*gens) + 1)
        self.full_lifecycles = self.model.sim_time
        self.slim_gens = endtime

        # calculate end based on this sim AND the loaded parent sim.
        if self.model.metadata['file_in']:
            ts_start = tskit.load(self.model.metadata['file_in'])
            sim_start = ts_start.max_root_time
            resched_end = int(endtime + sim_start)
            self.model.late(
                time=resched_end,
                scripts=[
                    "sim.treeSeqRememberIndividuals(sim.subpopulations.individuals)",
                    f"sim.treeSeqOutput('{self.model.metadata['file_out']}', metadata = METADATA)"],
                comment="end of sim; save .trees file",
            )

        # write output at last generation of this simulation.
        else:
            self.model.late(
                time=endtime,
                scripts=[
                    "sim.treeSeqRememberIndividuals(sim.subpopulations.individuals)",
                    f"sim.treeSeqOutput('{self.model.metadata['file_out']}', metadata = METADATA)"],
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

    def _set_gametophyte_k(self):
        """Set carrying capacity for gametophyte holding pop (p1).

        During p1 generation, to avoid lagging in the simulation, this
        automatically sets to 10x user-defined popsize.
        """
        if not self.gam_ceiling:
            self.gam_ceiling = 10 * self.gam_pop_size

    def _define_subpopulations(self):
        """add haploid and diploid life stages as subpopulations.
        """
        # load a trees file that already has p0 and p1 pops
        if self.model.metadata['file_in']:
            # set p1 to tag=3 (sporophytes) and p0 to tag=[0,1] (gametophytes)
            self.model._read_from_file(tag_scripts=[
                "p1.individuals.tag = 3;",
                "tags = rbinom(1, p0.individualCount, 0.5);",
                "p0.individuals.tag = tags;",
            ])

        # create new p0 and p1 populations
        else:
            self.model.first(
                time=1,
                scripts=[
                    "sim.addSubpop('p1', SPO_POP_SIZE)",
                    "sim.addSubpop('p0', 0)",
                    "p1.individuals.tag = 3",
                    "p1.individuals.setValue('maternal_fitness', 1.0);",
                    "p1.individuals.tagL0 = (runif(p1.individualCount) < GAM_FEMALE_TO_MALE_RATIO);",
                ],
                comment="define subpops: p1=diploid sporophytes, p0=haploid gametophytes",
            )

    def _add_initialize_globals(self):
        """Add defineGlobal calls to init variables.

        When this is called by different superclasses that have
        different attributes unique to each it stores only their
        unique set of attributes into a metadata dictionary that
        will be saved into the .trees file at the end of the sim.
        Includes parent attrs like model.
        """
        # exclude parent class attributes
        exclude = [
            "_substitution_str", "model",
            "_p0activate_str", "_p0deactivate_str",
            "_p1activate_str", "_p1deactivate_str",
        ]
        asdict = {
            i: j for (i, j) in self.__dict__.items()
            if i not in exclude
        }
        # save initalize metadata and update with dict
        self.model.map["initialize"][0]['simglobals']['METADATA'] = self.model.metadata
        self.model.map["initialize"][0]['simglobals']['METADATA'].update(asdict)

    def _add_initialize_constants(self):
        """Add defineConstant calls to init variables.

        When this is called by different superclasses that have
        different attributes unique to each it stores only their
        unique set of attributes. Excludes parent attrs like model.
        """
        # exclude parent class attributes
        exclude = [
            "lineage", "mode", "model", "gens_per_lifecycle",
            "full_lifecycles", "slim_gens",
            "model_source","_substitution_str",
            "_p0activate_str", "_p0deactivate_str",
            "_p1activate_str", "_p1deactivate_str",
        ]

        asdict = {
            i: j for (i, j) in self.__dict__.items()
            if i not in exclude
        }
        self.model.map["initialize"][0]['constants'].update(asdict)

    def _add_alternation_of_generations(self):
        """Alternation of generations scripts.

        This writes mutEffect, early, and late functions that activate
        or deactivate mutEffect effects of mutations in alternating
        generations.
        """
        idx = 6

        # iterate over MutationTypes
        for mut in self.model.chromosome.mutations:
            # only execute below if the mutation doesn't affect all lifestages
            if not mut.affects_diploid or not mut.affects_haploid:

                # refer to mutations by s{idx}
                idx += 1
                # sidx = str("s" + str(idx))

                # add mutEffect callback function (e.g., s5 mutEffect(m1) {...})
                # for each MutationType. This callback will be activated or
                # deactivated (below) by early scripts based on whether
                # it is the haploid or diploid subpopulation's generation.
                if not mut.affects_diploid:
                    self.model.muteffect(
                        idx=None,
                        mutation=mut.name,
                        scripts=HAP_MUT_FITNESS,
                        comment="mutation only expressed in haploid"
                    )
                if not mut.affects_haploid:
                    self.model.muteffect(
                        idx=None,
                        mutation=mut.name,
                        scripts=DIP_MUT_FITNESS,
                        comment="mutation only expressed in diploid"
                    )

    def _add_first_script(self):
        """Defines the first() callbacks for each gen.

        This is overridden by callbacks of the same name in subclasses
        """
        self.model.first(
            time=None,
            scripts=FIRST,
            comment="alternation of generations",
        )

    def _add_early_script(self):
        """Defines the early() callbacks for each gen.

        This is overridden by callbacks of the same name in subclasses
        """
        early_script = (
            EARLY.format(
                p0_fitnessScaling=P0_FITNESS_SCALE_DEFAULT,
                p1_fitnessScaling=P1_FITNESS_SCALE_DEFAULT,
                gametophyte_clones=GAM_CLONES,
                gam_maternal_effect=GAM_MATERNAL_EFFECT_ON_P1,
                sporophyte_clones=SPO_CLONES,
                spo_maternal_effect=SPO_MATERNAL_EFFECT_ON_P0,
            )
        )
        self.model.early(
            time=None,
            scripts=early_script,
            comment="events after reproduction",
        )


@dataclass
class WrightFisher(ReproductionBase):
    """Reproduction mode based on Wright-Fisher model."""
    pop_size: int
    selection: str = "none"  # soft selection on by default
    _gens_per_lifecycle: int = 1  # internal param
    sexes: bool = False  # not yet used?

    def run(self):
        """Updates self.model.map with new component scripts for running
        life history and reproduction based on input args.
        """
        self._define_subpopulations()
        self._add_initialize_constants()
        self._add_scripts()
        self._add_survival_script()
        self._write_trees_file()

    def _define_subpopulations(self):
        """Add a single diploid population. See NonWrightFisher for comparison."""
        if self.model.metadata['file_in']:
            self.model._read_from_file(tag_scripts="")
        else:
            self.model.first(
                time=1,
                scripts="sim.addSubpop('p1', K);",
                comment="define starting diploid population.",
            )

    def _add_scripts(self):
        """fitness and mating of diploid population."""
        if self.selection == "soft":
            self.model.repro(
                population="p1",
                scripts= WF_REPRO_SOFT,
                comment="WF model with soft selection (parent fitness determines mating success)"
            )

        elif self.selection == "hard":
            self.model.repro(
                population="p1",
                scripts= WF_REPRO_HARD,
                comment="WF model with hard selection (random mating)"
            )
            self.model.early(
                time=None,
                scripts="p1.fitnessScaling = K / p1.individualCount",
                comment="calculate relative fitness.",
            )

        elif self.selection == "none":
            self.model.repro(
                population="p1",
                scripts= "subpop.addCrossed(individual, subpop.sampleIndividuals(1));",
                comment="WF model with no selection; random mating"
            )

    def _add_initialize_constants(self):
        """Add defineConstant calls to init for new variables."""
        metadata_dict = {
            'model': "shadie WF",
            'length': self.model.sim_time,
            'spo_pop_size': self.pop_size,
            'gam_pop_size': "NA",
            'spo_mutation_rate': self.model.metadata['mutation_rate'],
            'recombination_rate': self.model.metadata['recomb_rate'],
            'selection': self.selection,
            'gens_per_lifecycle': self._gens_per_lifecycle,
        }

        self.model.map["initialize"][0]['constants']["K"] = self.pop_size
        self.model.map["initialize"][0]['simglobals']["METADATA"] = metadata_dict

        # save initalize metadata and update from dict
        self.model.map["initialize"][0]['simglobals']['METADATA'] = self.model.metadata
        self.model.map["initialize"][0]['simglobals']['METADATA'].update(metadata_dict)

    def _add_survival_script(self):
        """Defines the late() callbacks for each gen.

        This overrides the NonWrightFisher class function of same name.
        """
        self.model.survival(
            population=None,
            scripts="return (individual.age == 0);",
            comment="non-overlapping generations",
        )


if __name__ == "__main__":

    import shadie
    shadie.set_log_level("DEBUG")

    # define mutation types
    m0 = shadie.mtype(0.5, 'n', [0, 0.4])
    m1 = shadie.mtype(0.5, 'g', [0.8, 0.75], affects_haploid=False)
    m0 = shadie.mtype(0.5, 'f', [2], affects_diploid=False)

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

    # generate a model w/ slim script
    with shadie.Model() as mod:
        mod.initialize(chromosome=chrom, sim_time=1000, )  # file_in="/tmp/test.trees")
        mod.reproduction.wright_fisher_haploid_sexual(pop_size=1000)
    # print(mod.script)
    mod.write("/tmp/slim.slim")
    mod.run(seed=123, binary="/home/deren/miniconda3/envs/shadie/bin/slim")  # /usr/local/bin/slim")
