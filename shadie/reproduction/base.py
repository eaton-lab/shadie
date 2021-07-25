#!/usr/bin/env python

"""
Starting an alternate implementation of Reproduction 
"""

from typing import List
from dataclasses import dataclass, field
from shadie.reproduction.base_scripts import (
    EARLY_BRYO_DIO,
    FITNESS_BRYO_DIO_P0, FITNESS_BRYO_DIO_P1,
    ACTIVATE, DEACTIVATE, EARLY, SURV,
    REPRO_BRYO_DIO_P1, REPRO_BRYO_DIO_P0, SUBSTITUTION, SUB_INNER
)

DTYPES = ("d", "dio", "dioecy", "dioecious", "heterosporous", "dioicous")
MTYPES = ("m", "mono", "monoecy", "monecious", "homosporous", "monoicous")


@dataclass
class ReproductionBase:
    """
    Reproduction code block generation BaseClass. All Reproduction 
    subclasses will store the Model, lineage, mode, and a set of 
    script stored as a dictionary. Users will only interact with
    subclasses of ReproductionBase, generated by using the 
    ReproductionApi accessible from the Model object.

    Example
    -------
    with shadie.Model() as model:
        model.initialize(...)
        model.early(...)
        model.reproduction.bryophyte(...)
    """
    model: 'shadie.Model'

@dataclass
class BryophyteBase(ReproductionBase):
    lineage: str = field(default="Bryophyte", init=False)
    mode: str
    chromosome: any

@dataclass
class Bryophyte(BryophyteBase):
    """
    Reproduction mode based on mosses, hornworts, and liverworts
    """
    diploid_ne: int
    haploid_ne: int
    female_to_male_ratio: float=0.5
    spores_per_sporophyte: int=100
    clone_rate: float=1.0
    selfing_rate: float=0
    maternal_effect_weight: float=0
    random_death_chance: float=0


    def run(self) -> List[str]:
        """
        Returns a script as a list of strings by running the 
        appropriate life history functions based on input args.
        """
        self.add_initialize_constants()
        self.add_early_haploid_diploid_subpops()        
        if self.mode in DTYPES:
            self.dioicous()
        elif self.mode in MTYPES:
            self.monoicous()
        else:
            raise ValueError(
                f"'mode' not recognized, must be in {DTYPES + MTYPES}")


    def add_initialize_constants(self):
        """
        Add defineConstant calls to init for new variables
        """
        constants = self.model.map["initialize"][0]['constants']
        constants["dK"] = self.diploid_ne
        constants["hK"] = self.haploid_ne
        constants["Death_chance"] = self.random_death_chance
        constants["FtoM"] = self.female_to_male_ratio
        constants["Spore_num"] = self.spores_per_sporophyte
        constants["Clone_rate"] = self.clone_rate
        # constants["Clone_num"] = self.clone_number
        constants["Self_rate"] = self.selfing_rate
        constants["Maternal_weight"] = self.maternal_effect_weight


    def add_early_haploid_diploid_subpops(self):
        """
        add haploid and diploid life stages
        """
        self.model.early(
            time=1,
            scripts=["sim.addSubpop('p1', dK)", "sim.addSubpop('p0', hK)"],
            comment="define Bryophyte subpops: diploid sporophytes, haploid gametophytes",
        )


    def dioicous(self):
        """
        fills the script reproduction block with bryophyte-dioicous
        """

        #fitness callback:
        i = 4
        activate = []
        deactivate = []
        substitutions = []
        for mut in self.chromosome.mutations:
            i = i + 1
            idx = str("s"+str(i))
            active_script = ACTIVATE.format(**{'idx': idx}).lstrip()
            deactive_script = DEACTIVATE.format(**{'idx': idx}).lstrip()
            activate.append(active_script)
            deactivate.append(deactive_script)
            sub_inner = SUB_INNER.format(**{'idx': idx, 'mut': mut}).lstrip()
            substitutions.append(sub_inner)
            self.model.fitness(
                idx=idx,
                mutation=mut,
                scripts="return 1 + mut.selectionCoeff",
                comment="gametophytes have no dominance effects",
            )
            
        activate_str = ""
        deactivate_str = ""
        for i in activate:
            activate_str += "\n  ".join([i.strip(';') + ";\n    "])

        for i in deactivate:
            deactivate_str += "\n  ".join([i.strip(';') + ";\n    "])

        early_script = (
            EARLY.format(**{'activate': activate_str, 
                'deactivate': deactivate_str}).lstrip())

        self.model.early(
            time=None, 
            scripts=early_script, 
            comment="alternation of generations",
        )

        self.model.custom(SURV)

        self.model.repro(
            population = "p1",
            scripts = REPRO_BRYO_DIO_P1,
            comment = "generates gametes from sporophytes"
            )

        self.model.repro(
            population = "p0",
            scripts = REPRO_BRYO_DIO_P0,
            comment = "generates gametes from sporophytes"
            )

        substitution_str = ""
        for i in substitutions:
            substitution_str += "\n  ".join([i.strip(';') + ";\n    "])

        substitution_script = (
            SUBSTITUTION.format(**{'inner': substitution_str}).lstrip())

        self.model.late(
            time = None,
            scripts = substitution_script,
            comment = "fixes mutations in haploid gen"
            )


    def monoicous(self):
        """
        fills the script reproduction block with bryophyte-monoicous
        """



if __name__ == "__main__":


    import shadie
    with shadie.Model() as mod:
        
        # define mutation types
        m0 = shadie.mtype(0.5, 'n', 2.0, 1.0)
        m1 = shadie.mtype(0.5, 'g', 3.0, 1.0)
        
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

        # init the model
        mod.initialize(chromosome=chrom)

        mod.reproduction.bryophyte(
            mode='dio',
            chromosome = chrom,
            diploid_ne=1000, 
            haploid_ne=1000,
        )

    print(mod.script)
    #mod.run()
