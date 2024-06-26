#!/usr/bin/env python

"""
Pteridophyte specific SLIM script snippets used for string substitution.
"""

DEFS_PTER_VITTARIA = """
// model: homosporous pteridophyte
// p0 = haploid population
// p1 = diploid population
// 1 = gametophyte (1N) tag
// 2 = gametophyte clones (1N) tag
// 3 = sporophyte (2N) tag
// 4 = sporophyte clones (2N) tag;

// L0: Female = True, Male = False
"""

# ==PARAMETERS==
# GAM_CLONE_RATE
# GAM_CLONES_PER
# GAM_MATERNAL_EFFECT
# SEX
# SEX_RATE
# GAM_SELF_RATE_PER_EGG
# SPO_SELF_RATE_PER_EGG
# -------------------------
# TAGS
# L0, 2, 3
#-----------------------------------------------------------------------
REPRO_PTER_VITTARIA_P0 = """
	// clonal individual get added to the p0 pool for next round.
	// NOTE: this doesn't allow clones to reproduce this round.
	if (runif(1) < GAM_CLONE_RATE) {
		for (i in 1:GAM_CLONES_PER) {
			child = p0.addRecombinant(individual.genome1, NULL, NULL, individual.genome2, NULL, NULL, parent1 = individual); //only 1 parent recorded
			child.tag = 2; //marked as clone
			child.tagL0 = individual.tagL0; //inherits parent sex
			//gametophyte maternal effect not applicable for clones = neutral
			if (GAM_MATERNAL_EFFECT > 0)
				child.setValue("maternal_fitness", subpop.cachedFitness(individual.index));
		}
	}
	
	// iterate over each egg to find a mate (self, sib, or outcross)
	// NOTE: each gametophyte gives rise to antheridia that produce thousands of
	// clonal sperm. Because of this, sperm is not removed from the mating pool when used. 
	//Reproduction scripts run only on hermaphroditic gametophytes
	//Females: L0 = T
	if (SEX == T) {
		if (runif(1) < SEX_RATE) {
			if (individual.tagL0) {
				
				// get all males that could fertilize an egg of this hermaphrodite
				//In homosporous ferns, most gametophytes are hermaphroditic or male, 
				//so "males" includes all the hermaphrodites as well as male gametophytes
				males = p0.individuals;
				
				// if selfing is possible then get all sibling males
				if (SPO_SELF_RATE_PER_EGG > 0)
					//shared parent count for sibs is > 0 (1 or 2)
					siblings = males[individual.sharedParentCount(males)!=0];
				
				// iterate over each reproductive opportunity (archegonia) in this hermaphrodite.
				for (rep in 1:GAM_ARCHEGONIA_PER) {
					
					// weighted sampling: each egg gets gam-selfed, spo-selfed, or outcrossed.
					// Note: shadie enforces that GAM_SELF_RATE + SPO_SELF_RATE !> 1
					mode = sample(
						x=c(1, 2, 3),
						size=1,
						weights=c(GAM_SELF_RATE_PER_EGG, SPO_SELF_RATE_PER_EGG, 1 - (GAM_SELF_RATE_PER_EGG + SPO_SELF_RATE_PER_EGG))
						);
					
					// intra-gametophytic selfed
					if (mode == 1) {
						child = p1.addRecombinant(individual.genome1, NULL, NULL, individual.genome1, NULL, NULL, parent1 = individual);
						child.tag = 3; //sporophyte tag
						//gametophyte maternal effect on new sporophyte
						if (GAM_MATERNAL_EFFECT > 0)
							child.setValue("maternal_fitness", subpop.cachedFitness(individual.index));
					}
					
					// inter-gametophytic selfed individual (same sporo parent)
					// only occurs IF a sibling gametophyte is still alive.
					else if (mode == 2) {
						if (siblings.size() > 0) {
							sibling = sample(siblings, 1);
							child = p1.addRecombinant(individual.genome1, NULL, NULL, sibling.genome1, NULL, NULL, parent1 = individual);
							child.tag = 3; //sporophyte tag
							//gametophyte maternal effect on new sporophyte
							if (GAM_MATERNAL_EFFECT > 0)
								child.setValue("maternal_fitness", subpop.cachedFitness(individual.index));
						}
					}
					
					// outcrossing individual samples any other p0, and checks that it is outcrossing
					// only occurs if a non-sib gametophyte is still alive.
					else {
						// try at most 10 times to find a non-sib sperm, then skip.
						for (trial in 1:10) {
							sperm = sample(males, 1);
							if (individual.sharedParentCount(sperm)==0) {
								//recombination happens once here, then once again to produce the spores
								//resulting in chromosomes composed of any of the 4 parental genomes
								breaks1 = sim.chromosome.drawBreakpoints(individual);
        						breaks2 = sim.chromosome.drawBreakpoints(individual);
								child = p1.addRecombinant(individual.genome1, individual.genome2, breaks1, sperm.genome1, sperm.genome2, breaks2, parent1 = individual, parent2=sperm);
								child.tag = 3; //sporophyte tag
								//gametophyte maternal effect on new sporophyte
								if (GAM_MATERNAL_EFFECT > 0)
									child.setValue("maternal_fitness", subpop.cachedFitness(individual.index));
								break;
							}
						}
					}
				}
			}
		}
	}

"""

