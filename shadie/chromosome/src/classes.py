#!/usr/bin/env python

"""Superclasses of ChromosomeBase for generating Elements to represent
a Chromosome structure. ChromosomeBase has functions to visualize
these chroms and to convert them to SLiM simulation commands.

These classes are for internal use only. They are exposed in user-
facing functions in :meth:`shadie.chromosome`.
"""

from typing import Union, List, Optional
import numpy as np

# internal imports
from shadie.base.elements import ElementType
from shadie.base.defaults import SYN, NONCDS, INTRON, EXON, NEUT, BEN, DEL, EMPTY
from shadie.chromosome.src.base_class import ChromosomeBase


class Chromosome(ChromosomeBase):
    """Builds the default shadie chromosome used for testing.

    This chromosome is exposed to users in a factory function at
    :meth:`shadie.chromosome.default`.
    """
    def __init__(
        self,
        use_nucleotides: bool=False,
        use_synonymous_sites_in_coding: bool=False,
    ):
        # init from ChromosomeBase
        super().__init__(
            genome_size=10001,
            use_nucleotides=use_nucleotides,
            use_synonymous_sites_in_coding=use_synonymous_sites_in_coding,
        )
        # create default chromosome
        self.data.loc[0] = (
            NONCDS.altname, 0, 2000, NONCDS.name, NONCDS, NONCDS.is_coding)
        self.data.loc[2001] = (
            EXON.altname, 2001, 4000, EXON.name, EXON, EXON.is_coding)
        self.data.loc[4001] = (
            INTRON.altname, 4001, 6000, INTRON.name, INTRON, INTRON.is_coding)
        self.data.loc[6001] = (
            EXON.altname, 6001, 8000, EXON.name, EXON, EXON.is_coding)
        self.data.loc[8001] = (
            NONCDS.altname, 8001, 10000, NONCDS.name, NONCDS, NONCDS.is_coding)


