# project
(candidate name: SHaDY) 

### Description of project goal:
This program will be a wrapper around the forward-in-time evolutionary simulation program [SLiM3](https://messerlab.org/slim/). It will accept a phylogeny from the user and generate equivalent population demography inside a script that can be fed directly into SLiM3. THe user will also be able to define a number of different parameters for the simulation and the program will prepare the slim script appropriately along with a dispatch script, which is necessary to run SLiM3 from the command line. After the simulation is complete, the program will also provide a number of summary statistics and methods for inspecting the output of the simulation. 

The program is specifically designed to model the varied biphasic lifecycles in plants, allowing the user to explore the evolutionary consequences of different life histories. 


### Description of the code:
Possible dependencies:
* `numpy`: to manipulate data
* `pandas`: to organize and analyze data.
* `toytree`: to generate phylogenies.
* `msprime`: process and read .tree objects output by SLiM3
* `pyslim`: process and read .tree objects output by SLiM3


Classes:
- `Script`: the script file that will be generated by the package to run SLiM3
- `Demography`: creates subpopulation demoography for SLiM based on phylogeny input by user
- `Stats`: generates various summary statistics

Parameters (User-controlled):
- `lifehistory`:selection will act differently on haploid and diploid life stages depending on the kind of lineage the user wants to model
- `genome`: the size of the haploid set of genetic material upon which evolution is being simulated
- `genelement`: types of genomic elements, e.g. introns, exons, non-coding regions
- `muttype`: defines allowable mutation types in the simulation
- `chromosome`: allows user to make adjustments to linear arrangement of genomes into genes and other regions
- `tree`: phylogeny (newick or .tree object from toytree) that is used to generate subpopulation demography

Parameters (not editable by user):
- `dispatch`: the dispatch script generated by `Script` class; may include instructions for collecting summary statistics too
- `model`: SLiM3 can use Wright-Fisher (WF), extended WF, or non Wright-Fisher models
- `reproduction`: allows different mating models, e.g. clonal, slefing, hermaphroditic, sexual, and combinations thereof
- `fitness`: defines the fitness effects of different mutations
- `mutation`: changes to the genome


### Description of the data:
Users will be able to input a phylogeny and the program will generate the corresponding population demography for input into SLiM. 
Beyond that, the program will largely generate its own data and output summary statistics that can be used to evaluate observed data. The user will choose from a relatively simple set of options. The most user-customizeable part of the simulation will likely be the initial genomic data (e.g. the simulated chromosome)


### Description or demonstration of user interaction:
The user provides inputs a phylogeny in newick of .tree format and the `treecrawler` class will generate a subpopulation demogoraphy in the proper format for SLiM. `package` begins writing the slim script, using the .demo object to set up the subpopulation demography. 

User can then adjust other simulation parameters, such as life history, mutation rate, and recombination rate. `package` has built-in defaults for many values (which are adjusted dynamically by the script based on the parameters the user *does* define), so the user does not have to define every parameter for every run:
```python
# example of user-defined inputs and generated slim script file
...
```

Once the user is finished preparing the simulation script they can run a simulation in SLiM3:
```python
script.run #feeds script into SLiM3
```

User can calculate dN/dS, perform an MK-test, visualize mutations on a phylogeny, etc...
```python
# example of summary statistics from SLiM output
...
```