# ==PARAMETERS==
# SPO_CLONE_RATE
# SPO_CLONES_PER
# SPO_SPORES_PER
# SPO_MATERNAL_EFFECT
# GAM_FEMALE_TO_MALE_RATIO
# -------------------------
# TAGS
# L0, 1, 4
#-----------------------------------------------------------------------
REPRO_PTER_VITTARIA_P1 = """
	ind = individual;
    
    // clonal individual get added to the p0 pool for next round.
    // NOTE: this doesn't allow clones to reproduce this round.
    
    if (runif(1) < SPO_CLONE_RATE) {
        for (i in 1:SPO_CLONES_PER) {
            child = p1.addRecombinant(individual.genome1, NULL, NULL, individual.genome2, NULL, NULL, parent1 = individual, parent2 = individual);
            child.tag = 4; // sporophyte clone
            //sporophyte maternal effect not applicable for clones = neutral
            if (SPO_MATERNAL_EFFECT > 0)
                child.setValue("maternal_fitness", subpop.cachedFitness(individual.index)); 
            }
    }
    
    // fitness-based determination of how many spores are created by this ind
    ind_fitness = p1.cachedFitness(ind.index);
    max_fitness = max(p1.cachedFitness(NULL));
    ind_fitness_scaled = ind_fitness/max_fitness; 
    
    spore_vector = sample(c(0,1), SPO_SPORES_PER, replace = T, weights = c((1-ind_fitness_scaled), ind_fitness_scaled));
    spores = sum(spore_vector);

    // each spore produces its own recombinant breakpoints 
    for (rep in 1:spores) {
        breaks1 = sim.chromosome.drawBreakpoints(ind);
        breaks2 = sim.chromosome.drawBreakpoints(ind);
        breaks3 = sim.chromosome.drawBreakpoints(ind);
        breaks4 = sim.chromosome.drawBreakpoints(ind);
        
        // create four meiotic products. If later two of these mate with each other
        // it is an example of sporophytic selfing. Because we need to be able to match
        // sibling gametes at that time we tag them now with their sporophyte parent's index. 
        child1 = p0.addRecombinant(ind.genome1, ind.genome2, breaks1, ind.genome1, ind.genome2, breaks2, parent1 = ind);
        child2 = p0.addRecombinant(ind.genome2, ind.genome1, breaks1, ind.genome2, ind.genome1, breaks2, parent1 = ind);
        child3 = p0.addRecombinant(ind.genome1, ind.genome2, breaks3, ind.genome1, ind.genome2, breaks4, parent1 = ind);
        child4 = p0.addRecombinant(ind.genome2, ind.genome1, breaks3, ind.genome2, ind.genome1, breaks4, parent1 = ind);
        children = c(child1, child2, child3, child4);
        children.tag = 1; //gametophyte tag
        children.tagL0 = ifelse(runif(1) < GAM_FEMALE_TO_MALE_RATIO, T, F);
        
        //sporophyte maternal effect on new spores
        if (SPO_MATERNAL_EFFECT > 0)
            children.setValue("maternal_fitness", subpop.cachedFitness(individual.index));
    }

"""