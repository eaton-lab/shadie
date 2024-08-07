#!/usr/bin/env python

"""
Generates Elements to represent chromosome structure for SLiM simulation
"""

from typing import Union, List
import itertools
import pandas as pd
import numpy as np
from loguru import logger

# internal imports
from shadie.base.elements import ElementType
from shadie.base.defaults import SYN, NONCDS, INTRON, EXON, NEUT


class ChromosomeBase:
    """
    Base Chromosome superclass. This class contains functions that 
    are inherited by the Chromosome classes users will initialize
    using convenience functions, such as default, random, or explicit.
    This superclass is used to define functions shared by all of the
    subclasses, such as inspect, or for writing data to SLiM format.

    Parameters:
    -----------
    genome_size: int
        The size of the genome in bp
    nucleotides: bool
        Use initializeMutationTypeNuc instead of initializeMutationType
    """
    def __init__(self, genome_size, use_nucleotides=False):
        self.genome_size = genome_size
        self.data = pd.DataFrame(
            columns=['name', 'start', 'end', 'eltype', 'script', 'coding'],
            data=None,
        )
        self.mutations = []
        self.use_nuc = use_nucleotides


    def inspect(self):
        """
        Visualize chromosome structure using altair interactive.
        """
        return ""

    def to_slim_mutation_types(self):
        """
        Returns a string with newline separated SLIM commands to 
        initialize all MutationType objects in the chromosome data.

        Example:
        --------
        initializeMutationType("m1", 0.5, "f", 0.0);         
        initializeMutationTypeNuc("m2", 0.1, "g", -0.03, 0.2);  
        """
        elements = self.data.script.unique()
        mut_lists = [i.mlist for i in elements]
        mutations = set(itertools.chain(*mut_lists))
        return "\n  ".join([i.to_slim(nuc=self.use_nuc) for i in mutations])

    def to_slim_element_types(self):
        """
        Returns a string with newline separated SLIM commands to 
        initialize all ElementType objects in the chromosome data.
    
        Example:
        --------
        initializeGenomicElementType("g1", c(m1,m2), c(3,3), mm);
        initializeGenomicElementType("g2", c(m1,m2), c(5,1), mm);
        """
        elements = self.data.script.unique()
        return "\n  ".join([i.to_slim() for i in elements])

    def to_slim_elements(self):
        """
        Returns a string with newline separated SLIM commands to 
        initialize all Element objects in the chromosome data.
    
        Example:
        --------
        initializeGenomicElement(g3, 0, 4684);
        initializeGenomicElement(g1, 4685, 4708);
        """
        #Note: will need to fix the formatting on this chunk**
        commands = []

        # iterate over int start positions of elements
        for idx in self.data.index:

            # skip non-coding regions
            if self.data.loc[idx, "coding"] == 0:
                #commands.append(
                    #"initializeGenomicElement({}, {}, {});"
                    #.format(*self.data.loc[idx, ["eltype", "start", "end"]])
                    #)
                pass

            # define synonymous type at every 3rd position?
            # TODO: we need to require exons == length multiples of 3 
            # we should really stop users from mixing in neutral and non-neutral mutations
            if self.data.loc[idx, "coding"] == 1:
                ele = self.data.loc[idx]
                commands.append(
                    f"initializeGenomicElement({ele.eltype}, {ele.start}, {ele.end});"
                )
                # COMMENTING OUT FOR NOW while working on reproduction.
                # length = ele.end - ele.start
                # commands.append(
                #     f"types = rep({ele.eltype}, {length}); "
                #     f"starts = {ele.start} + seqLen(integerDiv({length}, 3)) * 3; "
                #     "ends = starts + 1; "
                #     "initializeGenomicElement(types, starts, ends); "
                # )
        return "\n  ".join(commands)


class Chromosome(ChromosomeBase):
    """
    Builds the default shadie chromosome used for testing.
    """
    def __init__(self):
        super().__init__(genome_size=10001)

        self.data.loc[0] = (
            NONCDS.altname, 0, 2000, NONCDS.name, NONCDS)
        self.data.loc[2001] = (
            EXON.altname, 2001, 4000, EXON.name, EXON)
        self.data.loc[4001] = (
            INTRON.altname, 4001, 6000, INTRON.name, INTRON)
        self.data.loc[6001] = (
            EXON.altname, 6001, 8000, EXON.name, EXON)
        self.data.loc[8001] = (
            NONCDS.altname, 8001, 10000, NONCDS.name, NONCDS)

        mutations = []
        for element in self.data.values():
            for mutation in element.mlist:
                if mutation.name not in mutations:
                    mutations.append(mutation.name)
        self.mutations = mutations