class ChromosomeRandom(ChromosomeBase):
    """Builds a random chromosome given defined element types.

    This chromosome builder is exposed to users in a factory function
    at :meth:`shadie.chromosome.random`.

    The chromosome will be a set length and composed randomly of
    intron, exon, and non-cds genomic ElementTypes with their
    relative weights scaled by args to the self.run() function.
    Default ElementTypes are used if not entered by the user.

    Examples
    --------
    >>> chrom = ChromosomeRandom()
    >>> chrom.run()
    """
    def __init__(
        self,
        genome_size: int=20000,
        intron: Union[None, ElementType, List[ElementType]]=None,
        exon: Union[None, ElementType, List[ElementType]]=None,
        noncds: ElementType=None,
        gene_size: Union[int, None]=None,
        intron_scale: Union[int, None]=None,
        cds_scale: Union[int, None]=None,
        noncds_scale: Union[int, None]=None,
        seed: Union[int, None]=None,
        use_nucleotides: bool=False,
        use_synonymous_sites_in_coding: bool=False,
    ):

        super().__init__(
            genome_size=genome_size,
            use_nucleotides=use_nucleotides,
            use_synonymous_sites_in_coding=use_synonymous_sites_in_coding,
        )
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.intron = intron if intron is not None else INTRON
        self.exon = exon if exon is not None else EXON
        self.noncds = noncds if noncds is not None else NONCDS
        self.genome_size = int(genome_size - 1)
        self.gene_size = genome_size
        self.intron_scale = intron_scale
        self.cds_scale = cds_scale
        self.noncds_scale = noncds_scale

    def get_noncds_span(self, scale:int) -> int:
        """
        Draws the number of bases until the next element from an
        exponential distribution. The scale is the average waiting
        time in number of bp.
        """
        scale=self.noncds_scale
        return int(self.rng.exponential(scale=scale))

    def get_cds_spans(self, length_scale:int, intron_scale:int) -> List[int]:
        """
        Draws the number of exons in a fixed length space from a
        Poisson distribution. The lam parameter is the average number
        of events per sampled region. A value of 0.005 means one
        intron per 200bp.
        """
        length_scale = self.gene_size, 
        intron_scale = self.intron_scale
        cds_span = int(self.rng.exponential(scale=length_scale))
        n_introns = int(self.rng.poisson(lam=cds_span / intron_scale))
        if n_introns:
            while True:
                splits = self.rng.dirichlet(np.ones(n_introns * 2 - 1))
                splits = (splits * cds_span).astype(int)
                splits[-1] = cds_span - sum(splits[:-1])
                if all(i > 3 for i in splits):
                    break
        else:
            splits = [cds_span]
        return splits

    def run(self, noncds_scale, cds_scale, intron_scale) -> None:
        """Generates a random chromosome by sampling elements.

        Waiting times are randomly sampled between CDS regions, as are
        the number of introns within CDS regions.
        """
        noncds_scale = self.noncds_scale
        cds_scale = self.cds_scale
        intron_scale = self.intron_scale
        idx = 0
        while 1:
            # start with a non-cds span
            span = self.get_noncds_span(noncds_scale)
            self.data.loc[idx] = (
                self.noncds.altname,
                idx + 1,
                min(idx + 1 + span, self.genome_size),
                self.noncds.name, self.noncds,
                self.noncds.is_coding,
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
                    if isinstance(self.exon, list):
                        ele = self.rng.choice(self.exon)
                    else:
                        ele = self.exon
                else:
                    if isinstance(self.intron, list):
                        ele = self.rng.choice(self.intron)
                    else:
                        ele = self.intron
                self.data.loc[idx] = (
                    ele.altname,
                    idx + 1,
                    idx + span + 1,
                    ele.name, ele,
                    ele.is_coding,
                )
                idx += span + 1
        self.data = self.data.sort_index()


class ChromosomeExplicit(ChromosomeBase):
    """Builds a chromosome from a dict of explicit intervals.

    Instructions provided as start, stop positions mapped to
    ElementTypes.

    Example
    -------
    chromosome.explicit({
        (500, 1000): g1,
        (2000, 3000): g2,
        (3001, 5000): g1,
        (5000, 10000): None,
    })
    """
    def __init__(
        self,
        data,
        genome_size: Optional[int]=None,
        use_nucleotides: bool=False,
        use_synonymous_sites_in_coding: bool=False,
        ):
        if genome_size is not None:
            genome_size = genome_size
        else:
            genome_size = 1 + (max(i[1] for i in data.keys()))

        super().__init__(
            genome_size,
            use_nucleotides,
            use_synonymous_sites_in_coding,
        )

        # check data dict for proper structure
        assert all(isinstance(i, tuple) for i in data.keys()), (
            "keys of input data should be tuples of integers.")
        assert all(isinstance(i, ElementType) for i in data.values() if i), (
            "values of input data should be ElementType objects.")

        # enter explicit dict into data
        for key in sorted(data, key=lambda x: x[0]):
            start, end = key
            if data[key] is not None:
                self.data.loc[start] = (
                    data[key].altname,
                    start,
                    end,
                    data[key].name,
                    data[key],
                    data[key].is_coding,
                )


if __name__ == "__main__":

    import shadie

    # define mutation types
    m0 = shadie.mtype(0.5, 'n', [2.0, 1.0])
    m1 = shadie.mtype(0.5, 'g', [3.0, 1.0])
    m2 = shadie.mtype(0.5, 'f', [0])

    # define elements types
    e0 = shadie.etype([m0, m1], [1, 2])
    e1 = shadie.etype([m2], [1])

    # # print(e0.mlist)

    # chrom = shadie.chromosome.random(100000)
    # #print(chrom.data.iloc[:50, :4])
    # #chrom.review("chromosome")

    # default = shadie.chromosome.default()
    # print(default.data)

    # design chromosome of elements
    # Do we want users to be able to put in a chromosome like this
    # and have the gaps filled with neutral portions? YES.
    # chrom = shadie.chromosome.explicit(
    #     data = {
    #     (0, 500): shadie.NONCDS,
    #     (500, 1000): e1,
    #     (2000, 3000): e0,
    #     (3001, 5000): e1,
    #     },
    #     use_synonymous_sites_in_coding=False,
    #     use_nucleotides=False,
    # )
    e0 = shadie.base.defaults.NONCDS

    chrom2 = shadie.chromosome.explicit(
        data={(0, 1000): NONCDS}
    )

    # elem = chrom.data.loc[500]["eltype"]
    # chrom.to_slim_mutation_types()
    test = chrom2.mutations
    # print(chrom.data.head())

    print(chrom2.data)
    print(test)
    print(chrom2.elements)
    # chrom.inspect()
    # print(test)
    print(chrom2.to_slim_elements())

    #print(chrom._skip_neutral_mutations)
