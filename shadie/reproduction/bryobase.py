#!/usr/bin/env python

"""
Bryophyte reproduction class is a superclass of NonWrightFisher class.

Class inheritance structure
---------------------------
ReproductionBase
    WrightFisher
    NonWrightFisher
        Brypophyte
            BryophyteDioicous
            BryophyteMonoicous
"""

from typing import Tuple, Optional
from dataclasses import dataclass, field
from shadie.reproduction.base import NonWrightFisher
from shadie.reproduction.base_scripts import (
    EARLY,
    SURV,
    MATERNAL_EFFECT,
    SUBSTITUTION,
    SUB_INNER,
)
from shadie.reproduction.bryo_scripts import (
    REPRO_BRYO_DIO_P1,
    REPRO_BRYO_DIO_P0,
    REPRO_BRYO_MONO_P1,
    REPRO_BRYO_MONO_P0,
)


DTYPES = ("dioicy", "dioicous", "heterosporous")
MTYPES = ("monoicy", "monoicous", "homosporous")


@dataclass
class Bryophyte(NonWrightFisher):
    """Reproduction mode based on mosses, hornworts, and liverworts."""
    lineage: str = field(default="Bryophyte", init=False)
    spo_pop_size: int
    gam_pop_size: int
    spo_mutation_rate: Optional[float]=None
    gam_mutation_rate: Optional[float]=None
    spo_spores_per: int=500
    gam_sporophytes_per: int=10
    gam_clone_rate: float=0.8
    gam_clone_number: int=100
    gam_maternal_effect: float=0.5
    spo_self_rate: float=0.1
    spo_random_death_chance: float=0.08
    gam_random_death_chance: float=0.08

    def _set_mutation_rates(self):
        """Set mutation rates for both, or use Model rate / 2 for both."""
        if self.spo_mutation_rate or self.gam_mutation_rate:
            require_spo = self.spo_mutation_rate is not None
            require_gam = self.gam_mutation_rate is not None
            assert require_gam and require_spo, (
                "You must define a mutation rate for both sporophyte "
                "and gametophyte generations.")
        else:
            self.spo_mutation_rate = 0.5 * self.model._mutation_rate
            self.gam_mutation_rate = 0.5 * self.model._mutation_rate

    def _add_shared_mode_scripts(self):
        """Fills model.map scripts applying to heterosp or homosp bryos.

        This will define survival callback functions s5-s8 which are
        turned on or off depending on model parameters.
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
            sub_inner = SUB_INNER.format(idx=sidx, mut=mut.name).lstrip()
            substitutions.append(sub_inner)

        # insert references to fitness callbacks into an early script
        # that will alternately activate or deactivate them on
        # alternating generations to only apply to gameto or sporo.
        activate_str = "\n    ".join(activate_scripts)
        deactivate_str = "\n    ".join(deactivate_scripts)
        early_script = (
            EARLY.format(activate=activate_str, deactivate=deactivate_str)
        )
        self.model.early(
            time=None,
            scripts=early_script,
            comment="alternation of generations",
        )

        # add a survival script which defines the random_chance of death
        # and also the survival=0 for alternation of generations.
        survival_script = (
            SURV.format(
                p0maternal_effect="",
                p1maternal_effect=MATERNAL_EFFECT,
                p0survival="return NULL;"
            )
        )
        self.model.custom(survival_script, comment="maternal effects and survival")

        # insert the substitution-checking scripts into larger context
        # and add as a late call.
        substitution_str = "\n    ".join(substitutions)
        substitution_script = (
            SUBSTITUTION.format(inner=substitution_str))
        self.model.late(
            time=None,
            scripts=substitution_script,
            comment="fixes mutations in haploid gen"
        )

    def _initialize_constants(self):
        """Add defineConstant calls to init variables.

        When this is called by different superclasses of Bryophyte
        that have different attributes unique to each it stores only
        its own unique set of attributes.
        """
        # exclude parent class attributes
        exclude = ["lineage", "mode", "model"]
        asdict = {
            i: j for (i, j) in self.__dict__.items()
            if i not in exclude
        }
        self.model.map["initialize"][0]['constants'].update(asdict)


@dataclass
class BryophyteDioicous(Bryophyte):
    mode: str = field(default="heterosporous", init=False)
    gam_female_to_male_ratio: Tuple[float,float]=(2, 1)
    spo_megaspores_per: int=1
    spo_microspores_per: int=1

    def run(self):
        """Fill self.model.map with SLiM script snippets."""
        # methods inherited from parent NonWrightFisher class
        self._define_subpopulations()
        self._write_trees_file()

        # methods inherited from parent Bryophyte class
        self._set_mutation_rates()
        self._add_shared_mode_scripts()

        # mode-specific functions
        self._set_gam_female_to_male_ratio_as_float()        
        self._initialize_constants()
        self._add_mode_scripts()

    def _set_gam_female_to_male_ratio_as_float(self):
        """Convert tuple ratio to a float."""
        sum_ratio = sum(self.gam_female_to_male_ratio)
        float_ratio = self.gam_female_to_male_ratio[0] / sum_ratio
        self.gam_female_to_male_ratio = float_ratio

    def _add_mode_scripts(self):
        """Add reproduction scripts unique to heterosporous bryo."""
        self.model.repro(
            population="p1",
            scripts=REPRO_BRYO_DIO_P1,
            comment="generates gametes from sporophytes"
        )
        self.model.repro(
            population="p0",
            scripts=REPRO_BRYO_DIO_P0,
            comment="generates gametes from sporophytes"
        )


@dataclass
class BryophyteMonoicous(Bryophyte):
    mode: str = field(default="homosporous", init=False)
    gam_self_rate: float=0.2

    def run(self):
        """Fill self.model.map with SLiM script snippets."""
        # methods inherited from parent NonWrightFisher class
        self._define_subpopulations()
        self._write_trees_file()

        # methods inherited from parent Bryophyte class
        self._set_mutation_rates()
        self._add_shared_mode_scripts()

        # mode-specific functions
        self._initialize_constants()
        self._add_mode_scripts()

    def _add_mode_scripts(self):
        """fills the model.map block with bryophyte-monoicous scripts."""
        # add reproduction scripts
        self.model.repro(
            population="p1",
            scripts=REPRO_BRYO_MONO_P1,
            comment="generates gametes from sporophytes"
        )
        self.model.repro(
            population="p0",
            scripts=REPRO_BRYO_MONO_P0,
            comment="generates gametes from sporophytes"
        )



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
        mod.initialize(chromosome=chrom, sim_time=50, file_out="/tmp/test.trees")
        mod.reproduction.bryophyte_dioicous(
            spo_pop_size=100,
            gam_pop_size=100,
        )
    mod.write("/tmp/slim.slim")
    mod.run(binary="/usr/local/bin/slim", seed=123)