class ChromosomeRandom(ChromosomeBase): 
    """
    Generates a random chromosome from of a given length from a set of
    intron, exon, and non-cds genomic ElementType objects. The default
    elements are used if not entered by the user.
    """
    def __init__(
        self, 
        genome_size:int=20000, 
        intron:ElementType=None,
        exon:ElementType=None,
        noncds:ElementType=None,
        seed:Union[int, None]=None,
        ):

        super().__init__(genome_size)
        self.rng = np.random.default_rng(seed)
        self.intron = intron if intron is not None else INTRON
        self.exon = exon if exon is not None else EXON
        self.noncds = noncds if noncds is not None else NONCDS

        elements = [self.intron, self.exon, self.noncds]
        mutations = []
        for elem in elements:
            for mutation in elem.mlist:
                if mutation.name not in mutations:
                    mutations.append(mutation.name)
        self.mutations = mutations


    def get_noncds_span(self, scale:int=5000) -> int:
        """
        Draws the number of bases until the next element from an 
        exponential distribution. The scale is the average waiting
        time in number of bp.
        """
        return int(self.rng.exponential(scale=scale))


    def get_cds_spans(self, length_scale:int=1000, intron_scale:int=1000) -> List[int]:
        """
        Draws the number of exons in a fixed length space from a 
        Poisson distribution. The lam parameter is the average number
        of events per sampled region. A value of 0.005 means one 
        intron per 200bp.
        """
        cds_span = int(self.rng.exponential(scale=length_scale))
        n_introns = int(self.rng.poisson(lam=cds_span / intron_scale))
        if n_introns:
            splits = self.rng.dirichlet(np.ones(n_introns * 2 - 1))
            splits = (splits * cds_span).astype(int)
            splits[-1] = cds_span - sum(splits[:-1])
        else:
            splits = [cds_span]
        return splits


    def run(self, noncds_scale=5000, cds_scale=1000, intron_scale=1000) -> None:
        """
        Generates a chromosome by randomly sampling waiting times 
        between CDS regions, and the number of introns within CDS
        regions.
        """
        idx = 0
        while 1:
            # start with a non-cds span
            span = self.get_noncds_span(noncds_scale)
            self.data.loc[idx] = (
                self.noncds.altname, 
                idx + 1, 
                min(idx + 1 + span, self.genome_size), 
                self.noncds.name, self.noncds,
                self.noncds.coding,
            )
            idx += span + 1
            
            # get a cds span
            spans = self.get_cds_spans(cds_scale, intron_scale)

            # break if cds goes beyond the end of the genome.
            if idx + sum(spans) + len(spans) > self.genome_size:
                break

            # enter the cds into data
            for enum, span in enumerate(spans):
                # even numbered segments are the exons (0, 2, 4)
                if not enum % 2:
                    self.data.loc[idx] = (
                        self.exon.altname, 
                        idx + 1, 
                        idx + span + 1, 
                        self.exon.name, self.exon,
                        self.exon.coding,
                    )
                else:
                    self.data.loc[idx] = (
                        self.intron.altname,
                        idx + 1,
                        idx + span + 1,
                        self.intron.name, self.intron, 
                        self.intron.coding,
                    )
                idx += span + 1
        self.data = self.data.sort_index()


class ChromosomeExplicit(ChromosomeBase):
    """
    Builds a chromosome dataframe from explicit instructions provided
    as start, stop positions mapped to ElementTypes. To add a regions
    without an assigned element...

    chromosome.explicit({
        (500, 1000): g1,
        (2000, 3000): g2,
        (3001, 5000): g1,
        (5000, 10000): None,
    })
    """
    def __init__(self, data):
        super().__init__(genome_size=max([i[1] + 1 for i in data.keys()]))

        # check data dict for proper structure
        assert all(isinstance(i, tuple) for i in data.keys()), (
            "keys of input data should be tuples of integers.")
        assert all(isinstance(i, ElementType) for i in data.values() if i), (
            "values of input data should be ElementType objects.")

        mutations = []
        for element in data.values():
            for mutation in element.mlist:
                if mutation.name not in mutations:
                    mutations.append(mutation.name)
        self.mutations = mutations

        # entere explicit dict into data
        for key in sorted(data, key=lambda x: x[0]):
            start, end = key
            if data[key] is not None:
                self.data.loc[start] = (
                    data[key].altname, start, end, data[key].name, data[key], data[key].coding)


if __name__ == "__main__":


    import shadie

    # define mutation types
    m0 = shadie.mtype(0.5, 'n', 2.0, 1.0)
    m1 = shadie.mtype(0.5, 'g', 3.0, 1.0)
    m2 = shadie.mtype(0.5, 'f', 0)
    
    # define elements types
    e0 = shadie.etype([m0, m1], [1, 2])
    e1 = shadie.etype([m2], [1])

    # print(e0.mlist)

    chrom = shadie.chromosome.random(100000)
    print(chrom.data.iloc[:50, :4])

    # # design chromosome of elements
    # # Do we want users to be able to put in a chromosome like this 
    # # and have the gaps filled with neutral portions? YES.
    # chrom = shadie.chromosome.explicit({
    #     (500, 1000): e1,
    #     (2000, 3000): e0,
    #     (3001, 5000): e1,
    # })

    # #elem = chrom.data.loc[500]["eltype"]
    # #chrom.to_slim_mutation_types()
    # test = chrom.mutations
    # print(chrom.data.head())
    # # print(test)
    # # chrom.to_slim_elements()