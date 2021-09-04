#!/usr/bin/env python

"""
API to make reproduction functions accessible from Model object.
These are the main user-facing options for implementing life 
histories into SLiM scripts using the shadie Model context.
"""
from typing import Union

#internal imports
from shadie.reproduction.optimized.base_wf import Base
from shadie.reproduction.optimized.bryophyte import Bryophyte
from shadie.reproduction.optimized.spermatophyte import Spermatophyte
from shadie.reproduction.optimized.pteridophyte import Pteridophyte


class ReproductionApi:
    """API for generating organism specific reproduction code blocks.

    Methods
    -------
    bryophyte
    spermatphyte
    angiosperm
    """
    def __init__(self, model: 'shadie.Model'):
        self.model = model

    def bryophyte(
        self, 
        mode:str, 
        spo_pop_size: int,
        gam_pop_size: int,
        spo_mutation_rate: Union[None, float]=None,
        gam_mutation_rate: Union[None, float]=None,
        spo_spores_per: int=100,
        gam_sporophytes_per: int = 10,
        gam_female_to_male_ratio: float.as_integer_ratio = (1,1),
        gam_clone_rate: float=0.0,
        gam_clone_number: int = 1,
        spo_self_rate: float=0.0,
        gam_self_rate: float=0.0,
        spo_maternal_effect: float=0,
        gam_maternal_effect: float=0,
        spo_random_death_chance:float=0,
        gam_random_death_chance: float=0, 
        _file_in = None,
        _chromosome=None,
        _sim_time = None,  
        _file_out = None,          
        ):
        """Adds bryo life history to the model scripts dict.

        Generate scripts appropriate for a bryophyte (moss, liverwort,
        or hornwort) life history. This adds code to the following 
        SLiM script blocks: reproduction, early, ...

        Parameters
        ----------
        mode: str
            A life history strategy: "dio" or "mono"-icous. 
        spo_pop_size: int
            Sporophyte (diploid) effective population size.
        gam_pop_size: int
            Gametophyte (haploid) effective population size.
        spo_mutation_rate: float
            Sporophyte mutation rate; chance mutations will arise during
            the sporophyte generation
        gam_mutation_rate: float
            Gametophyte mutation rate; chance mutations will arise during
            the gametophyte generation
        spo_spores_per: int
            Number of spores generated by each sporophyte.
        gam_female_to_male_ratio: tuple
            Gametophyte female:male ratio; e.g. (1,1) means F:M ratio of 
            1:1. In homosporous Pteridophyte model this is represents 
            hermaphrodite:male ratio.
        gam_clone_rate: float
            Chance a gametophyte will clone
        gam_selfing_rate: float
            Chance a gametophyte will engage in gametophytic selfing
        gam_maternal_effect_weight: float
            Maternal contribution to diploid offspring fitness (as
            weighted average)
        spo_random_death_chance:float
            Random chance a sporophyte will die before reproducing, 
            regardless of fitness. 
        gam_random_death_chance: float
            Random chance a gametophyte will die before reproducing,
            regardless of fitness
        file_in: str
            Provide a .trees file that will serve as the starting 
            point for the simulation
        ...
        """
        Bryophyte(
            model=self.model,
            mode=mode, spo_pop_size=spo_pop_size, gam_pop_size=gam_pop_size,
            spo_mutation_rate=spo_mutation_rate,
            gam_mutation_rate=gam_mutation_rate, 
            gam_female_to_male_ratio=gam_female_to_male_ratio,
            spo_spores_per=spo_spores_per, gam_sporophytes_per=gam_sporophytes_per,
            gam_clone_rate=gam_clone_rate,
            gam_clone_number=gam_clone_number,
            spo_self_rate=spo_self_rate, gam_self_rate=gam_self_rate,
            gam_maternal_effect=gam_maternal_effect,
            spo_random_death_chance=spo_random_death_chance,
            gam_random_death_chance=gam_random_death_chance,
            _file_in=self.model.file_in, _chromosome=self.model.chromosome, 
            _sim_time = 2*self.model.sim_time, 
            _file_out = self.model.file_out,
        ).run()

    def pteridophyte(
        self, 
        mode:str, 
        spo_pop_size: int,
        gam_pop_size: int,
        spo_mutation_rate: Union[None, float]=None,
        gam_mutation_rate: Union[None, float]=None,
        spo_spores_per: int=100,
        spo_female_to_male_ratio: float.as_integer_ratio = (1,1),
        gam_female_to_male_ratio: float.as_integer_ratio = (1,1),
        spo_clone_rate: float=0.0,
        spo_clone_number: int=1,
        spo_self_rate: float=0.0,
        gam_clone_rate: float=0.0,
        gam_clone_number: int=1,
        gam_self_rate: float=0.0,
        spo_maternal_effect: float=0,
        gam_maternal_effect: float=0,
        spo_random_death_chance: float=0, 
        gam_random_death_chance: float=0,
        _chromosome=None,
        _sim_time = None, 
        _file_in = None, 
        _file_out = None,       
        ):
        """
        Generate scripts appropriate for an pteridophyte (lycophytes 
        and ferns) life history.

        Parameters:
        -----------
        mode: str
            A life history strategy or "homo" or "hetero" -sporous.
        spo_pop_size: int
            Sporophyte (diploid) effective population size.
        gam_pop_size: int
            Gametophyte (haploid) effective population size.
        spo_mutation_rate: float
            Sporophyte mutation rate; chance mutations will arise during
            the sporophyte generation
        gam_mutation_rate: float
            Gametophyte mutation rate; chance mutations will arise during
            the gametophyte generation
        spo_spores_per: int
            Number of spores generated by each spororphyte.
        spo_female_to_male_ratio: tuple
            Sporophyte female:male ratio; e.g. (1,1) 
        gam_female_to_male_ratio: tuple
            Gametophyte female:male ratio; e.g. (1,1)
        spo_clone_rate: float
            Chance a sporophyte will clone
        gam_clone_rate: float
            Chance a gametophyte will clone
        gam_selfing_rate: float
            Chance a gametophyte will engage in gametophytic selfing
        gam_maternal_effect_weight: flat
            Maternal contribution to diploid offspring fitness (as
            weighted average)
        spo_random_death_chance:float
            Random chance a sporophyte will die before reproducing, 
            regardless of fitness. 
        gam_random_death_chance: float
            Random chance a gametophyte will die before reproducing,
            regardless of fitness
        file_in: str
            Provide a .trees file that will serve as the starting 
            point for the simulation
        ...
        """
        Pteridophyte(
            model=self.model, mode=mode, spo_pop_size=spo_pop_size, gam_pop_size=gam_pop_size,
            spo_mutation_rate = spo_mutation_rate,
            gam_mutation_rate = gam_mutation_rate, 
            spo_female_to_male_ratio = spo_female_to_male_ratio,
            gam_female_to_male_ratio = gam_female_to_male_ratio,
            spo_spores_per=spo_spores_per,
            spo_clone_rate=spo_clone_rate, 
            spo_clone_number = spo_clone_number,
            gam_clone_rate=gam_clone_rate,
            gam_clone_number = gam_clone_number,
            spo_self_rate=spo_self_rate, gam_self_rate=gam_self_rate,
            spo_maternal_effect=spo_maternal_effect,
            gam_maternal_effect=gam_maternal_effect,
            spo_random_death_chance=spo_random_death_chance, 
            gam_random_death_chance=gam_random_death_chance,
            _chromosome=self.model.chromosome,
            _sim_time = 2*self.model.sim_time, 
            _file_in=self.model.file_in,
            _file_out = self.model.file_out,
        ).run()


    def spermatophyte(
        self, 
        mode:str, 
        spo_pop_size: int,
        gam_pop_size: int,
        spo_mutation_rate: Union[None, float]=None,
        gam_mutation_rate: Union[None, float]=None,
        spo_female_to_male_ratio: float.as_integer_ratio = (1,1),
        spo_clone_rate: float=0.0,
        spo_clone_number: int =1,
        spo_self_rate: float=0.0,
        flower_ovules_per: int=30,
        flower_pollen_per: int=100,
        ovule_fertilization_rate: float=0.7,
        pollen_success_rate: float=1.0,
        pollen_comp: str="F",
        stigma_pollen_per: int=8,
        spo_maternal_effect: float=0,
        spo_random_death_chance: float=0,  
        gam_random_death_chance: float=0, 
        _chromosome=None,
        _sim_time = None, 
        _file_in = None, 
        _file_out = None, 
        ):
        """
        Generate scripts appropriate for an angiosperm (flowering plant)
        life history. Appropriate for gymnosperms as well.
        This adds code to the following 
        SLiM script blocks: reproduction, early, ...

        Parameters:
        -----------
        mode: str
            A life history strategy or "dio" or "mono" -ecious.
        spo_pop_size: int
            Sporophyte (diploid) effective population size.
        gam_pop_size: int
            Gametophyte (haploid) effective population size.
        spo_mutation_rate: float
            Sporophyte mutation rate; chance mutations will arise during
            the sporophyte generation
        gam_mutation_rate: float
            Gametophyte mutation rate; chance mutations will arise during
            the gametophyte generation. Default = 0
        spo_female_to_male_ratio: tuple
            Sporophyte female:male ratio; e.g. (1,1) 
        gam_female_to_male_ratio: tuple
            Gametophyte female:male ratio; e.g. (1,1)
        spo_clone_rate: float
            Chance a sporophyte will clone
        spo_clone_number: int
            Number of clones produced by each clonal sporophyte
        flower_ovules_per: int
            Number of ovules per sporophyte (remmeber to multiply number
            of flowers on each individual by number of ovules)
        ovule_fertilization_rate: float
            chance an ovule will be viable and set seed
        pollen_succcess_rate: float
            chance a give pollen will succcessfully fertilize an ovule
        flower_pollen_per: int
            number of pollen produced by each sporophyte
        pollen_comp: str="F" or "T"
            turn pollen competition on or off
        pollen_per_ovule: int
            number of pollen that will compete to fertilize a single 
            ovule *TODO: update code so that they compete for ALL the
            ovules in a given flower
        spo_maternal_effect_weight: float
            Maternal contribution to haploid offspring fitness (as
            weighted average)
        spo_random_death_chance:float
            Random chance a sporophyte will die before reproducing, 
            regardless of fitness. 
        gam_random_death_chance: float
            Random chance a gametophyte will die before reproducing,
            regardless of fitness
        ...
        """
        Spermatophyte(
            model=self.model, mode=mode,spo_pop_size=spo_pop_size, gam_pop_size=gam_pop_size,
            spo_mutation_rate = spo_mutation_rate,
            gam_mutation_rate = gam_mutation_rate, 
            spo_female_to_male_ratio = spo_female_to_male_ratio,
            spo_clone_rate=spo_clone_rate, 
            spo_clone_number = spo_clone_number, 
            spo_self_rate=spo_self_rate,
            flower_ovules_per=flower_ovules_per,
            flower_pollen_per=flower_pollen_per,
            ovule_fertilization_rate=ovule_fertilization_rate, 
            pollen_success_rate=pollen_success_rate, 
            pollen_comp=pollen_comp, 
            stigma_pollen_per = stigma_pollen_per,
            spo_maternal_effect=spo_maternal_effect,
            spo_random_death_chance=spo_random_death_chance,
            gam_random_death_chance=gam_random_death_chance,
            _chromosome=self.model.chromosome, 
            _sim_time = 2*self.model.sim_time, 
            _file_in=self.model.file_in,
            _file_out = self.model.file_out,
        ).run()

    def base(
        self,  
        ne = None,
        sexes = False,    
        _chromosome=None,
        _sim_time = None, 
        _file_in = None, 
        _file_out = None, 
        ):
        """
        Generate scripts appropriate for basic SLiM nonWF model, set up
        as a WF model

        Parameters:
        -----------
        sexes: bool
            default = False; individuals are hemraphroditic. If True, 
            individuals will be male and female
        ...
        """
        Base(
            model=self.model, ne = ne, sexes = sexes, 
            _chromosome=self.model.chromosome, 
            _sim_time = self.model.sim_time, 
            _file_in= self.model.file_in,
            _file_out = self.model.file_out,
        ).run()

    # def optimize(
    #         self, 
    #         desired_eggs_per_gen = None):
    #     """
    #     Convenience function to choose optimized params
    #     """
    #     Bryophyte(model).optimize(
    #         self,
    #         desired_eggs_per_gen = None,
    #     ).run()

