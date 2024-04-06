# Procedural road graph generation

This is a very basic prototype implementation of a procedural road network generation, based on the paper ['Interactive Procedural Street Modeling'](https://www.sci.utah.edu/~chengu/street_sig08/street_project.htm) and the open source implementation of this approach by [ProbableTrain](https://github.com/ProbableTrain/MapGenerator/).

The implementation is written in Python in order to enable integration of the generation with Blenders Python API.

Integration with Blender is very basic at this point and the generation includes only the most important underlying features, with little regard for performance or optimization.
