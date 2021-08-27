#!/usr/bin/env python

"""
Starting an alternate implementation of Reproduction 
"""

from dataclasses import dataclass, field


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
class nonWFBase(ReproductionBase):
    lineage: str = field(default="Null", init=False)
    chromosome: 'shadie.chromosome.ChromosomeBase'

@dataclass
class Base(nonWFBase):
    """
    Reproduction mode based on Wright-Fisher model
    """
    ne: int
    sexes: bool = False
    startfile: str = "F"

    def run(self):
        """
        Updates self.model.map with new component scripts for running
        life history and reproduction based on input args.
        """

        self.add_initialize_constants()
        self.add_early_subpops()        


    def add_initialize_constants(self):
        """
        Add defineConstant calls to init for new variables
        """
        constants = self.model.map["initialize"][0]['constants']
        constants["K"] = self.ne

    def add_early_subpops(self):
        """
        add haploid and diploid life stages
        """
        if self.startfile == "F":
            self.model.early(
                time=1,
                scripts="sim.addSubpop('p1', K);", 
                comment="define starting population",
            )

        self.model.early(
            time=None, 
            scripts="p1.fitnessScaling = K / p1.individualCount;", 
            comment="alternation of generations",
        )

        self.model.repro(
            population="p1",
            scripts="subpop.addCrossed(individual,subpop.sampleIndividuals(1));",
            comment="hermaphroditc crossing"
            )


if __name__ == "__main__":


    import shadie
    with shadie.Model() as mod:
        
        # define mutation types
        m0 = shadie.mtype(0.5, 'n', 0, 0.4)
        m1 = shadie.mtype(0.5, 'g', 0.8, 0.75)
        #I suggest we add a checkpoint that calculates the average
        #fitness of mutations input by the user. If fitness is too high
        #the simuulation will lag tremendously. 
        # OK: a good use case for logger.warning('fitness is too high...')
        
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
        mod.initialize(chromosome=chrom, length=1000)

        mod.reproduction.base(
            ne = 1000,
        )

    print(mod.script)
    #mod.run()
